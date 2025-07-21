---
search:
  exclude: true
---
# エージェントの実行

`Runner` クラスを使ってエージェントを実行できます。方法は 3 つあります:

1. [`Runner.run()`][agents.run.Runner.run] — 非同期で実行され、[`RunResult`][agents.result.RunResult] を返します。  
2. [`Runner.run_sync()`][agents.run.Runner.run_sync] — 同期メソッドで、内部的には `.run()` を呼び出します。  
3. [`Runner.run_streamed()`][agents.run.Runner.run_streamed] — 非同期で実行され、[`RunResultStreaming`][agents.result.RunResultStreaming] を返します。LLM をストリーミングモードで呼び出し、受信したイベントをリアルタイムでストリーミングします。  

```python
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance
```

詳細は [結果ガイド](results.md) を参照してください。

## エージェントループ

`Runner` の run メソッドでは、開始エージェントと入力を渡します。入力は文字列（ユーザーのメッセージと見なされます）または入力アイテムのリスト（OpenAI Responses API のアイテム）です。

`Runner` は以下のループを実行します:

1. 現在のエージェントと入力で LLM を呼び出します。  
2. LLM が出力を生成します。  
    1. LLM が `final_output` を返した場合、ループを終了して結果を返します。  
    2. LLM がハンドオフを行った場合、現在のエージェントと入力を更新し、ループを再実行します。  
    3. LLM がツール呼び出しを生成した場合、それらを実行し、結果を追加してループを再実行します。  
3. 渡された `max_turns` を超えた場合、[`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded] 例外を発生させます。  

!!! note

    LLM の出力が「最終出力」と見なされる条件は、求められた型のテキスト出力であり、ツール呼び出しが含まれていない場合です。

## ストリーミング

ストリーミングを使用すると、LLM 実行中のストリーミングイベントを受け取れます。ストリーム終了後、[`RunResultStreaming`][agents.result.RunResultStreaming] に実行全体の情報（生成された新しい出力を含む）が格納されます。ストリーミングイベントは `.stream_events()` で受け取ります。詳細は [ストリーミングガイド](streaming.md) を参照してください。

## Run config

`run_config` パラメーターでは、エージェント実行のグローバル設定を行えます:

- [`model`][agents.run.RunConfig.model]: 各エージェントの `model` 設定に関係なく、使用する LLM モデルをグローバルに指定します。  
- [`model_provider`][agents.run.RunConfig.model_provider]: モデル名を解決するモデルプロバイダー。デフォルトは OpenAI です。  
- [`model_settings`][agents.run.RunConfig.model_settings]: エージェント固有の設定を上書きします。たとえば、グローバルな `temperature` や `top_p` を設定できます。  
- [`input_guardrails`][agents.run.RunConfig.input_guardrails], [`output_guardrails`][agents.run.RunConfig.output_guardrails]: すべての実行に適用する入力／出力ガードレールのリスト。  
- [`handoff_input_filter`][agents.run.RunConfig.handoff_input_filter]: ハンドオフに入力フィルターが設定されていない場合に適用するグローバル入力フィルター。新しいエージェントに送信される入力を編集できます。詳細は [`Handoff.input_filter`][agents.handoffs.Handoff.input_filter] を参照してください。  
- [`tracing_disabled`][agents.run.RunConfig.tracing_disabled]: 実行全体の [トレーシング](tracing.md) を無効にします。  
- [`trace_include_sensitive_data`][agents.run.RunConfig.trace_include_sensitive_data]: LLM やツール呼び出しの入出力など、機微なデータをトレースに含めるかどうかを設定します。  
- [`workflow_name`][agents.run.RunConfig.workflow_name], [`trace_id`][agents.run.RunConfig.trace_id], [`group_id`][agents.run.RunConfig.group_id]: トレーシングに使用するワークフロー名、トレース ID、トレース グループ ID を設定します。少なくとも `workflow_name` の設定を推奨します。グループ ID は複数実行間でトレースを関連付ける任意フィールドです。  
- [`trace_metadata`][agents.run.RunConfig.trace_metadata]: すべてのトレースに含めるメタデータ。  

## 会話 / チャットスレッド

いずれの run メソッドを呼び出しても、1 回の呼び出しで 1 つ以上のエージェント（つまり 1 回以上の LLM 呼び出し）が実行されますが、チャット会話上は 1 つの論理的ターンとなります。例:

1. ユーザーのターン: ユーザーがテキストを入力  
2. Runner の実行: 1 つ目のエージェントが LLM を呼び出し、ツールを実行し、2 つ目のエージェントへハンドオフ。2 つ目のエージェントがさらにツールを実行し、最終出力を生成。  

エージェント実行後、ユーザーに何を表示するかは自由です。エージェントが生成したすべてのアイテムを表示しても、最終出力だけを表示しても構いません。いずれの場合も、ユーザーがフォローアップ質問をすると、再度 run メソッドを呼び出せます。

### 手動の会話管理

[`RunResultBase.to_input_list()`][agents.result.RunResultBase.to_input_list] メソッドを使用して次のターンの入力を取得し、手動で会話履歴を管理できます:

```python
async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    thread_id = "thread_123"  # Example thread ID
    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(result.final_output)
        # San Francisco

        # Second turn
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
        result = await Runner.run(agent, new_input)
        print(result.final_output)
        # California
```

### Sessions を使った自動会話管理

よりシンプルな方法として、[Sessions](sessions.md) を使用すれば `.to_input_list()` を手動で呼び出すことなく会話履歴を自動管理できます:

```python
from agents import Agent, Runner, SQLiteSession

async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    # Create session instance
    session = SQLiteSession("conversation_123")

    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
        print(result.final_output)
        # San Francisco

        # Second turn - agent automatically remembers previous context
        result = await Runner.run(agent, "What state is it in?", session=session)
        print(result.final_output)
        # California
```

Sessions は自動で以下を行います:

- 各実行前に会話履歴を取得  
- 各実行後に新しいメッセージを保存  
- 異なるセッション ID ごとに会話を分離して管理  

詳細は [Sessions のドキュメント](sessions.md) を参照してください。

## 例外

SDK は状況に応じて例外を発生させます。完全な一覧は [`agents.exceptions`][] を参照してください。概要は以下のとおりです:

- [`AgentsException`][agents.exceptions.AgentsException]: SDK で発生するすべての例外の基底クラスです。  
- [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded]: 実行が run メソッドに渡した `max_turns` を超えた場合に発生します。  
- [`ModelBehaviorError`][agents.exceptions.ModelBehaviorError]: モデルが無効な出力（JSON の構文エラーや存在しないツールの使用など）を生成した場合に発生します。  
- [`UserError`][agents.exceptions.UserError]: SDK を使用するコード側のミスで発生します。  
- [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered], [`OutputGuardrailTripwireTriggered`][agents.exceptions.OutputGuardrailTripwireTriggered]: [ガードレール](guardrails.md) が作動した場合に発生します。