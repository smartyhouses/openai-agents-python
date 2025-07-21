---
search:
  exclude: true
---
# モデル

Agents SDK には、OpenAI モデルをすぐに利用できる２種類のサポートがあります。

- **推奨**: [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel] は、新しい [Responses API](https://platform.openai.com/docs/api-reference/responses) を使用して OpenAI API を呼び出します。  
- [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] は、[Chat Completions API](https://platform.openai.com/docs/api-reference/chat) を使用して OpenAI API を呼び出します。

## 非 OpenAI モデル

ほとんどの非 OpenAI モデルは、[LiteLLM 統合](./litellm.md) を利用して使用できます。まず、litellm の依存関係グループをインストールします。

```bash
pip install "openai-agents[litellm]"
```

次に、`litellm/` プレフィックスを付けて任意の [サポートされているモデル](https://docs.litellm.ai/docs/providers) を利用します。

```python
claude_agent = Agent(model="litellm/anthropic/claude-3-5-sonnet-20240620", ...)
gemini_agent = Agent(model="litellm/gemini/gemini-2.5-flash-preview-04-17", ...)
```

### 非 OpenAI モデルを使用するその他の方法

他の LLM プロバイダーを統合する方法は、さらに３つあります（コード例は [こちら](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/)）。

1. [`set_default_openai_client`][agents.set_default_openai_client]  
   `AsyncOpenAI` のインスタンスを LLM クライアントとしてグローバルに使用したい場合に便利です。LLM プロバイダーが OpenAI 互換の API エンドポイントを持ち、`base_url` と `api_key` を設定できる場合にご利用ください。設定例は [examples/model_providers/custom_example_global.py](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/custom_example_global.py) を参照してください。

2. [`ModelProvider`][agents.models.interface.ModelProvider]  
   `Runner.run` レベルで指定します。実行中のすべての エージェント に対してカスタムモデルプロバイダーを使用できます。設定例は [examples/model_providers/custom_example_provider.py](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/custom_example_provider.py) を参照してください。

3. [`Agent.model`][agents.agent.Agent.model]  
   個々の Agent インスタンスにモデルを指定できます。エージェントごとに異なるプロバイダーを組み合わせることが可能です。設定例は [examples/model_providers/custom_example_agent.py](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/custom_example_agent.py) を参照してください。多くのモデルを簡単に使用する方法として、[LiteLLM 統合](./litellm.md) もご活用いただけます。

`platform.openai.com` の API キーをお持ちでない場合は、`set_tracing_disabled()` でトレーシングを無効化するか、[別のトレーシングプロセッサー](../tracing.md) を設定することを推奨します。

!!! note
    これらの例では、ほとんどの LLM プロバイダーが Responses API をまだサポートしていないため、Chat Completions API／モデルを使用しています。ご利用の LLM プロバイダーが Responses API をサポートしている場合は、Responses の利用をお勧めします。

## モデルの組み合わせ

１つのワークフロー内で、エージェントごとに異なるモデルを使用したい場合があります。たとえば、簡易的なタスクには小型で高速なモデル、複雑なタスクには高性能な大型モデルを使うといったケースです。[`Agent`][agents.Agent] を設定する際、以下のいずれかでモデルを選択できます。

1. モデル名を直接渡す  
2. 任意のモデル名と、それを [`ModelProvider`][agents.models.interface.ModelProvider] が `Model` インスタンスにマッピングできるよう指定する  
3. [`Model`][agents.models.interface.Model] 実装を直接渡す

!!!note
    SDK は [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel] と [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] の両方に対応していますが、ワークフローごとに１つのモデル形状のみを使用することを推奨します。２つのモデル形状では利用できる機能やツールが異なるためです。モデル形状を混在させる必要がある場合は、使用するすべての機能が両方で利用可能かを確認してください。

```python
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
    model="o3-mini", # (1)!
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model=OpenAIChatCompletionsModel( # (2)!
        model="gpt-4o",
        openai_client=AsyncOpenAI()
    ),
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
    model="gpt-3.5-turbo",
)

async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
```

1. OpenAI モデル名を直接指定しています。  
2. [`Model`][agents.models.interface.Model] 実装を提供しています。

エージェントで使用するモデルをさらに詳細に設定したい場合は、`temperature` などの任意パラメーターを含む [`ModelSettings`][agents.models.interface.ModelSettings] を渡せます。

```python
from agents import Agent, ModelSettings

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.1),
)
```

また、OpenAI の Responses API を使用する場合は、`user` や `service_tier` など[追加の任意パラメーター](https://platform.openai.com/docs/api-reference/responses/create) を指定できます。トップレベルで指定できない場合は、`extra_args` を利用して渡してください。

```python
from agents import Agent, ModelSettings

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model="gpt-4o",
    model_settings=ModelSettings(
        temperature=0.1,
        extra_args={"service_tier": "flex", "user": "user_12345"},
    ),
)
```

## 他の LLM プロバイダーを使用する際の一般的な問題

### トレーシング クライアントの 401 エラー

トレーシング関連のエラーが発生する場合、トレースが OpenAI サーバーにアップロードされる際に OpenAI API キーが無いことが原因です。以下の３つの方法で解決できます。

1. トレーシングを完全に無効化する: [`set_tracing_disabled(True)`][agents.set_tracing_disabled]  
2. トレーシング用の OpenAI キーを設定する: [`set_tracing_export_api_key(...)`][agents.set_tracing_export_api_key]（このキーはトレースのアップロードのみに使用され、[platform.openai.com](https://platform.openai.com/) から取得する必要があります）  
3. OpenAI 以外のトレースプロセッサーを使用する: [トレーシングドキュメント](../tracing.md#custom-tracing-processors) を参照

### Responses API のサポート

SDK はデフォルトで Responses API を使用しますが、多くの LLM プロバイダーはまだ対応していません。そのため 404 などのエラーが発生する場合があります。解決策は２つです。

1. [`set_default_openai_api("chat_completions")`][agents.set_default_openai_api] を呼び出す  
   （`OPENAI_API_KEY` と `OPENAI_BASE_URL` を環境変数で設定している場合に機能します）。  
2. [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] を使用する  
   例は [こちら](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/) でご覧いただけます。

### structured outputs のサポート

一部のモデルプロバイダーは、[structured outputs](https://platform.openai.com/docs/guides/structured-outputs) をサポートしていません。その結果、次のようなエラーが発生することがあります。

```

BadRequestError: Error code: 400 - {'error': {'message': "'response_format.type' : value is not one of the allowed values ['text','json_object']", 'type': 'invalid_request_error'}}

```

これは一部プロバイダーの制限で、JSON 出力には対応していても `json_schema` を指定できないためです。現在修正に取り組んでいますが、JSON スキーマ出力をサポートするプロバイダーの利用を推奨します。そうでない場合、JSON が不正な形式で返され、アプリが頻繁に壊れる恐れがあります。

## プロバイダーを跨いでモデルを混在させる

モデルプロバイダーごとの機能差に注意しないと、エラーが発生する可能性があります。たとえば、OpenAI は structured outputs、マルチモーダル入力、ホスト型の file search や web search をサポートしていますが、多くの他プロバイダーはこれらをサポートしていません。以下の点にご注意ください。

- サポートされていない `tools` を理解しないプロバイダーには送信しない  
- テキストのみのモデルを呼び出す前にマルチモーダル入力を除外する  
- structured JSON 出力をサポートしないプロバイダーでは、不正な JSON が返る場合があることを認識する