---
search:
  exclude: true
---
# ストリーミング

ストリーミングを利用すると、エージェントの実行をリアルタイムで購読できます。これは、エンドユーザーに進行状況や部分的なレスポンスを表示する際に役立ちます。

ストリーミングを行うには `Runner.run_streamed()` を呼び出します。これにより `RunResultStreaming` が返されます。`result.stream_events()` を呼び出すと、以下で説明する `StreamEvent` オブジェクトの非同期ストリームを取得できます。

## Raw response events

`RawResponsesStreamEvent` は LLM から直接渡される raw イベントです。OpenAI Responses API 形式であり、各イベントには `response.created`、`response.output_text.delta` などの type と data が含まれます。これらのイベントは、生成されたメッセージを即座にユーザーへストリーム配信したい場合に便利です。

たとえば、次のコードは LLM が生成したテキストをトークンごとに出力します。

```python
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Joker",
        instructions="You are a helpful assistant.",
    )

    result = Runner.run_streamed(agent, input="Please tell me 5 jokes.")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

## Run item イベントと エージェント イベント

`RunItemStreamEvent` はより高レベルのイベントで、アイテムが完全に生成された時点を通知します。これにより、各トークンではなく「メッセージが生成された」「ツールが実行された」などのレベルで進行状況をプッシュできます。同様に `AgentUpdatedStreamEvent` は、ハンドオフの結果として現在のエージェントが変更された際に更新を通知します。

たとえば、次のコードは raw イベントを無視し、ユーザーへ更新のみをストリーム配信します。

```python
import asyncio
import random
from agents import Agent, ItemHelpers, Runner, function_tool

@function_tool
def how_many_jokes() -> int:
    return random.randint(1, 10)


async def main():
    agent = Agent(
        name="Joker",
        instructions="First call the `how_many_jokes` tool, then tell that many jokes.",
        tools=[how_many_jokes],
    )

    result = Runner.run_streamed(
        agent,
        input="Hello",
    )
    print("=== Run starting ===")

    async for event in result.stream_events():
        # We'll ignore the raw responses event deltas
        if event.type == "raw_response_event":
            continue
        # When the agent updates, print that
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            continue
        # When items are generated, print them
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output: {event.item.output}")
            elif event.item.type == "message_output_item":
                print(f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
            else:
                pass  # Ignore other event types

    print("=== Run complete ===")


if __name__ == "__main__":
    asyncio.run(main())
```