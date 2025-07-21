---
search:
  exclude: true
---
# トレーシング

Agents SDK には組み込みのトレーシング機能があり、エージェント実行中に発生する LLM 生成、ツール呼び出し、ハンドオフ、ガードレール、カスタムイベントなどを包括的に記録します。[Traces ダッシュボード](https://platform.openai.com/traces) を利用すると、開発中および本番環境でワークフローをデバッグ、可視化、監視できます。

!!!note

    トレーシングはデフォルトで有効です。無効化する方法は 2 つあります。

    1. 環境変数 `OPENAI_AGENTS_DISABLE_TRACING=1` を設定してグローバルに無効化する  
    2. 単一の実行に対して [`agents.run.RunConfig.tracing_disabled`][] を `True` に設定する

***OpenAI の API を Zero Data Retention (ZDR) ポリシーで運用している組織では、トレーシングは利用できません。***

## トレースとスパン

- **トレース**: 1 つのワークフローのエンドツーエンド操作を表します。複数のスパンで構成され、以下のプロパティを持ちます。  
    - `workflow_name`: 論理的なワークフローまたはアプリ名。例: 「コード生成」や「カスタマーサービス」  
    - `trace_id`: トレース固有の ID。渡さなければ自動生成されます。形式は `trace_<32_alphanumeric>`  
    - `group_id`: 省略可。複数のトレースを同一の会話に紐づけるための ID。例: チャットスレッド ID  
    - `disabled`: `True` の場合、このトレースは記録されません  
    - `metadata`: トレースに付与する任意のメタデータ  
- **スパン**: 開始時刻と終了時刻を持つ操作を表します。  
    - `started_at` と `ended_at` タイムスタンプ  
    - 所属するトレースを示す `trace_id`  
    - 親スパンを指す `parent_id`（存在する場合）  
    - スパンに関する情報を格納する `span_data`。例: `AgentSpanData` はエージェント情報、`GenerationSpanData` は LLM 生成情報など

## デフォルトのトレーシング

デフォルトでは、SDK は以下をトレースします。

- `Runner.{run, run_sync, run_streamed}()` 全体を `trace()` でラップ
- エージェント実行ごとに `agent_span()` でラップ
- LLM 生成を `generation_span()` でラップ
- 関数ツール呼び出しを `function_span()` でラップ
- ガードレールを `guardrail_span()` でラップ
- ハンドオフを `handoff_span()` でラップ
- 音声入力（音声→テキスト）を `transcription_span()` でラップ
- 音声出力（テキスト→音声）を `speech_span()` でラップ
- 関連する音声スパンは `speech_group_span()` の下に配置される場合があります

デフォルトのトレース名は「Agent trace」です。`trace` を使用して名前を設定するか、[`RunConfig`][agents.run.RunConfig] で名前やその他プロパティを構成できます。

さらに、[カスタムトレーシングプロセッサ](#custom-tracing-processors) を設定して、別の送信先へトレースを送る（置き換えまたは追加送信）ことも可能です。

## 上位レベルのトレース

複数回の `run()` 呼び出しを 1 つのトレースにまとめたい場合、コード全体を `trace()` でラップできます。

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

1. `with trace()` で 2 回の `Runner.run` をラップしているため、それぞれが個別のトレースを作成せず、1 つのトレース内に含まれます。

## トレースの作成

[`trace()`][agents.tracing.trace] 関数を使用してトレースを作成できます。トレースは開始と終了が必要で、次の 2 通りの方法があります。

1. **推奨**: コンテキストマネージャとして使用（例: `with trace(...) as my_trace`）。自動的に開始と終了が行われます。  
2. [`trace.start()`][agents.tracing.Trace.start] と [`trace.finish()`][agents.tracing.Trace.finish] を手動で呼び出す

現在のトレースは Python の [`contextvar`](https://docs.python.org/3/library/contextvars.html) で管理されるため、並行処理にも自動対応します。トレースを手動で開始／終了する場合は、`start()`／`finish()` に `mark_as_current` と `reset_current` を渡して現在のトレースを更新してください。

## スパンの作成

各種 [`*_span()`][agents.tracing.create] メソッドでスパンを作成できますが、通常は手動でスパンを作成する必要はありません。カスタム情報を追跡したい場合は [`custom_span()`][agents.tracing.custom_span] が利用可能です。

スパンは自動的に現在のトレースに含まれ、最も近い現在のスパンの下にネストされます。これも Python の [`contextvar`](https://docs.python.org/3/library/contextvars.html) で管理されます。

## 機微データ

一部のスパンは機微なデータを含む場合があります。

`generation_span()` には LLM 生成の入出力が、`function_span()` には関数呼び出しの入出力が保存されます。機微データを含む可能性があるため、[`RunConfig.trace_include_sensitive_data`][agents.run.RunConfig.trace_include_sensitive_data] でこれらのデータ記録を無効化できます。

同様に、オーディオスパンにはデフォルトで base64 エンコードされた PCM データ（音声入力・出力）が含まれます。録音データの記録を無効にするには、[`VoicePipelineConfig.trace_include_sensitive_audio_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_audio_data] を設定してください。

## カスタムトレーシングプロセッサ

トレーシングのハイレベルな構成は以下のとおりです。

- 初期化時にグローバル [`TraceProvider`][agents.tracing.setup.TraceProvider] を作成し、トレースを生成  
- `TraceProvider` に [`BatchTraceProcessor`][agents.tracing.processors.BatchTraceProcessor] を設定し、トレース／スパンをバッチで [`BackendSpanExporter`][agents.tracing.processors.BackendSpanExporter] へ送信  
- `BackendSpanExporter` が OpenAI バックエンドへバッチ送信

このデフォルト設定をカスタマイズして別のバックエンドへ送信したり、エクスポーターの動作を変更したりするには次の 2 つの方法があります。

1. [`add_trace_processor()`][agents.tracing.add_trace_processor]: 既定の送信に加え、**追加** のトレースプロセッサを登録  
2. [`set_trace_processors()`][agents.tracing.set_trace_processors]: 既定のプロセッサを **置き換え**、独自のトレースプロセッサを使用（OpenAI バックエンドへ送信したい場合は対応する `TracingProcessor` を含める必要があります）

## 外部トレーシングプロセッサ一覧

- Weights & Biases
- Arize-Phoenix
- Future AGI
- MLflow (self-hosted/OSS
- MLflow (Databricks hosted
- Braintrust
- Pydantic Logfire
- AgentOps
- Scorecard
- Keywords AI
- LangSmith
- Maxim AI
- Comet Opik
- Langfuse
- Langtrace
- Okahu-Monocle
- Galileo
- Portkey AI