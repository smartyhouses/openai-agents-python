---
search:
  exclude: true
---
# エージェント

エージェントはアプリケーションの中核となる構成要素です。エージェントとは、`instructions` と `tools` で設定された大規模言語モデル ( LLM ) です。

## 基本設定

エージェントでよく設定する主なプロパティは次のとおりです:

-   `name`: エージェントを識別する必須の文字列。
-   `instructions`: developer メッセージまたは system prompt とも呼ばれます。
-   `model`: 使用する LLM と、temperature や top_p などのモデル調整パラメーターを設定する省略可能な `model_settings`。
-   `tools`: エージェントがタスク達成のために使用できるツール。

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="o3-mini",
    tools=[get_weather],
)
```

## コンテキスト

エージェントはその `context` 型に対してジェネリックです。コンテキストは依存性注入の仕組みで、あなたが作成して `Runner.run()` に渡すオブジェクトです。これはすべてのエージェント、ツール、ハンドオフなどに渡され、実行時の依存関係や状態をまとめて保持します。任意の Python オブジェクトをコンテキストとして指定できます。

```python
@dataclass
class UserContext:
    uid: str
    is_pro_user: bool

    async def fetch_purchases() -> list[Purchase]:
        return ...

agent = Agent[UserContext](
    ...,
)
```

## 出力タイプ

デフォルトでは、エージェントはプレーンテキスト (つまり `str`) を出力します。特定の型で出力させたい場合は `output_type` パラメーターを使用します。一般的によく使われるのは Pydantic オブジェクトですが、Pydantic の TypeAdapter でラップできる型であれば、dataclasses、lists、TypedDict など何でもサポートしています。

```python
from pydantic import BaseModel
from agents import Agent


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

!!! note

    `output_type` を渡すと、モデルは通常のプレーンテキストではなく [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) を使用するよう指示されます。

## ハンドオフ

ハンドオフは、エージェントが委任できるサブエージェントです。ハンドオフのリストを渡すと、エージェントは関連性がある場合にそれらへ委任できます。これにより、単一タスクに特化したモジュール型エージェントを編成できる強力なパターンが実現します。詳しくは [ハンドオフ](handoffs.md) ドキュメントをご覧ください。

```python
from agents import Agent

booking_agent = Agent(...)
refund_agent = Agent(...)

triage_agent = Agent(
    name="Triage agent",
    instructions=(
        "Help the user with their questions."
        "If they ask about booking, handoff to the booking agent."
        "If they ask about refunds, handoff to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

## 動的 instructions

ほとんどの場合、エージェント作成時に `instructions` を指定できますが、関数を介して動的に提供することも可能です。関数はエージェントとコンテキストを受け取り、プロンプトを返す必要があります。同期関数と async 関数のどちらも利用できます。

```python
def dynamic_instructions(
    context: RunContextWrapper[UserContext], agent: Agent[UserContext]
) -> str:
    return f"The user's name is {context.context.name}. Help them with their questions."


agent = Agent[UserContext](
    name="Triage agent",
    instructions=dynamic_instructions,
)
```

## ライフサイクルイベント (hooks)

エージェントのライフサイクルを観察したい場合があります。たとえば、イベントをログに残したり、特定のイベント発生時にデータを事前取得したりするケースです。`hooks` プロパティを使用してエージェントのライフサイクルにフックできます。[`AgentHooks`][agents.lifecycle.AgentHooks] クラスをサブクラス化し、必要なメソッドをオーバーライドしてください。

## ガードレール

ガードレールを使用すると、エージェントの実行と並行してユーザー入力に対するチェックやバリデーションを実行できます。たとえば、ユーザー入力の関連性を検査するなどが可能です。詳しくは [guardrails](guardrails.md) ドキュメントを参照してください。

## エージェントのクローン／コピー

`clone()` メソッドを使うと、エージェントを複製し、任意のプロパティを変更できます。

```python
pirate_agent = Agent(
    name="Pirate",
    instructions="Write like a pirate",
    model="o3-mini",
)

robot_agent = pirate_agent.clone(
    name="Robot",
    instructions="Write like a robot",
)
```

## Tool の使用を強制する

ツールのリストを渡しても、LLM が必ずツールを使用するとは限りません。[`ModelSettings.tool_choice`][agents.model_settings.ModelSettings.tool_choice] を設定することでツール使用を強制できます。有効な値は次のとおりです:

1. `auto` : LLM がツールを使うかどうかを判断します。  
2. `required` : LLM にツール使用を必須とします (どのツールを使うかは自動で判断)。  
3. `none` : LLM にツールを使用しないように要求します。  
4. 具体的な文字列 (例: `my_tool`) を設定すると、その特定のツールを必ず使用させます。

!!! note

    無限ループを防ぐため、フレームワークはツール呼び出し後に `tool_choice` を自動的に "auto" にリセットします。この挙動は [`agent.reset_tool_choice`][agents.agent.Agent.reset_tool_choice] で設定可能です。ツールの結果が LLM に送られ、`tool_choice` の設定により再度ツール呼び出しが生成されることで無限ループが発生します。

    ツール呼び出し後にエージェントを完全に停止させたい場合 (自動モードに戻さずに終了したい場合) は、[`Agent.tool_use_behavior="stop_on_first_tool"`] を設定すると、ツールの出力をそのまま最終応答として使用し、追加の LLM 処理を行いません。