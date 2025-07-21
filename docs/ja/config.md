---
search:
  exclude: true
---
# SDK の設定

## API キーとクライアント

デフォルトでは、 SDK はインポートされた時点で LLM リクエストとトレーシング用に `OPENAI_API_KEY` 環境変数を参照します。アプリが開始する前にこの環境変数を設定できない場合は、[set_default_openai_key()][agents.set_default_openai_key] 関数を使用してキーを設定できます。

```python
from agents import set_default_openai_key

set_default_openai_key("sk-...")
```

また、使用する OpenAI クライアントを設定することもできます。デフォルトでは、 SDK は環境変数または上記で設定した既定のキーを用いて `AsyncOpenAI` インスタンスを生成します。[set_default_openai_client()][agents.set_default_openai_client] 関数を使用すると、これを変更できます。

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client

custom_client = AsyncOpenAI(base_url="...", api_key="...")
set_default_openai_client(custom_client)
```

さらに、利用する OpenAI API をカスタマイズすることもできます。デフォルトでは OpenAI Responses API を使用しますが、[set_default_openai_api()][agents.set_default_openai_api] 関数を使って Chat Completions API に切り替えられます。

```python
from agents import set_default_openai_api

set_default_openai_api("chat_completions")
```

## トレーシング

トレーシングはデフォルトで有効になっています。前述の OpenAI API キー（環境変数または既定のキー）が自動的に使用されます。トレーシングに使用する API キーを明示的に設定したい場合は、[`set_tracing_export_api_key`][agents.set_tracing_export_api_key] 関数をご利用ください。

```python
from agents import set_tracing_export_api_key

set_tracing_export_api_key("sk-...")
```

トレーシングを完全に無効化したい場合は、[`set_tracing_disabled()`][agents.set_tracing_disabled] 関数を使用します。

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)
```

## デバッグロギング

SDK にはハンドラーが設定されていない Python ロガーが 2 つあります。デフォルト状態では、警告とエラーは `stdout` に出力されますが、それ以外のログは抑制されます。

詳細なログ出力を有効にするには、[`enable_verbose_stdout_logging()`][agents.enable_verbose_stdout_logging] 関数を使用します。

```python
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()
```

また、ハンドラー、フィルター、フォーマッターなどを追加してログをカスタマイズすることも可能です。詳しくは [Python logging guide](https://docs.python.org/3/howto/logging.html) をご覧ください。

```python
import logging

logger = logging.getLogger("openai.agents") # or openai.agents.tracing for the Tracing logger

# To make all logs show up
logger.setLevel(logging.DEBUG)
# To make info and above show up
logger.setLevel(logging.INFO)
# To make warning and above show up
logger.setLevel(logging.WARNING)
# etc

# You can customize this as needed, but this will output to `stderr` by default
logger.addHandler(logging.StreamHandler())
```

### ログに含まれる機密データ

一部のログには、ユーザー データなどの機密データが含まれる場合があります。これらのデータをログに出力したくない場合は、以下の環境変数を設定してください。

LLM の入力と出力のログを無効にするには:

```bash
export OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1
```

ツールの入力と出力のログを無効にするには:

```bash
export OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1
```