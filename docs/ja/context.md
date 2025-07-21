---
search:
  exclude: true
---
# コンテキスト管理

コンテキストという言葉には多くの意味があります。ここでは主に 2 つのコンテキストについて説明します:

1. コードでローカルに利用できるコンテキスト: これは、ツール関数実行時や `on_handoff` のようなコールバック、ライフサイクルフックなどで必要となるデータおよび依存関係です。  
2. LLM が応答を生成するときに参照できるコンテキスト: これは LLM が見るデータです。

## ローカルコンテキスト

これは [`RunContextWrapper`][agents.run_context.RunContextWrapper] クラスとその [`context`][agents.run_context.RunContextWrapper.context] プロパティで表現されます。仕組みは次のとおりです。

1. 任意の Python オブジェクトを作成します。よく使われるパターンは dataclass や Pydantic オブジェクトです。  
2. そのオブジェクトを各種 `run` メソッドに渡します (例: `Runner.run(..., **context=whatever**)`)。  
3. すべてのツール呼び出しやライフサイクルフックには `RunContextWrapper[T]` というラッパーオブジェクトが渡されます。ここで `T` は作成したコンテキストオブジェクトの型で、`wrapper.context` からアクセスできます。  

最も重要なポイント: 同じエージェント実行内のすべてのエージェント、ツール関数、ライフサイクルフックは、同一の _型_ のコンテキストを共有しなければなりません。

コンテキストでできることの例:

- 実行時の状況データ (例: ユーザー名 / UID などユーザーに関する情報)  
- 依存オブジェクト (例: ロガー、データフェッチャーなど)  
- ヘルパー関数  

!!! danger "Note"

    コンテキストオブジェクトは **LLM に送信されません**。これはあくまでローカルオブジェクトであり、読み書きやメソッド呼び出しのみが可能です。

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

1. これはコンテキストオブジェクトです。ここでは dataclass を使用していますが、任意の型を利用できます。  
2. これはツールです。`RunContextWrapper[UserInfo]` を受け取り、実装内でコンテキストを参照しています。  
3. エージェントをジェネリック型 `UserInfo` でマークすることで、型チェッカーが (異なるコンテキスト型を持つツールを渡した場合などの) エラーを検出できます。  
4. `run` 関数にコンテキストを渡します。  
5. エージェントはツールを正しく呼び出し、年齢を取得します。  

## エージェント／LLM コンテキスト

LLM が呼び出されるとき、LLM が参照できるデータは会話履歴に含まれるものだけです。そのため、新しいデータを LLM に提供したい場合は、そのデータを履歴に含める必要があります。主な方法は次のとおりです。

1. エージェントの `instructions` に追加する。これは「system prompt」や「developer message」とも呼ばれます。システムプロンプトは静的文字列でも、コンテキストを受け取って文字列を返す動的関数でもかまいません。ユーザー名や現在の日付のように常に役立つ情報を渡す定番の手法です。  
2. `Runner.run` を呼び出す際の `input` に追加する。`instructions` と似ていますが、[chain of command](https://cdn.openai.com/spec/model-spec-2024-05-08.html#follow-the-chain-of-command) 上でより下位にメッセージを配置できます。  
3. 関数ツール経由で公開する。これはオンデマンドのコンテキストに便利です。LLM が必要になったときにツールを呼び出してデータを取得できます。  
4. リトリーバルや Web 検索を利用する。これらはファイルやデータベースから関連データを取得する (リトリーバル) 、あるいは Web から取得する (Web 検索) 特殊なツールです。関連するコンテキストデータで応答を「グラウンディング」する際に有効です。