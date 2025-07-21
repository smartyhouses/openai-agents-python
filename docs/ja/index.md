---
search:
  exclude: true
---
# OpenAI Agents SDK

[OpenAI Agents SDK](https://github.com/openai/openai-agents-python) は、ごく少ない抽象化で軽量かつ使いやすいパッケージとして、エージェント指向の AI アプリを構築できる SDK です。これは、以前のエージェント向け実験プロジェクト [Swarm](https://github.com/openai/swarm/tree/main) を、プロダクションレベルにアップグレードしたものです。Agents SDK には、ごく少数の basic components（プリミティブ）が含まれています:

- **Agents**: instructions と tools を備えた LLM
- **Handoffs**: 特定のタスクを別のエージェントへ委任する仕組み
- **Guardrails**: エージェントへの入力を検証する仕組み
- **Sessions**: エージェント実行間で会話履歴を自動的に保持

 Python と組み合わせることで、これらのプリミティブは tools とエージェント間の複雑な関係を十分に表現でき、急な学習曲線なしで実世界のアプリケーションを構築できます。さらに、SDK には **tracing** が組み込まれており、エージェントフローを可視化・デバッグできるほか、評価やモデルのファインチューニングにも利用できます。

## Agents SDK を使用する理由

SDK には次の 2 つの設計原則があります。

1. 利用する価値があるだけの機能を備えつつ、プリミティブを最小限に抑え、学習を迅速にする。  
2. デフォルトで十分に機能するが、動作を細かくカスタマイズできる。

SDK の主な機能は次のとおりです。

- Agent ループ: tools の呼び出し、結果を LLM へ送信、LLM が完了するまでループする処理を内蔵。  
- Python ファースト: 新しい抽象概念を学ぶことなく、組み込みの言語機能でエージェントをオーケストレーション・連鎖。  
- Handoffs: 複数のエージェント間で調整・委任を行う強力な機能。  
- Guardrails: エージェントと並行して入力検証を実行し、チェック失敗時には早期に処理を中断。  
- Sessions: エージェント実行間の会話履歴を自動管理し、手動での状態管理を排除。  
- Function tools: 任意の Python 関数を tool に変換し、スキーマを自動生成。Pydantic によるバリデーションもサポート。  
- Tracing: ワークフローを可視化・デバッグ・モニタリングできる tracing を内蔵し、OpenAI の評価・ファインチューニング・蒸留ツールも利用可能。

## Installation

```bash
pip install openai-agents
```

## Hello world example

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

(_実行する場合は、`OPENAI_API_KEY` 環境変数を設定してください_)

```bash
export OPENAI_API_KEY=sk-...
```