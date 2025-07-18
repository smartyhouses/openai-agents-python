---
search:
  exclude: true
---
# Model context protocol (MCP)

[Model context protocol] (通称 **MCP**) は、 LLM にツールとコンテキストを提供するための仕組みです。 MCP のドキュメントによると、  

> MCP は、アプリケーションが LLM にコンテキストを提供する方法を標準化するオープンプロトコルです。 USB-C がデバイスをさまざまな周辺機器やアクセサリーにつなぐ共通規格であるのと同じように、 MCP は AI モデルを多様なデータソースやツールへ接続する共通規格を提供します。

Agents SDK は MCP をサポートしています。これにより、幅広い MCP サーバーを利用してエージェントにツールやプロンプトを提供できます。

## MCP サーバー

現在の MCP 仕様では、使用するトランスポート方式に基づき、次の 3 種類のサーバーが定義されています。

1. **stdio** サーバー: アプリケーションのサブプロセスとして実行され、いわゆる「ローカル」で動作します。  
2. **HTTP over SSE** サーバー: リモートで動作し、 URL を介して接続します。  
3. **Streamable HTTP** サーバー: MCP 仕様で定義された Streamable HTTP トランスポートを用いてリモートで動作します。  

これらのサーバーへは [`MCPServerStdio`][agents.mcp.server.MCPServerStdio]、 [`MCPServerSse`][agents.mcp.server.MCPServerSse]、 [`MCPServerStreamableHttp`][agents.mcp.server.MCPServerStreamableHttp] クラスで接続できます。

たとえば、公式 MCP ファイルシステムサーバーを利用する場合は次のようにします。

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

## Using MCP servers

MCP サーバーはエージェントに追加できます。 Agents SDK はエージェントが実行されるたびに MCP サーバーの `list_tools()` を呼び出し、 LLM にそのサーバーのツールを認識させます。 LLM が MCP サーバー上のツールを呼び出すと、 SDK はサーバーの `call_tool()` を実行します。

```python

agent=Agent(
    name="Assistant",
    instructions="Use the tools to achieve the task",
    mcp_servers=[mcp_server_1, mcp_server_2]
)
```

## Tool filtering

MCP サーバーでツールフィルターを設定すると、エージェントが利用できるツールを絞り込めます。 SDK は静的および動的フィルタリングの両方をサポートしています。

### Static tool filtering

シンプルな許可／ブロックリストには静的フィルタリングを使用します。

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

**`allowed_tool_names` と `blocked_tool_names` の両方を設定した場合、処理順序は以下のとおりです。**  
1. まず `allowed_tool_names`（許可リスト）を適用 — 指定されたツールのみを残す  
2. 次に `blocked_tool_names`（ブロックリスト）を適用 — 残ったツールから指定されたツールを除外する  

例: `allowed_tool_names=["read_file", "write_file", "delete_file"]` と `blocked_tool_names=["delete_file"]` を設定すると、利用可能なのは `read_file` と `write_file` だけになります。

### Dynamic tool filtering

より複雑なロジックが必要な場合は、関数を使った動的フィルタリングを利用します。

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
- `run_context`: 現在のランコンテキスト  
- `agent`: ツールを要求しているエージェント  
- `server_name`: MCP サーバー名  

## Prompts

MCP サーバーはプロンプトも提供でき、これを使ってエージェントの instructions を動的に生成できます。パラメーターを渡して再利用可能な instruction テンプレートを作成できます。

### Using prompts

プロンプトをサポートする MCP サーバーは、次の 2 つの主要メソッドを提供します。  

- `list_prompts()`: サーバー上で利用可能なすべてのプロンプトを一覧表示  
- `get_prompt(name, arguments)`: 具体的なプロンプトをオプションのパラメーター付きで取得  

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

## Caching

エージェントが実行されるたびに MCP サーバーの `list_tools()` が呼び出されるため、サーバーがリモートの場合はレイテンシが発生することがあります。ツール一覧を自動的にキャッシュするには、 [`MCPServerStdio`][agents.mcp.server.MCPServerStdio]、 [`MCPServerSse`][agents.mcp.server.MCPServerSse]、 [`MCPServerStreamableHttp`][agents.mcp.server.MCPServerStreamableHttp] で `cache_tools_list=True` を渡してください。ツール一覧が変更されないことが確実な場合のみ推奨されます。

キャッシュを無効化したい場合は、サーバーの `invalidate_tools_cache()` を呼び出せます。

## End-to-end examples

完全な動作例は [examples/mcp](https://github.com/openai/openai-agents-python/tree/main/examples/mcp) をご覧ください。

## Tracing

[Tracing](./tracing.md) は MCP の操作を自動でキャプチャし、次を含みます。

1. ツール一覧取得のための MCP サーバー呼び出し  
2. 関数呼び出しに関する MCP 関連情報  

![MCP Tracing Screenshot](../assets/images/mcp-tracing.jpg)