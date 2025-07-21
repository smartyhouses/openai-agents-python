---
search:
  exclude: true
---
# ガイド

このガイドでは、 OpenAI Agents SDK の realtime 機能を用いて音声対応 AI エージェントを構築する方法を詳しく解説します。

!!! warning "Beta feature"
Realtime エージェントはベータ版です。実装の改善に伴い、破壊的変更が行われる可能性があります。

## 概要

Realtime エージェントは、音声とテキスト入力をリアルタイムで処理し、リアルタイム音声で応答する対話フローを実現します。 OpenAI の Realtime API と永続接続を維持し、低レイテンシかつ割り込みにも柔軟に対応できる自然な音声会話を可能にします。

## アーキテクチャ

### コアコンポーネント

realtime システムは、次の主要コンポーネントで構成されます。

-   ** RealtimeAgent **: instructions、tools、handoffs で構成されたエージェントです。  
-   ** RealtimeRunner **: 設定を管理します。 `runner.run()` を呼び出すとセッションを取得できます。  
-   ** RealtimeSession **: 1 回の対話セッションを表します。通常、ユーザーが会話を開始するたびに作成し、会話が終了するまで保持します。  
-   ** RealtimeModel **: 基盤となるモデルインターフェース（通常は OpenAI の WebSocket 実装）  

### セッションフロー

典型的な realtime セッションは次のフローで進行します。

1. ** RealtimeAgent ** を instructions、tools、handoffs と共に作成します。  
2. エージェントと設定オプションを使用して ** RealtimeRunner ** をセットアップします。  
3. `await runner.run()` で **セッションを開始** し、 RealtimeSession を取得します。  
4. `send_audio()` または `send_message()` で **音声またはテキストメッセージを送信** します。  
5. セッションを反復処理して **イベントをリッスン** します。イベントには音声出力、転写、ツール呼び出し、ハンドオフ、エラーなどがあります。  
6. ユーザーがエージェントの発話をさえぎった場合に **割り込みを処理** します。これにより現在の音声生成が自動的に停止します。  

セッションは会話履歴を保持し、 realtime モデルとの永続接続を管理します。

## エージェント設定

RealtimeAgent は通常の Agent クラスとほぼ同様に機能しますが、いくつかの重要な違いがあります。詳細は [`RealtimeAgent`][agents.realtime.agent.RealtimeAgent] API リファレンスをご覧ください。

主な違い:

-   モデルの選択はエージェントレベルではなくセッションレベルで設定します。  
-   structured outputs のサポートはありません（`outputType` はサポートされていません）。  
-   音声はエージェントごとに設定できますが、最初のエージェントが発話した後に変更できません。  
-   それ以外の tools、handoffs、instructions などの機能は同じです。  

## セッション設定

### モデル設定

セッション設定では、基盤となる realtime モデルの挙動を制御できます。モデル名（例: `gpt-4o-realtime-preview`）、音声（alloy, echo, fable, onyx, nova, shimmer）や対応モダリティ（text / audio）を指定できます。音声フォーマットは入力・出力ともに設定可能で、デフォルトは PCM16 です。

### オーディオ設定

オーディオ設定では、音声入力と出力の扱いを制御します。Whisper などのモデルを用いた入力音声の転写、言語設定、ドメイン固有用語の精度を高める転写プロンプトを指定できます。ターン検出設定では、音声活動検出しきい値、無音時間、検出された発話周辺のパディングなどにより、エージェントがいつ応答を開始・停止すべきかを制御します。

## ツールと関数

### ツールの追加

通常のエージェントと同様に、 realtime エージェントは会話中に実行される function tools をサポートしています。

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Your weather API logic here
    return f"The weather in {city} is sunny, 72°F"

@function_tool
def book_appointment(date: str, time: str, service: str) -> str:
    """Book an appointment."""
    # Your booking logic here
    return f"Appointment booked for {service} on {date} at {time}"

agent = RealtimeAgent(
    name="Assistant",
    instructions="You can help with weather and appointments.",
    tools=[get_weather, book_appointment],
)
```

## ハンドオフ

### ハンドオフの作成

ハンドオフを利用すると、会話を専門特化したエージェント間で引き継ぐことができます。

```python
from agents.realtime import realtime_handoff

# Specialized agents
billing_agent = RealtimeAgent(
    name="Billing Support",
    instructions="You specialize in billing and payment issues.",
)

technical_agent = RealtimeAgent(
    name="Technical Support",
    instructions="You handle technical troubleshooting.",
)

# Main agent with handoffs
main_agent = RealtimeAgent(
    name="Customer Service",
    instructions="You are the main customer service agent. Hand off to specialists when needed.",
    handoffs=[
        realtime_handoff(billing_agent, tool_description="Transfer to billing support"),
        realtime_handoff(technical_agent, tool_description="Transfer to technical support"),
    ]
)
```

## イベント処理

セッションはイベントをストリーミングし、セッションオブジェクトを反復処理することでリッスンできます。イベントには音声出力チャンク、転写結果、ツール実行開始・終了、エージェントハンドオフ、エラーなどがあります。主に扱うべきイベントは以下です。

-   **audio**: エージェント応答の raw 音声データ  
-   **audio_end**: エージェントの発話終了  
-   **audio_interrupted**: ユーザーがエージェントを割り込み  
-   **tool_start/tool_end**: ツール実行ライフサイクル  
-   **handoff**: エージェントのハンドオフ発生  
-   **error**: 処理中にエラー発生  

完全なイベント詳細は [`RealtimeSessionEvent`][agents.realtime.events.RealtimeSessionEvent] を参照してください。

## ガードレール

Realtime エージェントでサポートされるのは出力ガードレールのみです。リアルタイム生成中のパフォーマンスを維持するため、ガードレールはデバウンスされ定期的に実行されます（毎単語ではありません）。デフォルトのデバウンス長は 100 文字ですが、設定可能です。

ガードレールがトリガーされると `guardrail_tripped` イベントが生成され、エージェントの現在の応答を割り込むことがあります。デバウンス動作により、安全性とリアルタイム性能のバランスを取ります。テキストエージェントと異なり、 realtime エージェントはガードレール発動時に Exception を発生させません。

## オーディオ処理

[`session.send_audio(audio_bytes)`][agents.realtime.session.RealtimeSession.send_audio] で音声を、 [`session.send_message()`][agents.realtime.session.RealtimeSession.send_message] でテキストをセッションへ送信します。

音声出力を取得するには `audio` イベントをリッスンし、お好みのオーディオライブラリで再生してください。ユーザーが割り込んだ際に即座に再生を停止しキューにある音声をクリアするため、 `audio_interrupted` イベントも必ずリッスンしてください。

## 直接モデルにアクセス

低レベルでの接続制御やカスタムリスナー追加など高度な操作が必要な場合、基盤モデルに直接アクセスできます。

```python
# Add a custom listener to the model
session.model.add_listener(my_custom_listener)
```

これにより、 [`RealtimeModel`][agents.realtime.model.RealtimeModel] インターフェースへ直接アクセスし、より柔軟なユースケースに対応できます。

## コード例

完全な動作例は [examples/realtime ディレクトリ](https://github.com/openai/openai-agents-python/tree/main/examples/realtime) を参照してください。 UI コンポーネントあり・なし両方のデモを含みます。