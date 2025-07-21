---
search:
  exclude: true
---
# モデルコンテキストプロトコル (MCP)

[Model context protocol](https://modelcontextprotocol.io/introduction)（略称 MCP）は、 LLM にツールとコンテキストを提供する方法です。MCP のドキュメントからの引用です。

> MCP は、アプリケーションが LLM にコンテキストを渡す方法を標準化するオープンプロトコルです。MCP を AI アプリケーション向けの USB-C ポートのように考えてください。USB-C がデバイスをさまざまな周辺機器やアクセサリに接続するための標準化された方法を提供するのと同様に、MCP は AI モデルを異なるデータソースやツールに接続するための標準化された方法を提供します。

Agents SDK は MCP をサポートしています。これにより、幅広い MCP サーバーを利用してエージェントにツールやプロンプトを提供できます。

## MCP サーバー

現在、 MCP 仕様では使用するトランスポートメカニズムに応じて 3 種類のサーバーが定義されています。

1. **stdio** サーバー: アプリケーションのサブプロセスとして実行されます。ローカルで動作していると考えることができます。  
2. **HTTP over SSE** サーバー: リモートで実行され、 URL で接続します。  
3. **Streamable HTTP** サーバー: MCP 仕様で定義されている Streamable HTTP トランスポートを使用してリモートで実行されます。  

これらのサーバーへは [`MCPServerStdio`][agents.mcp.server.MCPServerStdio]、 [`MCPServerSse`][agents.mcp.server.MCPServerSse]、 [`MCPServerStreamableHttp`][agents.mcp.server.MCPServerStreamableHttp] クラスを使用して接続できます。

たとえば、公式の MCP ファイルシステムサーバー <https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem> を使用する場合は次のようになります。

```python
from agents.run_context import RunContextWrapper

async with MCPServerStdio(
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
    }
) as server:
    # Note: In practice, you typically add the server to an Agent
    # and let the framework handle tool listing automatically.
    # Direct calls to list_tools() require run_context and agent parameters.
    run_context = RunContextWrapper(context=None)
    agent = Agent(name="test", instructions="test")
    tools = await server.list_tools(run_context, agent)
```

## MCP サーバーの利用

MCP サーバーはエージェントに追加できます。 Agents SDK はエージェントが実行されるたびに MCP サーバーの `list_tools()` を呼び出し、 LLM に MCP サーバーのツールを認識させます。 LLM が MCP サーバーのツールを呼び出すと、 SDK はそのサーバーの `call_tool()` を実行します。

```python

agent=Agent(
    name="Assistant",
    instructions="Use the tools to achieve the task",
    mcp_servers=[mcp_server_1, mcp_server_2]
)
```

## ツールフィルタリング

MCP サーバーにツールフィルターを設定することで、エージェントが利用可能なツールを制限できます。 SDK は静的および動的の両方のツールフィルタリングをサポートします。

### 静的ツールフィルタリング

単純な許可 / ブロックリストであれば、静的フィルタリングを利用できます。

```python
from agents.mcp import create_static_tool_filter

# Only expose specific tools from this server
server = MCPServerStdio(
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
    },
    tool_filter=create_static_tool_filter(
        allowed_tool_names=["read_file", "write_file"]
    )
)

# Exclude specific tools from this server
server = MCPServerStdio(
    params={
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
    },
    tool_filter=create_static_tool_filter(
        blocked_tool_names=["delete_file"]
    )
)

```

**`allowed_tool_names` と `blocked_tool_names` の両方を設定した場合の処理順は次のとおりです。**  
1. まず `allowed_tool_names`（許可リスト）を適用し、指定されたツールのみを残します  
2. 次に `blocked_tool_names`（ブロックリスト）を適用し、残ったツールから指定されたツールを除外します  

たとえば `allowed_tool_names=["read_file", "write_file", "delete_file"]` と `blocked_tool_names=["delete_file"]` を設定した場合、利用可能なのは `read_file` と `write_file` のみになります。

### 動的ツールフィルタリング

より複雑なフィルタリングロジックが必要な場合は、関数を使った動的フィルターを使用できます。

```python
from agents.mcp import ToolFilterContext

# Simple synchronous filter
def custom_filter(context: ToolFilterContext, tool) -> bool:
    """Example of a custom tool filter."""
    # Filter logic based on tool name patterns
    return tool.name.startswith("allowed_prefix")

# Context-aware filter
def context_aware_filter(context: ToolFilterContext, tool) -> bool:
    """Filter tools based on context information."""
    # Access agent information
    agent_name = context.agent.name

    # Access server information  
    server_name = context.server_name

    # Implement your custom filtering logic here
    return some_filtering_logic(agent_name, server_name, tool)

# Asynchronous filter
async def async_filter(context: ToolFilterContext, tool) -> bool:
    """Example of an asynchronous filter."""
    # Perform async operations if needed
    result = await some_async_check(context, tool)
    return result

server = MCPServerStdio(
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
    },
    tool_filter=custom_filter  # or context_aware_filter or async_filter
)
```

`ToolFilterContext` では次の情報にアクセスできます。  
- `run_context`: 現在の実行コンテキスト  
- `agent`: ツールを要求しているエージェント  
- `server_name`: MCP サーバー名  

## プロンプト

MCP サーバーは、エージェントの instructions を動的に生成するためのプロンプトも提供できます。これにより、パラメーターでカスタマイズ可能な再利用可能な instructions テンプレートを作成できます。

### プロンプトの利用

プロンプトをサポートする MCP サーバーは次の 2 つの主要メソッドを提供します。  
- `list_prompts()`: サーバー上で利用可能なすべてのプロンプトを一覧表示します  
- `get_prompt(name, arguments)`: 任意のパラメーターとともに指定したプロンプトを取得します  

```python
# List available prompts
prompts_result = await server.list_prompts()
for prompt in prompts_result.prompts:
    print(f"Prompt: {prompt.name} - {prompt.description}")

# Get a specific prompt with parameters
prompt_result = await server.get_prompt(
    "generate_code_review_instructions",
    {"focus": "security vulnerabilities", "language": "python"}
)
instructions = prompt_result.messages[0].content.text

# Use the prompt-generated instructions with an Agent
agent = Agent(
    name="Code Reviewer",
    instructions=instructions,  # Instructions from MCP prompt
    mcp_servers=[server]
)
```

## キャッシュ

エージェントが実行されるたびに、 MCP サーバーの `list_tools()` が呼び出されます。サーバーがリモートの場合は特に、これがレイテンシの要因になることがあります。ツール一覧を自動でキャッシュするには、 [`MCPServerStdio`][agents.mcp.server.MCPServerStdio]、 [`MCPServerSse`][agents.mcp.server.MCPServerSse]、 [`MCPServerStreamableHttp`][agents.mcp.server.MCPServerStreamableHttp] に `cache_tools_list=True` を渡してください。ツール一覧が変化しないことが確実な場合のみ使用してください。

キャッシュを無効化したい場合は、サーバーの `invalidate_tools_cache()` を呼び出します。

## エンドツーエンドのコード例

[examples/mcp](https://github.com/openai/openai-agents-python/tree/main/examples/mcp) で完全な動作例をご覧いただけます。

## トレーシング

[トレーシング](./tracing.md) では MCP の操作を自動で記録します。具体的には次の情報が含まれます。  
1. MCP サーバーへのツール一覧取得呼び出し  
2. 関数呼び出しに関する MCP 関連情報  

![MCP Tracing Screenshot](../assets/images/mcp-tracing.jpg)