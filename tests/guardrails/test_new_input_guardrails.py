from __future__ import annotations

from typing import Any

import pytest

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardailInputs,
    InputGuardrail,
    RunContextWrapper,
    TResponseInputItem,
)
from agents.guardrail import input_guardrail


def get_sync_guardrail(triggers: bool, output_info: Any | None = None):
    def sync_guardrail(context: RunContextWrapper[Any], inputs: InputGuardailInputs):
        assert inputs.agent is not None
        assert inputs.input is not None

        return GuardrailFunctionOutput(
            output_info=output_info,
            tripwire_triggered=triggers,
        )

    return sync_guardrail


@pytest.mark.asyncio
async def test_sync_input_guardrail():
    guardrail = InputGuardrail(guardrail_function=get_sync_guardrail(triggers=False))
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        context=RunContextWrapper(context=None),
        previous_response_id=None,
    )
    assert not result.output.tripwire_triggered
    assert result.output.output_info is None

    guardrail = InputGuardrail(guardrail_function=get_sync_guardrail(triggers=True))
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        context=RunContextWrapper(context=None),
        previous_response_id=None,
    )
    assert result.output.tripwire_triggered
    assert result.output.output_info is None

    guardrail = InputGuardrail(
        guardrail_function=get_sync_guardrail(triggers=True, output_info="test")
    )
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        context=RunContextWrapper(context=None),
        previous_response_id=None,
    )
    assert result.output.tripwire_triggered
    assert result.output.output_info == "test"


def get_async_input_guardrail(triggers: bool, output_info: Any | None = None):
    async def async_guardrail(context: RunContextWrapper[Any], inputs: InputGuardailInputs):
        assert inputs.agent is not None
        assert inputs.input is not None

        return GuardrailFunctionOutput(
            output_info=output_info,
            tripwire_triggered=triggers,
        )

    return async_guardrail


@pytest.mark.asyncio
async def test_async_input_guardrail():
    guardrail = InputGuardrail(guardrail_function=get_async_input_guardrail(triggers=False))
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        context=RunContextWrapper(context=None),
        previous_response_id=None,
    )
    assert not result.output.tripwire_triggered
    assert result.output.output_info is None

    guardrail = InputGuardrail(guardrail_function=get_async_input_guardrail(triggers=True))
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        context=RunContextWrapper(context=None),
        previous_response_id=None,
    )
    assert result.output.tripwire_triggered
    assert result.output.output_info is None

    guardrail = InputGuardrail(
        guardrail_function=get_async_input_guardrail(triggers=True, output_info="test")
    )
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        context=RunContextWrapper(context=None),
        previous_response_id=None,
    )
    assert result.output.tripwire_triggered
    assert result.output.output_info == "test"


@input_guardrail
def decorated_input_guardrail(
    context: RunContextWrapper[Any], inputs: InputGuardailInputs
) -> GuardrailFunctionOutput:
    assert inputs.agent is not None
    assert inputs.input is not None

    return GuardrailFunctionOutput(
        output_info="test_1",
        tripwire_triggered=False,
    )


@input_guardrail(name="Custom name")
def decorated_named_input_guardrail(
    context: RunContextWrapper[Any], agent: Agent[Any], input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    return GuardrailFunctionOutput(
        output_info="test_2",
        tripwire_triggered=False,
    )


@pytest.mark.asyncio
async def test_input_guardrail_decorators():
    guardrail = decorated_input_guardrail
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        previous_response_id=None,
        context=RunContextWrapper(context=None),
    )
    assert not result.output.tripwire_triggered
    assert result.output.output_info == "test_1"

    guardrail = decorated_named_input_guardrail
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        previous_response_id=None,
        context=RunContextWrapper(context=None),
    )
    assert not result.output.tripwire_triggered
    assert result.output.output_info == "test_2"
    assert guardrail.get_name() == "Custom name"


@input_guardrail
def guardrail_with_previous_response_id(
    context: RunContextWrapper[Any], inputs: InputGuardailInputs
) -> GuardrailFunctionOutput:
    assert inputs.agent is not None
    assert inputs.input is not None
    assert inputs.previous_response_id is not None
    return GuardrailFunctionOutput(
        output_info="test_3",
        tripwire_triggered=False,
    )


@pytest.mark.asyncio
async def test_guardrail_with_previous_response_id():
    guardrail = guardrail_with_previous_response_id
    result = await guardrail.run(
        agent=Agent(name="test"),
        input="test",
        previous_response_id="test",
        context=RunContextWrapper(context=None),
    )
    assert not result.output.tripwire_triggered
    assert result.output.output_info == "test_3"
