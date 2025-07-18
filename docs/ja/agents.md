---
search:
  exclude: true
---
# エージェント

エージェントはアプリの中核となる構成要素です。エージェントとは、 instructions と tools で構成された大規模言語モデル ( LLM ) です。

## 基本設定

エージェントで最もよく設定するプロパティは以下のとおりです。

- `name`: エージェントを識別する必須の文字列です。  
- `instructions`: developer メッセージまたは システムプロンプト とも呼ばれます。  
- `model`: 使用する LLM を指定し、`model_settings` で temperature、top_p などのチューニングパラメーターを任意で設定できます。  
- `tools`: エージェントがタスクを達成するために使用できる tools です。  

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

エージェントは `context` 型についてジェネリックになっています。コンテキストは依存性注入のためのツールで、あなたが生成して `Runner.run()` に渡すオブジェクトです。このオブジェクトは各エージェント、 tool、ハンドオフなどに渡され、実行時の依存関係や状態を保持する入れ物として機能します。任意の Python オブジェクトをコンテキストとして提供できます。

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

デフォルトでは、エージェントはプレーンテキスト (つまり `str`) を出力します。特定の型で出力させたい場合は `output_type` パラメーターを使用してください。一般的には [Pydantic](https://docs.pydantic.dev/) オブジェクトを使いますが、Pydantic の [TypeAdapter](https://docs.pydantic.dev/latest/api/type_adapter/) でラップできる型 ― dataclass、リスト、TypedDict など ― であればすべてサポートしています。

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

    `output_type` を渡すと、モデルは通常のプレーンテキスト応答ではなく [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) を使用するよう指示されます。

## ハンドオフ

ハンドオフは、エージェントが委任できるサブエージェントです。ハンドオフのリストを提供しておくと、エージェントは必要に応じてそれらに処理を委任できます。これは、単一タスクに特化したモジュール化されたエージェントをオーケストレーションする強力なパターンです。詳細は [handoffs](handoffs.md) ドキュメントを参照してください。

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

多くの場合、エージェント作成時に instructions を指定できますが、関数を通じて動的に instructions を提供することも可能です。この関数はエージェントとコンテキストを受け取り、プロンプトを返す必要があります。同期関数でも `async` 関数でも構いません。

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

エージェントのライフサイクルを監視したいケースがあります。たとえば、イベントをログに記録したり、特定のイベント発生時にデータを事前取得したりする場合です。`hooks` プロパティを使ってエージェントのライフサイクルにフックできます。[`AgentHooks`][agents.lifecycle.AgentHooks] クラスを継承し、関心のあるメソッドをオーバーライドしてください。

## ガードレール

ガードレールを使用すると、エージェントの実行と並行してユーザー入力に対するチェックやバリデーションを行えます。たとえば、ユーザー入力の関連性をスクリーニングすることが可能です。詳細は [guardrails](guardrails.md) ドキュメントを参照してください。

## エージェントの複製 / コピー

エージェントの `clone()` メソッドを使用すると、エージェントを複製し、任意のプロパティを変更できます。

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

## Tool 使用の強制

tool のリストを指定しても、 LLM が必ずしも tool を使用するとは限りません。[`ModelSettings.tool_choice`][agents.model_settings.ModelSettings.tool_choice] を設定することで、 tool 使用を強制できます。有効な値は次のとおりです。

1. `auto` : LLM が tool を使うかどうかを判断します。  
2. `required` : LLM に tool の使用を必須とします (ただしどの tool を使うかは自動で判断します)。  
3. `none` : LLM に tool を使用しないことを必須とします。  
4. 文字列 (`my_tool` など) を指定すると、その特定の tool を使用することを必須とします。  

!!! note

    無限ループを防ぐため、フレームワークは tool 呼び出し後に `tool_choice` を自動的に "auto" にリセットします。この挙動は [`agent.reset_tool_choice`][agents.agent.Agent.reset_tool_choice] で設定できます。無限ループは、tool の結果が LLM に送信され、`tool_choice` の設定により LLM が再度 tool 呼び出しを生成し続けることで発生します。

    tool 呼び出し後に自動モードへ戻さず、完全に停止させたい場合は [`Agent.tool_use_behavior="stop_on_first_tool"`] を設定してください。この設定では、最初の tool 出力をそのまま最終応答として使用し、追加の LLM 処理を行いません。