---
search:
  exclude: true
---
# コンテキスト管理

コンテキストという語は多義的です。主に次の 2 種類のコンテキストがあります。

1. コード内でローカルに利用できるコンテキスト: これはツール関数の実行時や `on_handoff` のようなコールバック、ライフサイクルフックなどで必要となるデータや依存関係です。  
2. LLM が利用できるコンテキスト: これは LLM が応答を生成する際に参照するデータです。

## ローカル コンテキスト

これは [`RunContextWrapper`][agents.run_context.RunContextWrapper] クラスと、その内部にある [`context`][agents.run_context.RunContextWrapper.context] プロパティによって表現されます。仕組みは次のとおりです:

1. 任意の Python オブジェクトを作成します。一般的には dataclass や Pydantic オブジェクトを使用するパターンがよく見られます。  
2. そのオブジェクトを各種 run メソッド (例: `Runner.run(..., **context=whatever**)`) に渡します。  
3. すべてのツール呼び出しやライフサイクルフックには `RunContextWrapper[T]` というラッパーオブジェクトが渡されます。ここで `T` はコンテキストオブジェクトの型であり、 `wrapper.context` からアクセスできます。  

**最も重要なポイント**: 特定のエージェント実行においては、エージェント本体、ツール関数、ライフサイクルフックなど、すべてが同じ _型_ のコンテキストを使用しなければなりません。

コンテキストは次のような用途に使用できます:

- エージェント実行時の状況データ (例: username/uid など ユーザー に関する情報)  
- 依存関係 (例: logger オブジェクトやデータフェッチャーなど)  
- ヘルパー関数  

!!! danger "Note"

    コンテキストオブジェクトは ** LLM ** に送信されません。完全にローカルなオブジェクトであり、読み書きやメソッド呼び出しを自由に行えます。

```python
import asyncio
from dataclasses import dataclass

from agents import Agent, RunContextWrapper, Runner, function_tool

@dataclass
class UserInfo:  # (1)!
    name: str
    uid: int

@function_tool
async def fetch_user_age(wrapper: RunContextWrapper[UserInfo]) -> str:  # (2)!
    """Fetch the age of the user. Call this function to get user's age information."""
    return f"The user {wrapper.context.name} is 47 years old"

async def main():
    user_info = UserInfo(name="John", uid=123)

    agent = Agent[UserInfo](  # (3)!
        name="Assistant",
        tools=[fetch_user_age],
    )

    result = await Runner.run(  # (4)!
        starting_agent=agent,
        input="What is the age of the user?",
        context=user_info,
    )

    print(result.final_output)  # (5)!
    # The user John is 47 years old.

if __name__ == "__main__":
    asyncio.run(main())
```

1. これはコンテキストオブジェクトです。ここでは dataclass を使っていますが、どのような型でも構いません。  
2. これはツールです。`RunContextWrapper[UserInfo]` を受け取ることが分かります。ツールの実装はコンテキストから値を読み取ります。  
3. エージェントにはジェネリック型 `UserInfo` を指定しています。これにより、異なるコンテキスト型を取るツールを渡そうとした場合などに、型チェッカーがエラーを検出できます。  
4. コンテキストは `run` 関数に渡されます。  
5. エージェントはツールを正しく呼び出し、年齢を取得します。  

## エージェント / LLM コンテキスト

 LLM が呼び出される際、**唯一** 見ることができるデータは会話履歴だけです。そのため、 LLM に新しいデータを渡したい場合は、そのデータを会話履歴に含める形で提供しなければなりません。主な方法は次のとおりです:

1. Agent の `instructions` に追加する。これは "system prompt" または "developer message" とも呼ばれます。system prompt は固定文字列でも、コンテキストを受け取って文字列を返す動的関数でも構いません。たとえば ユーザー の名前や現在の日付など、常に有用な情報を渡す際に一般的な手法です。  
2. `Runner.run` を呼び出す際の `input` に追加する。この方法は `instructions` と似ていますが、[指揮系統](https://cdn.openai.com/spec/model-spec-2024-05-08.html#follow-the-chain-of-command) の下位にメッセージを配置できる点が異なります。  
3. function tools を介して公開する。これは _オンデマンド_ コンテキストに便利です。 LLM が必要だと判断したタイミングでツールを呼び出し、データを取得できます。  
4. retrieval や web search を利用する。これらはファイルやデータベースから関連データを取得する retrieval、または Web から情報を取得する web search といった特殊なツールです。関連コンテキストに基づいた回答を "グラウンディング" する場合に有効です。