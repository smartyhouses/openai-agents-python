---
search:
  exclude: true
---
# トレーシング

Agents SDK にはトレーシング機能が組み込まれており、 エージェントの実行中に発生する LLM 生成、ツール呼び出し、ハンドオフ、ガードレール、さらにカスタムイベントまでを包括的に記録します。 [Traces ダッシュボード](https://platform.openai.com/traces) を使うことで、開発時や本番環境でワークフローをデバッグ・可視化・監視できます。

!!!note

    トレーシングはデフォルトで有効です。無効にする方法は 2 つあります:

    1. 環境変数 `OPENAI_AGENTS_DISABLE_TRACING=1` を設定すると、グローバルにトレーシングを無効化できます  
    2. 単一の実行のみ無効化したい場合は、[`agents.run.RunConfig.tracing_disabled`][] に `True` を設定してください

***OpenAI の API を Zero Data Retention (ZDR) ポリシーで利用している組織では、トレーシングは利用できません。***

## トレースとスパン

- **トレース** は 1 つのワークフローのエンドツーエンド操作を表します。複数のスパンで構成され、以下のプロパティを持ちます:  
    - `workflow_name`: 論理的なワークフローやアプリ名。例: 「Code generation」や「Customer service」  
    - `trace_id`: トレースの一意 ID。渡さなければ自動生成されます。形式は `trace_<32_alphanumeric>`  
    - `group_id`: オプションのグループ ID。1 つの会話から生成される複数のトレースを関連付けるために使用します。例: チャットスレッド ID  
    - `disabled`: `True` の場合、このトレースは記録されません  
    - `metadata`: トレースに付与する任意のメタデータ  
- **スパン** は開始時刻と終了時刻を持つ操作を表します。スパンは以下を持ちます:  
    - `started_at` と `ended_at` のタイムスタンプ  
    - 所属するトレースを示す `trace_id`  
    - 親スパンを指す `parent_id` (存在する場合)  
    - スパンに関する情報を示す `span_data`。例: `AgentSpanData` はエージェントに関する情報、`GenerationSpanData` は LLM 生成に関する情報など  

## デフォルトのトレーシング

デフォルトでは、SDK は次をトレースします:

- `Runner.{run, run_sync, run_streamed}()` 全体を `trace()` でラップ  
- エージェントが実行されるたびに `agent_span()` でラップ  
- LLM 生成は `generation_span()` でラップ  
- 関数ツール呼び出しはそれぞれ `function_span()` でラップ  
- ガードレールは `guardrail_span()` でラップ  
- ハンドオフは `handoff_span()` でラップ  
- 音声入力 (音声→テキスト) は `transcription_span()` でラップ  
- 音声出力 (テキスト→音声) は `speech_span()` でラップ  
- 関連する音声スパンは `speech_group_span()` の下に配置される場合があります  

デフォルトではトレース名は「Agent trace」です。`trace` を使用する場合はこの名前を設定できますし、[`RunConfig`][agents.run.RunConfig] で名前やその他プロパティを構成することもできます。

さらに、[カスタムトレースプロセッサ](#custom-tracing-processors) を設定して、トレースを別の宛先に送信する (置き換えまたはセカンダリ宛先) ことも可能です。

## より高レベルのトレース

複数回の `run()` 呼び出しを 1 つのトレースにまとめたい場合があります。その場合、コード全体を `trace()` でラップしてください。

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.")

    with trace("Joke workflow"): # (1)!
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
        print(f"Joke: {first_result.final_output}")
        print(f"Rating: {second_result.final_output}")
```

1. `Runner.run` への 2 回の呼び出しが `with trace()` に包まれているため、各実行は個別のトレースを作成せず、全体トレースの一部になります。

## トレースの作成

[`trace()`][agents.tracing.trace] 関数を使ってトレースを作成できます。トレースは開始と終了が必要で、方法は 2 つあります:

1. **推奨**: コンテキストマネージャとして使用する (例: `with trace(...) as my_trace`)。開始と終了が自動で行われます  
2. [`trace.start()`][agents.tracing.Trace.start] と [`trace.finish()`][agents.tracing.Trace.finish] を手動で呼び出す  

現在のトレースは Python の [`contextvar`](https://docs.python.org/3/library/contextvars.html) で管理されるため、並行処理でも自動的に機能します。トレースを手動で開始・終了する場合は、`start()`/`finish()` に `mark_as_current` と `reset_current` を渡して現在のトレースを更新してください。

## スパンの作成

各種 [`*_span()`][agents.tracing.create] メソッドでスパンを作成できます。通常は手動でスパンを作成する必要はありません。カスタム情報を追跡したい場合は [`custom_span()`][agents.tracing.custom_span] を利用できます。

スパンは自動的に現在のトレースの一部となり、最も近い現在のスパンの下にネストされます。これも Python の [`contextvar`](https://docs.python.org/3/library/contextvars.html) で追跡されます。

## 機微データ

特定のスパンは機微なデータを記録する可能性があります。

`generation_span()` は LLM 生成の入力/出力を保存し、`function_span()` は関数呼び出しの入力/出力を保存します。これらに機微データが含まれる場合があるため、[`RunConfig.trace_include_sensitive_data`][agents.run.RunConfig.trace_include_sensitive_data] でデータ取得を無効化できます。

同様に、オーディオスパンはデフォルトで入力・出力音声を base64 形式の PCM データとして含みます。このオーディオデータの取得は [`VoicePipelineConfig.trace_include_sensitive_audio_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_audio_data] で無効化できます。

## カスタムトレーシングプロセッサ

トレーシングの高レベル構成は次の通りです:

- 初期化時にグローバルな [`TraceProvider`][agents.tracing.setup.TraceProvider] を作成し、トレースを生成  
- `TraceProvider` に [`BatchTraceProcessor`][agents.tracing.processors.BatchTraceProcessor] を設定してトレース/スパンをバッチ送信し、[`BackendSpanExporter`][agents.tracing.processors.BackendSpanExporter] が OpenAI バックエンドへバッチエクスポート  

このデフォルト設定をカスタマイズして別のバックエンドへ送信したりエクスポーター動作を変更したりするには、次の 2 つの方法があります:

1. [`add_trace_processor()`][agents.tracing.add_trace_processor]  
   追加のトレースプロセッサを登録し、トレース/スパンを受信して独自処理を実行できます。OpenAI バックエンドへの送信はそのまま行われます。  
2. [`set_trace_processors()`][agents.tracing.set_trace_processors]  
   デフォルトのプロセッサを置き換えます。OpenAI バックエンドへ送信したい場合は、その処理を含む `TracingProcessor` を自分で追加する必要があります。  

## 外部トレーシングプロセッサ一覧

- [Weights & Biases](https://weave-docs.wandb.ai/guides/integrations/openai_agents)
- [Arize-Phoenix](https://docs.arize.com/phoenix/tracing/integrations-tracing/openai-agents-sdk)
- [Future AGI](https://docs.futureagi.com/future-agi/products/observability/auto-instrumentation/openai_agents)
- [MLflow (self-hosted/OSS](https://mlflow.org/docs/latest/tracing/integrations/openai-agent)
- [MLflow (Databricks hosted](https://docs.databricks.com/aws/en/mlflow/mlflow-tracing#-automatic-tracing)
- [Braintrust](https://braintrust.dev/docs/guides/traces/integrations#openai-agents-sdk)
- [Pydantic Logfire](https://logfire.pydantic.dev/docs/integrations/llms/openai/#openai-agents)
- [AgentOps](https://docs.agentops.ai/v1/integrations/agentssdk)
- [Scorecard](https://docs.scorecard.io/docs/documentation/features/tracing#openai-agents-sdk-integration)
- [Keywords AI](https://docs.keywordsai.co/integration/development-frameworks/openai-agent)
- [LangSmith](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_openai_agents_sdk)
- [Maxim AI](https://www.getmaxim.ai/docs/observe/integrations/openai-agents-sdk)
- [Comet Opik](https://www.comet.com/docs/opik/tracing/integrations/openai_agents)
- [Langfuse](https://langfuse.com/docs/integrations/openaiagentssdk/openai-agents)
- [Langtrace](https://docs.langtrace.ai/supported-integrations/llm-frameworks/openai-agents-sdk)
- [Okahu-Monocle](https://github.com/monocle2ai/monocle)
- [Galileo](https://v2docs.galileo.ai/integrations/openai-agent-integration#openai-agent-integration)
- [Portkey AI](https://portkey.ai/docs/integrations/agents/openai-agents)