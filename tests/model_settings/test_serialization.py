import json
from dataclasses import fields

from openai.types.shared import Reasoning

from agents.model_settings import ModelSettings


def verify_serialization(model_settings: ModelSettings) -> None:
    """Verify that ModelSettings can be serialized to a JSON string."""
    json_dict = model_settings.to_json_dict()
    json_string = json.dumps(json_dict)
    assert json_string is not None


def test_basic_serialization() -> None:
    """Tests whether ModelSettings can be serialized to a JSON string."""

    # First, lets create a ModelSettings instance
    model_settings = ModelSettings(
        temperature=0.5,
        top_p=0.9,
        max_tokens=100,
    )

    # Now, lets serialize the ModelSettings instance to a JSON string
    verify_serialization(model_settings)


def test_all_fields_serialization() -> None:
    """Tests whether ModelSettings can be serialized to a JSON string."""

    # First, lets create a ModelSettings instance
    model_settings = ModelSettings(
        temperature=0.5,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        tool_choice="auto",
        parallel_tool_calls=True,
        truncation="auto",
        max_tokens=100,
        reasoning=Reasoning(),
        metadata={"foo": "bar"},
        store=False,
        include_usage=False,
        extra_query={"foo": "bar"},
        extra_body={"foo": "bar"},
        extra_headers={"foo": "bar"},
        kwargs={"custom_param": "value", "another_param": 42},
    )

    # Verify that every single field is set to a non-None value
    for field in fields(model_settings):
        assert getattr(model_settings, field.name) is not None, (
            f"You must set the {field.name} field"
        )

    # Now, lets serialize the ModelSettings instance to a JSON string
    verify_serialization(model_settings)


def test_kwargs_serialization() -> None:
    """Test that kwargs are properly serialized."""
    model_settings = ModelSettings(
        temperature=0.5,
        kwargs={"custom_param": "value", "another_param": 42, "nested": {"key": "value"}},
    )

    json_dict = model_settings.to_json_dict()
    assert json_dict["kwargs"] == {
        "custom_param": "value",
        "another_param": 42,
        "nested": {"key": "value"},
    }

    # Verify serialization works
    verify_serialization(model_settings)


def test_kwargs_resolve() -> None:
    """Test that kwargs are properly merged in the resolve method."""
    base_settings = ModelSettings(
        temperature=0.5, kwargs={"param1": "base_value", "param2": "base_only"}
    )

    override_settings = ModelSettings(
        top_p=0.9, kwargs={"param1": "override_value", "param3": "override_only"}
    )

    resolved = base_settings.resolve(override_settings)

    # Check that regular fields are properly resolved
    assert resolved.temperature == 0.5  # from base
    assert resolved.top_p == 0.9  # from override

    # Check that kwargs are properly merged
    expected_kwargs = {
        "param1": "override_value",  # override wins
        "param2": "base_only",  # from base
        "param3": "override_only",  # from override
    }
    assert resolved.kwargs == expected_kwargs


def test_kwargs_resolve_with_none() -> None:
    """Test that resolve works properly when one side has None kwargs."""
    # Base with kwargs, override with None
    base_settings = ModelSettings(kwargs={"param1": "value1"})
    override_settings = ModelSettings(temperature=0.8)

    resolved = base_settings.resolve(override_settings)
    assert resolved.kwargs == {"param1": "value1"}
    assert resolved.temperature == 0.8

    # Base with None, override with kwargs
    base_settings = ModelSettings(temperature=0.5)
    override_settings = ModelSettings(kwargs={"param2": "value2"})

    resolved = base_settings.resolve(override_settings)
    assert resolved.kwargs == {"param2": "value2"}
    assert resolved.temperature == 0.5


def test_kwargs_resolve_both_none() -> None:
    """Test that resolve works when both sides have None kwargs."""
    base_settings = ModelSettings(temperature=0.5)
    override_settings = ModelSettings(top_p=0.9)

    resolved = base_settings.resolve(override_settings)
    assert resolved.kwargs is None
    assert resolved.temperature == 0.5
    assert resolved.top_p == 0.9
