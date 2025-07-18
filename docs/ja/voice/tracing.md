---
search:
  exclude: true
---
# トレーシング

[エージェントのトレーシング方法](../tracing.md)と同様に、音声パイプラインも自動的にトレーシングされます。

上記のトレーシングドキュメントで基本情報をご確認いただけますが、[`VoicePipelineConfig`][agents.voice.pipeline_config.VoicePipelineConfig] を使ってパイプラインのトレーシングを追加で設定することも可能です。

主なトレーシング関連のフィールドは次のとおりです:

- [`tracing_disabled`][agents.voice.pipeline_config.VoicePipelineConfig.tracing_disabled]: トレーシングを無効にするかどうかを制御します。デフォルトではトレーシングは有効です。  
- [`trace_include_sensitive_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_data]: 音声の書き起こしなど、機密になり得るデータをトレースに含めるかどうかを制御します。これは音声パイプライン専用で、ワークフロー内部の処理には影響しません。  
- [`trace_include_sensitive_audio_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_audio_data]: 音声データ自体をトレースに含めるかどうかを制御します。  
- [`workflow_name`][agents.voice.pipeline_config.VoicePipelineConfig.workflow_name]: トレースするワークフローの名前です。  
- [`group_id`][agents.voice.pipeline_config.VoicePipelineConfig.group_id]: 複数のトレースを関連付けるための `group_id` です。  
- [`trace_metadata`][agents.voice.pipeline_config.VoicePipelineConfig.tracing_disabled]: トレースに追加するメタデータです。