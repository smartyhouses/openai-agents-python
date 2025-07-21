---
search:
  exclude: true
---
# 結果

`Runner.run` メソッドを呼び出すと、返されるのは次のいずれかです。

-   [`RunResult`][agents.result.RunResult] — `run` または `run_sync` を呼び出した場合
-   [`RunResultStreaming`][agents.result.RunResultStreaming] — `run_streamed` を呼び出した場合

これらはいずれも [`RunResultBase`][agents.result.RunResultBase] を継承しており、ほとんどの有用な情報はここに含まれています。

## 最終出力

[`final_output`][agents.result.RunResultBase.final_output] プロパティには、最後に実行されたエージェントの最終出力が入ります。内容は次のいずれかです。

-   エージェントに `output_type` が定義されていない場合は `str`
-   エージェントに `output_type` が定義されている場合は `last_agent.output_type` 型のオブジェクト

!!! note

    `final_output` の型は `Any` です。ハンドオフが発生する可能性があるため静的型付けはできません。ハンドオフが起こると、どのエージェントが最後になるか分からないため、可能な出力型の集合を静的に特定できないからです。

## 次のターンへの入力

[`result.to_input_list()`][agents.result.RunResultBase.to_input_list] を使うと、元の入力に加えてエージェント実行中に生成されたアイテムを連結した input list を取得できます。これにより、あるエージェント実行の出力を別の実行に渡したり、ループで回して毎回新しい ユーザー 入力を追加したりするのが簡単になります。

## 最後のエージェント

[`last_agent`][agents.result.RunResultBase.last_agent] プロパティには、最後に実行されたエージェントが入ります。アプリケーションによっては、次に ユーザー が何か入力したときにこれが役立つことがよくあります。たとえば、最初に受付を行うエージェントが言語別のエージェントへハンドオフする場合、最後のエージェントを保持しておき、次回の ユーザー メッセージで再利用できます。

## 新しいアイテム

[`new_items`][agents.result.RunResultBase.new_items] プロパティには、実行中に生成された新しいアイテムが入ります。アイテムは [`RunItem`][agents.items.RunItem] でラップされています。RunItem は LLM が生成した raw アイテムを包んでいます。

-   [`MessageOutputItem`][agents.items.MessageOutputItem] は LLM からのメッセージを示します。raw アイテムは生成されたメッセージです。
-   [`HandoffCallItem`][agents.items.HandoffCallItem] は LLM がハンドオフツールを呼び出したことを示します。raw アイテムはツール呼び出しアイテムです。
-   [`HandoffOutputItem`][agents.items.HandoffOutputItem] はハンドオフが発生したことを示します。raw アイテムはハンドオフツール呼び出しに対するツール応答です。アイテムからソース／ターゲットのエージェントにもアクセスできます。
-   [`ToolCallItem`][agents.items.ToolCallItem] は LLM がツールを呼び出したことを示します。
-   [`ToolCallOutputItem`][agents.items.ToolCallOutputItem] はツールが呼び出されたことを示します。raw アイテムはツール応答です。アイテムからツール出力にもアクセスできます。
-   [`ReasoningItem`][agents.items.ReasoningItem] は LLM の reasoning アイテムを示します。raw アイテムは生成された reasoning です。

## その他の情報

### ガードレール結果

[`input_guardrail_results`][agents.result.RunResultBase.input_guardrail_results] と [`output_guardrail_results`][agents.result.RunResultBase.output_guardrail_results] プロパティには、ガードレールの結果が入ります（存在する場合）。ガードレール結果にはログや保存に役立つ情報が含まれることがあるため、こちらで取得できます。

### Raw 応答

[`raw_responses`][agents.result.RunResultBase.raw_responses] プロパティには、 LLM が生成した [`ModelResponse`][agents.items.ModelResponse] が入ります。

### 元の入力

[`input`][agents.result.RunResultBase.input] プロパティには、`run` メソッドに渡した元の入力が入ります。ほとんどの場合必要ありませんが、必要なときのために利用可能にしています。