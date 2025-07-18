---
search:
  exclude: true
---
# 結果

`Runner.run` メソッドを呼び出すと、次のいずれかが返されます:

-   [`RunResult`][agents.result.RunResult] (`run` または `run_sync` を呼び出した場合)
-   [`RunResultStreaming`][agents.result.RunResultStreaming] (`run_streamed` を呼び出した場合)

どちらも [`RunResultBase`][agents.result.RunResultBase] を継承しており、ほとんどの有用な情報はここに含まれています。

## 最終出力

[`final_output`][agents.result.RunResultBase.final_output] プロパティには、最後に実行されたエージェントの最終出力が格納されます。内容は以下のいずれかです。

-   エージェントに `output_type` が定義されていない場合は `str`
-   エージェントに `output_type` が定義されている場合は `last_agent.output_type` 型のオブジェクト

!!! note
    `final_output` の型は `Any` です。ハンドオフが発生する可能性があるため静的型付けはできません。ハンドオフが起こると、どのエージェントが最後になるか事前には分からず、したがって出力型の集合を静的に決定できないためです。

## 次ターンへの入力

[`result.to_input_list()`][agents.result.RunResultBase.to_input_list] を使用すると、実行時に生成されたアイテムを元の入力に連結した入力リストへ変換できます。これにより、一度のエージェント実行結果を別の実行へ渡したり、ループで実行して毎回新しいユーザー入力を追加したりすることが容易になります。

## 最後のエージェント

[`last_agent`][agents.result.RunResultBase.last_agent] プロパティには、最後に実行されたエージェントが格納されています。アプリケーションによっては、ユーザーが次回入力する際にこれを利用すると便利です。たとえば、一次受付エージェントが言語特化エージェントへハンドオフする場合、`last_agent` を保存しておけば、ユーザーが次にメッセージを送った際に再利用できます。

## 新規アイテム

[`new_items`][agents.result.RunResultBase.new_items] プロパティには、実行中に生成された新しいアイテムが格納されます。アイテムは [`RunItem`][agents.items.RunItem] でラップされており、 raw アイテムを保持します。

-   [`MessageOutputItem`][agents.items.MessageOutputItem]:  LLM からのメッセージ。 raw アイテムは生成されたメッセージです。
-   [`HandoffCallItem`][agents.items.HandoffCallItem]:  LLM がハンドオフツールを呼び出したことを示します。 raw アイテムはツール呼び出しです。
-   [`HandoffOutputItem`][agents.items.HandoffOutputItem]:  ハンドオフが発生したことを示します。 raw アイテムはハンドオフツール呼び出しへのツールレスポンスです。ソース／ターゲットエージェントにもアクセスできます。
-   [`ToolCallItem`][agents.items.ToolCallItem]:  LLM がツールを呼び出したことを示します。
-   [`ToolCallOutputItem`][agents.items.ToolCallOutputItem]:  ツールが呼び出されたことを示します。 raw アイテムはツールレスポンスです。ツール出力にもアクセスできます。
-   [`ReasoningItem`][agents.items.ReasoningItem]:  LLM からの推論アイテム。 raw アイテムは生成された推論です。

## その他の情報

### ガードレール結果

[`input_guardrail_results`][agents.result.RunResultBase.input_guardrail_results] と [`output_guardrail_results`][agents.result.RunResultBase.output_guardrail_results] プロパティには、ガードレールの実行結果が格納されます。ガードレール結果にはログや保存したい有用な情報が含まれることがあるため、これらを公開しています。

### raw 応答

[`raw_responses`][agents.result.RunResultBase.raw_responses] プロパティには、 LLM によって生成された [`ModelResponse`][agents.items.ModelResponse] が格納されます。

### 元の入力

[`input`][agents.result.RunResultBase.input] プロパティには、`run` メソッドに渡した元の入力が格納されています。通常は不要ですが、必要に応じて参照できます。