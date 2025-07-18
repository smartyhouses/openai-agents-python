---
search:
  exclude: true
---
# エージェントの実行

エージェントは [`Runner`][agents.run.Runner] クラスで実行できます。選択肢は 3 つあります。

1. `Runner.run()` は非同期で実行され、[`RunResult`][agents.result.RunResult] を返します。  
2. `Runner.run_sync()` は同期メソッドで、内部的には `.run()` を呼び出します。  
3. `Runner.run_streamed()` は非同期で実行され、[`RunResultStreaming`][agents.result.RunResultStreaming] を返します。 LLM をストリーミングモードで呼び出し、そのイベントを受信次第ストリームします。

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

詳細は [結果ガイド](results.md) をご覧ください。

## エージェントループ

`Runner` の run メソッドを使用するときは、開始エージェントと入力を渡します。入力は文字列（ユーザー メッセージと見なされます）または入力項目のリスト（OpenAI Responses API の項目）です。

ランナーは次のループを実行します。

1. 現在のエージェントと入力で LLM を呼び出します。  
2. LLM が出力を生成します。  
　　1. LLM が `final_output` を返した場合、ループを終了して結果を返します。  
　　2. LLM がハンドオフを行った場合、現在のエージェントと入力を更新し、ループを再実行します。  
　　3. LLM がツール呼び出しを生成した場合、それらを実行し、結果を追加してループを再実行します。  
3. 渡された `max_turns` を超えた場合、[`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded] 例外を送出します。

!!! note

    LLM の出力が「最終出力」と見なされる条件は、目的の型でテキスト出力を生成し、ツール呼び出しがないことです。

## ストリーミング

ストリーミングを使用すると、LLM の実行中にストリーミングイベントを受け取れます。ストリーム完了後、[`RunResultStreaming`][agents.result.RunResultStreaming] には実行に関する完全な情報（新しい出力すべてを含む）が格納されます。`.stream_events()` を呼び出してストリーミングイベントを取得できます。詳細は [ストリーミングガイド](streaming.md) を参照してください。

## 実行設定

`run_config` パラメーターでは、エージェント実行のグローバル設定を行えます。

- [`model`][agents.run.RunConfig.model]: 各エージェントの `model` 設定に関係なく、グローバルで使用する LLM モデルを指定します。  
- [`model_provider`][agents.run.RunConfig.model_provider]: モデル名を解決するモデルプロバイダー。デフォルトは OpenAI。  
- [`model_settings`][agents.run.RunConfig.model_settings]: エージェント固有の設定を上書きします。例として、グローバルな `temperature` や `top_p` を設定可能です。  
- [`input_guardrails`][agents.run.RunConfig.input_guardrails], [`output_guardrails`][agents.run.RunConfig.output_guardrails]: すべての実行に適用する入力／出力ガードレールのリスト。  
- [`handoff_input_filter`][agents.run.RunConfig.handoff_input_filter]: ハンドオフに既定のフィルターがない場合に適用するグローバル入力フィルター。新しいエージェントに送る入力を編集できます。詳細は [`Handoff.input_filter`][agents.handoffs.Handoff.input_filter] を参照してください。  
- [`tracing_disabled`][agents.run.RunConfig.tracing_disabled]: 実行全体の [トレーシング](tracing.md) を無効化します。  
- [`trace_include_sensitive_data`][agents.run.RunConfig.trace_include_sensitive_data]: トレースに LLM やツール呼び出しの入出力など、潜在的に機密性の高いデータを含めるかを設定します。  
- [`workflow_name`][agents.run.RunConfig.workflow_name], [`trace_id`][agents.run.RunConfig.trace_id], [`group_id`][agents.run.RunConfig.group_id]: トレーシング用のワークフロー名、トレース ID、トレース グループ ID を設定します。少なくとも `workflow_name` を設定することを推奨します。グループ ID は複数実行間でトレースを関連付けるための任意項目です。  
- [`trace_metadata`][agents.run.RunConfig.trace_metadata]: すべてのトレースに含めるメタデータ。  

## 会話 / チャットスレッド

いずれの run メソッドを呼び出しても、1 回以上のエージェント実行（ひいては 1 回以上の LLM 呼び出し）が発生しますが、チャット会話上は 1 つの論理ターンを表します。例:

1. ユーザーターン: ユーザーがテキストを入力  
2. Runner 実行: 第 1 エージェントが LLM を呼び出し、ツールを実行、別のエージェントへハンドオフ。第 2 エージェントがさらにツールを実行し、最終出力を生成。  

エージェント実行が終了したら、ユーザーに何を表示するか選択できます。たとえば、エージェントが生成したすべての新しい項目を表示するか、最終出力だけを表示するかを決められます。その後、ユーザーが追加入力を行った場合に再度 run メソッドを呼び出します。

### 手動での会話管理

[`RunResultBase.to_input_list()`][agents.result.RunResultBase.to_input_list] メソッドを使って次ターン用の入力を取得し、会話履歴を手動で管理できます。

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

### Sessions を用いた自動会話管理

より簡単な方法として、[Sessions](sessions.md) を使えば `.to_input_list()` を明示的に呼ばずに会話履歴を自動管理できます。

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

Sessions は自動で以下を行います。

- 各実行前に会話履歴を取得  
- 各実行後に新しいメッセージを保存  
- セッション ID ごとに別々の会話を維持  

詳細は [Sessions ドキュメント](sessions.md) を参照してください。

## 例外

特定のケースで SDK は例外を送出します。完全な一覧は [`agents.exceptions`][] にあります。概要は以下のとおりです。

- [`AgentsException`][agents.exceptions.AgentsException]: SDK が送出するすべての例外の基底クラス。  
- [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded]: 実行が `max_turns` を超えた場合に送出されます。  
- [`ModelBehaviorError`][agents.exceptions.ModelBehaviorError]: モデルが不正な出力 (例: JSON の構造が誤っている、存在しないツールを呼び出す) を生成した際に送出されます。  
- [`UserError`][agents.exceptions.UserError]: SDK を使用するコードの記述ミスなど、ユーザー側のエラーで送出されます。  
- [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered], [`OutputGuardrailTripwireTriggered`][agents.exceptions.OutputGuardrailTripwireTriggered]: [ガードレール](guardrails.md) がトリップした際に送出されます。