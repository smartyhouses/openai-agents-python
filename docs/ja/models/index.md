---
search:
  exclude: true
---
# モデル

Agents SDK には、 OpenAI モデルをそのまま利用できる 2 種類の方式が用意されています。

- **推奨**: [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel] は、 OpenAI API を新しい [Responses API](https://platform.openai.com/docs/api-reference/responses) で呼び出します。  
- [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] は、 OpenAI API を [Chat Completions API](https://platform.openai.com/docs/api-reference/chat) で呼び出します。

## 非 OpenAI モデル

ほとんどの非 OpenAI モデルは [LiteLLM integration](./litellm.md) 経由で利用できます。まずは litellm の依存グループをインストールしてください。

```bash
pip install "openai-agents[litellm]"
```

その後、`litellm/` プレフィックスを付けて、[supported models](https://docs.litellm.ai/docs/providers) のいずれかを使用します。

```python
claude_agent = Agent(model="litellm/anthropic/claude-3-5-sonnet-20240620", ...)
gemini_agent = Agent(model="litellm/gemini/gemini-2.5-flash-preview-04-17", ...)
```

### その他の非 OpenAI モデルの利用方法

他の LLM プロバイダーを統合する方法はさらに 3 つあります（コード例は [こちら](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/) を参照）。

1. [`set_default_openai_client`][agents.set_default_openai_client]  
   `AsyncOpenAI` インスタンスを LLM クライアントとしてグローバルに利用したい場合に便利です。 LLM プロバイダーが OpenAI 互換の API エンドポイントを持ち、`base_url` と `api_key` を設定できるケース向けです。設定例は [examples/model_providers/custom_example_global.py](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/custom_example_global.py) をご覧ください。  
2. [`ModelProvider`][agents.models.interface.ModelProvider]  
   `Runner.run` レベルで利用できます。「この実行ではすべての エージェント に対してカスタムモデルプロバイダーを使う」という指定が可能です。設定例は [examples/model_providers/custom_example_provider.py](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/custom_example_provider.py) をご覧ください。  
3. [`Agent.model`][agents.agent.Agent.model]  
   特定の Agent インスタンスでモデルを指定できます。これにより、 エージェント ごとに異なるプロバイダーを組み合わせて使えます。設定例は [examples/model_providers/custom_example_agent.py](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/custom_example_agent.py) をご覧ください。多くのモデルを簡単に使う方法としては、[LiteLLM integration](./litellm.md) が便利です。

`platform.openai.com` の API キーがない場合は、`set_tracing_disabled()` でトレーシングを無効にするか、[別のトレーシングプロセッサー](../tracing.md) を設定することを推奨します。

!!! note

    これらのコード例では、ほとんどの LLM プロバイダーが Responses API をまだサポートしていないため、 Chat Completions API／モデルを使用しています。もしお使いの LLM プロバイダーが Responses API に対応している場合は、Responses を利用することをお勧めします。

## モデルの組み合わせ

1 つのワークフロー内で、 エージェント ごとに異なるモデルを使いたい場合があります。たとえば、振り分けには小さく高速なモデルを、複雑なタスクには大きく高性能なモデルを使うといったケースです。[`Agent`][agents.Agent] を設定する際、次のいずれかの方法でモデルを指定できます。

1. モデル名を直接渡す。  
2. 任意のモデル名と、それを `Model` インスタンスにマッピングできる [`ModelProvider`][agents.models.interface.ModelProvider] を渡す。  
3. [`Model`][agents.models.interface.Model] 実装を直接渡す。  

!!!note

    SDK は [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel] と [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] の両方の形状をサポートしていますが、ワークフローごとに 1 つのモデル形状のみを使用することを推奨します。両者は利用可能な機能やツールのセットが異なるためです。モデル形状を混在させる必要がある場合は、使用するすべての機能が両方でサポートされていることを確認してください。

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

1. OpenAI モデル名を直接設定しています。  
2. [`Model`][agents.models.interface.Model] 実装を提供しています。  

エージェントで使用するモデルをさらに詳細に設定したい場合は、`temperature` などのオプションを指定できる [`ModelSettings`][agents.models.interface.ModelSettings] を渡します。

```python
from agents import Agent, ModelSettings

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.1),
)
```

また、 OpenAI の Responses API を使用する場合、`user` や `service_tier` など [いくつかの追加パラメーター](https://platform.openai.com/docs/api-reference/responses/create) が利用できます。トップレベルで指定できない場合は、`extra_args` で渡してください。

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

## 他プロバイダー利用時によくある問題

### トレーシングクライアントの 401 エラー

トレースは OpenAI サーバーにアップロードされるため、 OpenAI API キーがないとエラーになります。対処方法は次の 3 つです。

1. トレーシングを完全に無効化する: [`set_tracing_disabled(True)`][agents.set_tracing_disabled]  
2. トレーシング用に OpenAI キーを設定する: [`set_tracing_export_api_key(...)`][agents.set_tracing_export_api_key]  
   この API キーはトレースのアップロードのみに使用され、[platform.openai.com](https://platform.openai.com/) のキーである必要があります。  
3. 非 OpenAI のトレースプロセッサーを使用する。詳細は [tracing docs](../tracing.md#custom-tracing-processors) を参照してください。  

### Responses API サポート

SDK はデフォルトで Responses API を使用しますが、ほとんどの他社 LLM プロバイダーはまだ対応していません。そのため 404 エラーなどが発生することがあります。以下のいずれかで解決してください。

1. [`set_default_openai_api("chat_completions")`][agents.set_default_openai_api] を呼び出す。  
   これは環境変数 `OPENAI_API_KEY` と `OPENAI_BASE_URL` を設定している場合に有効です。  
2. [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] を使用する。コード例は [こちら](https://github.com/openai/openai-agents-python/tree/main/examples/model_providers/) にあります。  

### structured outputs のサポート

一部のモデルプロバイダーは [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) をサポートしていません。その場合、次のようなエラーが発生することがあります。

```

BadRequestError: Error code: 400 - {'error': {'message': "'response_format.type' : value is not one of the allowed values ['text','json_object']", 'type': 'invalid_request_error'}}

```

これは一部プロバイダーの制限で、 JSON 出力自体はサポートするものの、`json_schema` を指定できないというものです。現在修正に取り組んでいますが、 JSON schema 出力をサポートするプロバイダーを使用することを推奨します。そうでない場合、不正な JSON が生成され、アプリが頻繁に壊れる可能性があります。

## プロバイダーを跨いだモデルの混在

モデルプロバイダー間の機能差に注意しないとエラーが発生します。たとえば、 OpenAI は structured outputs、マルチモーダル入力、ホスト型 file search や web search をサポートしますが、多くの他社プロバイダーはこれらをサポートしていません。以下の制限にご注意ください。

- サポートしていない `tools` を理解しないプロバイダーに送らない  
- テキストのみのモデルを呼び出す前にマルチモーダル入力を除去する  
- structured JSON outputs をサポートしないプロバイダーは無効な JSON を返すことがある点を考慮する