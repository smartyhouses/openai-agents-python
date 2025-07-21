---
search:
  exclude: true
---
# ガードレール

ガードレールは エージェント と _並列_ で動作し、ユーザー入力のチェックとバリデーションを行えます。たとえば、とても高性能 (そのぶん遅く / 高価) なモデルを使って顧客対応を行うエージェントがあるとします。悪意のある ユーザー がそのモデルに数学の宿題を解かせようとした場合、高価なモデルを無駄に動かしたくありません。そこで、低コスト / 高速なモデルを使ったガードレールを事前に実行し、悪用を検知したらただちにエラーを発生させることで、時間とコストを節約できます。

ガードレールには 2 種類あります:

1. 入力ガードレール: 最初のユーザー入力に対して実行されます  
2. 出力ガードレール: 最終的なエージェント出力に対して実行されます  

## 入力ガードレール

入力ガードレールは 3 ステップで動作します:

1. まず、ガードレールはエージェントに渡されたものと同じ入力を受け取ります。  
2. 次に、ガードレール関数が実行され [`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput] を生成し、それを [`InputGuardrailResult`][agents.guardrail.InputGuardrailResult] でラップします。  
3. 最後に [`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered] が true かどうかを確認します。true の場合、[`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered] 例外が発生し、適切に ユーザー へ応答するか例外を処理できます。  

!!! Note

    入力ガードレールはユーザー入力に対して実行されることを想定しているため、ガードレールは *最初* のエージェントの場合にのみ実行されます。「なぜ `guardrails` プロパティがエージェント側にあり、`Runner.run` に渡さないのか」と疑問に思うかもしれません。これはガードレールが実際のエージェントと密接に関連しているためです。エージェントごとに異なるガードレールを実行することが多く、コードを同じ場所に置いたほうが可読性が高まります。

## 出力ガードレール

出力ガードレールは 3 ステップで動作します:

1. まず、ガードレールはエージェントが生成した出力を受け取ります。  
2. 次に、ガードレール関数が実行され [`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput] を生成し、それを [`OutputGuardrailResult`][agents.guardrail.OutputGuardrailResult] でラップします。  
3. 最後に [`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered] が true かどうかを確認します。true の場合、[`OutputGuardrailTripwireTriggered`][agents.exceptions.OutputGuardrailTripwireTriggered] 例外が発生し、適切に ユーザー へ応答するか例外を処理できます。  

!!! Note

    出力ガードレールは最終的なエージェント出力に対して実行されることを想定しているため、ガードレールは *最後* のエージェントの場合にのみ実行されます。入力ガードレールと同様に、ガードレールはエージェントごとに異なることが多いため、コードを同じ場所に置いたほうが可読性が高まります。

## トリップワイヤー

入力または出力がガードレール検査に失敗した場合、ガードレールはトリップワイヤーでそれを通知できます。トリップワイヤーが発火したガードレールを検知した時点で、ただちに `{Input,Output}GuardrailTripwireTriggered` 例外を発生させ、エージェントの実行を停止します。

## ガードレールの実装

入力を受け取り、[`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput] を返す関数を用意する必要があります。この例では、そのために内部でエージェントを実行します。

```python
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent( # (1)!
    name="Guardrail check",
    instructions="Check if the user is asking you to do their math homework.",
    output_type=MathHomeworkOutput,
)


@input_guardrail
async def math_guardrail( # (2)!
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output, # (3)!
        tripwire_triggered=result.final_output.is_math_homework,
    )


agent = Agent(  # (4)!
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    input_guardrails=[math_guardrail],
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except InputGuardrailTripwireTriggered:
        print("Math homework guardrail tripped")
```

1. このエージェントをガードレール関数内で使用します。  
2. ここがガードレール関数で、エージェントの入力 / コンテキストを受け取り、結果を返します。  
3. ガードレール結果に追加情報を含めることもできます。  
4. ワークフローを定義する実際のエージェントです。  

出力ガードレールも同様です。

```python
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    output_guardrail,
)
class MessageOutput(BaseModel): # (1)!
    response: str

class MathOutput(BaseModel): # (2)!
    reasoning: str
    is_math: bool

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the output includes any math.",
    output_type=MathOutput,
)

@output_guardrail
async def math_guardrail(  # (3)!
    ctx: RunContextWrapper, agent: Agent, output: MessageOutput
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, output.response, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math,
    )

agent = Agent( # (4)!
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    output_guardrails=[math_guardrail],
    output_type=MessageOutput,
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except OutputGuardrailTripwireTriggered:
        print("Math output guardrail tripped")
```

1. これは実際のエージェントの出力型です。  
2. これはガードレールの出力型です。  
3. ここがガードレール関数で、エージェントの出力を受け取り、結果を返します。  
4. ワークフローを定義する実際のエージェントです。