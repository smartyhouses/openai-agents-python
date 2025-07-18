---
search:
  exclude: true
---
# OpenAI Agents SDK

[OpenAI Agents SDK](https://github.com/openai/openai-agents-python) は、非常に少ない抽象化で軽量かつ使いやすいパッケージとして、エージェント指向の AI アプリを構築できるようにします。これは、以前のエージェント実験である [Swarm](https://github.com/openai/swarm/tree/main) の本番運用版アップグレードです。Agents SDK には、ごく少数の基本コンポーネントがあります。

-   **エージェント** 、instructions とツールを備えた LLM  
-   **ハンドオフ** 、特定のタスクを他のエージェントに委任する機能  
-   **ガードレール** 、エージェントへの入力を検証する仕組み  
-   **セッション** 、エージェント実行間で会話履歴を自動的に管理  

Python と組み合わせることで、これらの基本コンポーネントはツールとエージェント間の複雑な関係性を表現でき、急な学習コストなしに実際のアプリケーションを構築できます。さらに、SDK には組み込みの **トレーシング** があり、エージェントフローを可視化・デバッグし、評価やファインチューニングまで行えます。

## Agents SDK を使う理由

SDK には 2 つの設計原則があります。

1. 使う価値があるだけの機能を持ちながら、学習が速いようにプリミティブを最小限にする  
2. デフォルトで高い使い勝手を提供しつつ、動作を細部までカスタマイズできる  

主な機能は次のとおりです。

-   エージェントループ: ツール呼び出し、結果の LLM への送信、完了までのループを自動で処理  
-    Python ファースト: 新しい抽象を学ばずとも、言語機能だけでエージェントを編成・連携  
-   ハンドオフ: 複数エージェント間の協調と委任を実現する強力な機能  
-   ガードレール: エージェントと並行して入力検証を実行し、失敗時には早期終了  
-   セッション: エージェント実行間の会話履歴を自動管理し、手動の状態管理を排除  
-   関数ツール: 任意の Python 関数をツール化し、自動スキーマ生成と Pydantic ベースの検証を提供  
-   トレーシング: フローの可視化・デバッグ・モニタリングに加え、OpenAI の評価・ファインチューニング・蒸留ツールを使用可能  

## インストール

```bash
pip install openai-agents
```

## Hello World 例

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

(_実行する際は `OPENAI_API_KEY` 環境変数を設定してください_)

```bash
export OPENAI_API_KEY=sk-...
```