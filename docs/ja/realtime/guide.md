---
search:
  exclude: true
---
# ガイド

このガイドでは、 OpenAI Agents SDK のリアルタイム機能を使って音声対応の AI エージェントを構築する方法を詳しく説明します。

!!! warning "ベータ機能"
リアルタイム エージェントはベータ版です。実装の改善に伴い、破壊的変更が入る可能性があります。

## 概要

リアルタイム エージェントは、音声およびテキスト入力をリアルタイムに処理し、リアルタイムの音声で応答できる会話フローを実現します。 OpenAI の Realtime API と持続的に接続を保ち、低レイテンシで自然な音声対話を行い、割り込みにも柔軟に対応します。

## アーキテクチャ

### コアコンポーネント

リアルタイム システムは、次の主要コンポーネントで構成されます。

- **RealtimeAgent**: instructions、tools、handoffs で設定されたエージェント
- **RealtimeRunner**: 設定を管理します。 `runner.run()` を呼び出すとセッションを取得できます。
- **RealtimeSession**: 1 回の対話セッション。 ユーザーが会話を開始するたびに作成し、会話が終了するまで保持します。
- **RealtimeModel**: 基盤となるモデル インターフェース (通常は OpenAI の WebSocket 実装)

### セッションフロー

一般的なリアルタイム セッションの流れは次のとおりです。

1. **RealtimeAgent** を instructions、tools、handoffs 付きで作成します。
2. エージェントと構成オプションを使って **RealtimeRunner** をセットアップします。
3. `await runner.run()` で **セッションを開始** し、 RealtimeSession を取得します。
4. `send_audio()` または `send_message()` で **音声またはテキスト メッセージを送信** します。
5. セッションを反復しながら **イベントを監視** します。イベントには音声出力、転写、ツール呼び出し、ハンドオフ、エラーなどがあります。
6. ユーザーがエージェントの発話中に話し始めたときの **割り込みに対応** します。割り込みがあると現在の音声生成が自動的に停止します。

セッションは会話履歴を保持し、リアルタイム モデルとの持続接続を管理します。

## エージェント構成

RealtimeAgent は通常の Agent クラスとほぼ同じですが、いくつか重要な違いがあります。詳細な API は [`RealtimeAgent`][agents.realtime.agent.RealtimeAgent] リファレンスをご覧ください。

通常のエージェントとの主な違い:

- モデル選択はエージェント レベルではなくセッション レベルで設定します。
- structured outputs はサポートされません ( `outputType` は使用不可)。
- 音声はエージェント単位で設定できますが、最初のエージェントが発話した後に変更できません。
- その他の機能 (tools、handoffs、instructions など) は同じ方法で動作します。

## セッション構成

### モデル設定

セッション構成では基盤となるリアルタイム モデルの挙動を制御できます。モデル名 (例: `gpt-4o-realtime-preview`)、音声選択 ( alloy、echo、fable、onyx、nova、shimmer )、対応モダリティ (テキストおよび/または音声) を設定可能です。入出力のオーディオ形式も指定でき、デフォルトは PCM16 です。

### オーディオ設定

オーディオ設定では、音声入力と出力の扱い方を制御します。 Whisper などのモデルを用いた入力音声の転写、言語設定、専門用語の精度を高める転写プロンプトを指定できます。ターン検出設定では、音声活動検出しきい値、無音時間、検出された発話前後のパディングなどで、エージェントが応答を開始・終了するタイミングを調整します。

## ツールと関数

### ツールの追加

通常のエージェントと同様に、リアルタイム エージェントでも会話中に実行される function tools をサポートします。

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

ハンドオフを使用すると、会話を専門エージェント間で転送できます。

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

セッションはイベントをストリーム配信します。セッション オブジェクトを反復しながらイベントを監視してください。イベントには、音声出力チャンク、転写結果、ツール実行開始・終了、エージェント ハンドオフ、エラーなどがあります。主なイベントは次のとおりです。

- **audio**: エージェント応答の raw 音声データ
- **audio_end**: エージェントが発話を完了
- **audio_interrupted**: ユーザーがエージェントを割り込み
- **tool_start/tool_end**: ツール実行ライフサイクル
- **handoff**: エージェント ハンドオフが発生
- **error**: 処理中にエラーが発生

イベントの詳細は [`RealtimeSessionEvent`][agents.realtime.events.RealtimeSessionEvent] を参照してください。

## ガードレール

リアルタイム エージェントでは出力ガードレールのみサポートされます。パフォーマンスへの影響を避けるため、ガードレールはデバウンスされ、すべての単語ではなく一定間隔で実行されます。デフォルトのデバウンス長は 100 文字で、設定可能です。

ガードレールが作動すると `guardrail_tripped` イベントが生成され、エージェントの現在の応答を中断できます。デバウンス動作により、安全性とリアルタイム性能のバランスを取ります。テキスト エージェントと異なり、リアルタイム エージェントではガードレール作動時に Exception は発生しません。

## オーディオ処理

[`session.send_audio(audio_bytes)`][agents.realtime.session.RealtimeSession.send_audio] で音声を、 [`session.send_message()`][agents.realtime.session.RealtimeSession.send_message] でテキストをセッションに送信します。

音声出力を再生するには `audio` イベントを監視し、任意のオーディオ ライブラリでデータを再生してください。ユーザーが割り込んだ場合に即座に再生を停止し、キューにある音声をクリアするため、 `audio_interrupted` イベントも必ず監視してください。

## モデルへの直接アクセス

基盤となるモデルに直接アクセスし、独自のリスナーを追加したり、高度な操作を行ったりできます。

```python
# Add a custom listener to the model
session.model.add_listener(my_custom_listener)
```

これにより、低レベルで接続を制御する必要がある高度なユースケース向けに [`RealtimeModel`][agents.realtime.model.RealtimeModel] インターフェースへ直接アクセスできます。

## コード例

完全な動作例は、 [examples/realtime ディレクトリ](https://github.com/openai/openai-agents-python/tree/main/examples/realtime) をご覧ください。 UI コンポーネントあり・なし両方のデモを収録しています。