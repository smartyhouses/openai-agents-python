---
search:
  exclude: true
---
# ハンドオフ

ハンドオフを使用すると、あるエージェントがタスクを別のエージェントへ委任できます。これは、異なるエージェントがそれぞれ得意分野を持つシナリオで特に有用です。たとえばカスタマーサポート アプリでは、注文状況、返金、FAQ などをそれぞれ担当するエージェントが存在する場合があります。

ハンドオフは、 LLM にとってツールとして表現されます。たとえば `Refund Agent` というエージェントへハンドオフする場合、そのツール名は `transfer_to_refund_agent` になります。

## ハンドオフの作成

すべてのエージェントには [`handoffs`][agents.agent.Agent.handoffs] というパラメーターがあり、 `Agent` を直接渡すことも、ハンドオフをカスタマイズする ` Handoff ` オブジェクトを渡すこともできます。

Agents SDK が提供する [`handoff()`][agents.handoffs.handoff] 関数を使用してハンドオフを作成できます。この関数では、ハンドオフ先のエージェントに加え、オーバーライドや入力フィルターをオプションで指定できます。

### 基本的な使い方

以下はシンプルなハンドオフの例です。

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

# (1)!
triage_agent = Agent(name="Triage agent", handoffs=[billing_agent, handoff(refund_agent)])
```

1. `billing_agent` のようにエージェントを直接指定するか、 `handoff()` 関数を使用できます。

### `handoff()` 関数によるハンドオフのカスタマイズ

[`handoff()`][agents.handoffs.handoff] 関数では、次の項目をカスタマイズできます。

- `agent` : ハンドオフ先のエージェントです。  
- `tool_name_override` : 既定では ` Handoff.default_tool_name()` が使用され、 `transfer_to_<agent_name>` に解決されます。これを上書きできます。  
- `tool_description_override` : ` Handoff.default_tool_description()` による既定のツール説明を上書きします。  
- `on_handoff` : ハンドオフが呼び出されたときに実行されるコールバック関数です。ハンドオフが発生した時点でデータ取得を開始するなどの用途に便利です。この関数はエージェント コンテキストを受け取り、オプションで LLM が生成した入力も受け取れます。入力データは `input_type` パラメーターで制御されます。  
- `input_type` : ハンドオフが想定する入力の型（オプション）です。  
- `input_filter` : 次のエージェントが受け取る入力をフィルタリングできます。詳細は後述します。  

```python
from agents import Agent, handoff, RunContextWrapper

def on_handoff(ctx: RunContextWrapper[None]):
    print("Handoff called")

agent = Agent(name="My agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    tool_name_override="custom_handoff_tool",
    tool_description_override="Custom description",
)
```

## ハンドオフ入力

状況によっては、 LLM にハンドオフを呼び出す際にデータを渡してほしい場合があります。たとえば「エスカレーション エージェント」へハンドオフする場合、理由を渡してログに残せるようにしたいかもしれません。

```python
from pydantic import BaseModel

from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalation agent called with reason: {input_data.reason}")

agent = Agent(name="Escalation agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    input_type=EscalationData,
)
```

## 入力フィルター

ハンドオフが発生すると、新しいエージェントが会話を引き継ぎ、これまでの会話履歴全体を閲覧できます。これを変更したい場合は、 [`input_filter`][agents.handoffs.Handoff.input_filter] を設定できます。入力フィルターは [` HandoffInputData`][agents.handoffs.HandoffInputData] を受け取り、新しい ` HandoffInputData` を返す関数です。

よくあるパターン（たとえば履歴からすべてのツール呼び出しを削除するなど）は [`agents.extensions.handoff_filters`][] に実装されています。

```python
from agents import Agent, handoff
from agents.extensions import handoff_filters

agent = Agent(name="FAQ agent")

handoff_obj = handoff(
    agent=agent,
    input_filter=handoff_filters.remove_all_tools, # (1)!
)
```

1. これにより、 `FAQ agent` が呼び出されたときに履歴からすべてのツールが自動的に削除されます。

## 推奨プロンプト

 LLM がハンドオフを正しく理解できるよう、エージェントにハンドオフに関する情報を含めることを推奨します。 [`agents.extensions.handoff_prompt.RECOMMENDED_PROMPT_PREFIX`][] に提案するプレフィックスが用意されているほか、 [`agents.extensions.handoff_prompt.prompt_with_handoff_instructions`][] を呼び出して、推奨されるデータを自動的にプロンプトへ追加することもできます。

```python
from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

billing_agent = Agent(
    name="Billing agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    <Fill in the rest of your prompt here>.""",
)
```