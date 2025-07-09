from __future__ import annotations

from typing import Any, Literal, TypeAlias, Union

from typing_extensions import NotRequired, TypedDict


class RealtimeTransportError(TypedDict):
    """Represents a transport‑layer error."""

    type: Literal["error"]
    error: Any


class RealtimeTransportToolCallEvent(TypedDict):
    """Model attempted a tool/function call."""

    type: Literal["function_call"]
    name: str
    call_id: str
    arguments: str

    id: NotRequired[str]
    previous_item_id: NotRequired[str]


class RealtimeTransportAudioEvent(TypedDict):
    """Raw audio bytes emitted by the model."""

    type: Literal["audio"]
    data: bytes
    response_id: str


class RealtimeTransportAudioTranscriptionCompletedEvent(TypedDict):
    """Finalised user‑audio transcript."""

    type: Literal["conversation.item.input_audio_transcription.completed"]
    item_id: str
    transcript: str


class RealtimeTransportTranscriptDelta(TypedDict):
    """Partial transcript update."""

    type: Literal["transcript_delta"]
    item_id: str
    delta: str
    response_id: str


RealtimeTransportLayerResponseCompleted: TypeAlias = protocol.StreamEventResponseCompleted
RealtimeTransportLayerResponseStarted: TypeAlias = protocol.StreamEventResponseStarted

RealtimeConnectionStatus: TypeAlias = Literal["connecting", "connected", "disconnected"]

RealtimeTransportEvent: TypeAlias = Union[
    RealtimeTransportError,
    RealtimeTransportToolCallEvent,
    RealtimeTransportAudioTranscriptionCompletedEvent,
    dict[str, Any],  # fallback for other event payloads
]
