import abc
from typing import Any, Callable, Literal, TypedDict, Union

from typing_extensions import TypeAlias

from ..util._types import MaybeAwaitable
from .config import RealtimeClientMessage, RealtimeSessionConfig, RealtimeUserInput
from .items import RealtimeItem
from .transport_events import TransportToolCallEvent

APIKeyOrKeyFunc = str | Callable[[], MaybeAwaitable[str]]
"""Either an API key or a function that returns an API key."""

RealtimeModelName: TypeAlias = Union[
    Literal[
        "gpt-4o-realtime-preview",
        "gpt-4o-mini-realtime-preview",
        "gpt-4o-realtime-preview-2025-06-03",
        "gpt-4o-realtime-preview-2024-12-17",
        "gpt-4o-realtime-preview-2024-10-01",
        "gpt-4o-mini-realtime-preview-2024-12-17",
    ],
    str,
]
"""The name of a realtime model."""


class RealtimeTransportConnectionOptions(TypedDict):
    """Options for connecting to a realtime transport."""

    api_key: APIKeyOrKeyFunc | None = None
    """The API key to use for the transport. If unset, the transport will attempt to use the
    `OPENAI_API_KEY` environment variable.
    """

    model: str | None = None
    """The model to use."""

    url: str | None = None
    """The URL to use for the transport. If unset, the transport will use the default OpenAI
    WebSocket URL.
    """

    initial_session_config: RealtimeSessionConfig | None = None


class RealtimeSessionTransport(abc.ABC):
    """A transport layer for realtime sessions."""

    @abc.abstractmethod
    async def connect(self, options: RealtimeTransportConnectionOptions) -> None:
        """Establish a connection to the model and keep it alive."""
        pass

    @abc.abstractmethod
    async def send_event(self, event: RealtimeClientMessage) -> None:
        """Send an event to the model."""
        pass

    @abc.abstractmethod
    async def send_message(
        self, message: RealtimeUserInput, other_event_data: dict[str, Any] | None = None
    ) -> None:
        """Send a message to the model."""
        pass

    @abc.abstractmethod
    async def send_audio(self, audio: bytes, *, commit: bool = False) -> None:
        """Send a raw audio chunk to the model.

        Args:
            audio: The audio data to send.
            commit: Whether to commit the audio buffer to the model.  If the model does not do turn
            detection, this can be used to indicate the turn is completed.
        """
        pass

    @abc.abstractmethod
    async def send_tool_output(
        self, tool_call: TransportToolCallEvent, output: str, start_response: bool
    ) -> None:
        """Send tool output to the model."""
        pass

    @abc.abstractmethod
    async def update_session_config(self, config: RealtimeSessionConfig) -> None:
        """Update the session config."""
        pass

    @abc.abstractmethod
    async def interrupt(self) -> None:
        """Interrupt the model. For example, could be triggered by a guardrail."""
        pass

    @abc.abstractmethod
    async def reset_history(
        self, old_history: list[RealtimeItem], new_history: list[RealtimeItem]
    ) -> None:
        """Reset the history of the session."""
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the session."""
        pass


class OpenAIRealtimeWebSocketTransport(RealtimeSessionTransport):
    """A transport layer for realtime sessions that uses OpenAI's WebSocket API."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def connect(self, options: RealtimeTransportConnectionOptions) -> None:
        """Establish a connection to the model and keep it alive."""
        pass

    async def send_event(self, event: RealtimeClientMessage) -> None:
        """Send an event to the model."""
        pass

    async def send_message(
        self, message: RealtimeUserInput, other_event_data: dict[str, Any] | None = None
    ) -> None:
        """Send a message to the model."""
        pass

    async def send_audio(self, audio: bytes, *, commit: bool = False) -> None:
        """Send a raw audio chunk to the model.

        Args:
            audio: The audio data to send.
            commit: Whether to commit the audio buffer to the model.  If the model does not do turn
            detection, this can be used to indicate the turn is completed.
        """
        pass

    async def update_session_config(self, config: RealtimeSessionConfig) -> None:
        """Update the session config."""
        pass

    async def close(self) -> None:
        """Close the session."""
        pass
