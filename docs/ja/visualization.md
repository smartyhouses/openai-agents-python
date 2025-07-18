---
search:
  exclude: true
---
# エージェントの可視化

エージェントの可視化を使用すると、 **Graphviz** を用いてエージェントとその関係を構造化されたグラフィカル表示で生成できます。これにより、アプリケーション内でエージェント、ツール、ハンドオフがどのように相互作用するかを理解しやすくなります。

## インストール

オプションの `viz` 依存グループをインストールします:

```bash
pip install "openai-agents[viz]"
```

## グラフの生成

`draw_graph` 関数を使用してエージェントの可視化を生成できます。この関数は有向グラフを作成し、以下のように表示します:

- **エージェント** は黄色のボックスで表されます。
- **ツール** は緑色の楕円で表されます。
- **ハンドオフ** は一方のエージェントから別のエージェントへの有向エッジです。

### 使用例

```python
from agents import Agent, function_tool
from agents.extensions.visualization import draw_graph

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
    tools=[get_weather],
)

draw_graph(triage_agent)
```

![Agent Graph](../assets/images/graph.png)

これにより、 **triage エージェント** の構造とサブエージェントおよびツールへの接続を視覚的に表したグラフが生成されます。

## 可視化の理解

生成されたグラフには次の要素が含まれます:

- エントリーポイントを示す **開始ノード** (`__start__`)
- 黄色で塗りつぶされた長方形として表されるエージェント
- 緑で塗りつぶされた楕円として表されるツール
- 相互作用を示す有向エッジ
  - エージェント間のハンドオフには **実線の矢印**
  - ツール呼び出しには **点線の矢印**
- 実行が終了する場所を示す **終了ノード** (`__end__`)

## グラフのカスタマイズ

### グラフの表示
デフォルトでは、 `draw_graph` はグラフをインラインで表示します。別ウィンドウでグラフを表示するには、次のように記述します:

```python
draw_graph(triage_agent).view()
```

### グラフの保存
デフォルトでは、 `draw_graph` はグラフをインラインで表示します。ファイルとして保存するには、ファイル名を指定します:

```python
draw_graph(triage_agent, filename="agent_graph")
```

これにより、作業ディレクトリに `agent_graph.png` が生成されます。