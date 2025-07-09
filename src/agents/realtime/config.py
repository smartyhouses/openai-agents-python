from __future__ import annotations

from typing import (
    Literal,
    Union,
)

from typing_extensions import NotRequired, TypeAlias, TypedDict

from ..model_settings import ToolChoice
from ..tool import FunctionTool


class RealtimeClientMessage(TypedDict, total=False):
    type: str  # explicitly required
    # All additional keys are permitted because total=False


class UserInputText(TypedDict):
    type: Literal["input_text"]
    text: str


class RealtimeUserInputMessage(TypedDict):
    type: Literal["message"]
    role: Literal["user"]
    content: list[UserInputText]


RealtimeUserInput: TypeAlias = Union[str, RealtimeUserInputMessage]


RealtimeAudioFormat: TypeAlias = Union[Literal["pcm16", "g711_ulaw", "g711_alaw"], str]


class RealtimeInputAudioTranscriptionConfig(TypedDict, total=False):
    language: NotRequired[str]
    model: NotRequired[Literal["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"] | str]
    prompt: NotRequired[str]


class RealtimeTurnDetectionConfig(TypedDict, total=False):
    """Turn detection config. Allows extra vendor keys if needed."""

    type: NotRequired[Literal["semantic_vad", "server_vad"]]
    create_response: NotRequired[bool]
    eagerness: NotRequired[Literal["auto", "low", "medium", "high"]]
    interrupt_response: NotRequired[bool]
    prefix_padding_ms: NotRequired[int]
    silence_duration_ms: NotRequired[int]
    threshold: NotRequired[float]


class RealtimeSessionConfig(TypedDict):
    model: NotRequired[str]
    instructions: NotRequired[str]
    modalities: NotRequired[list[Literal["text", "audio"]]]
    voice: NotRequired[str]

    input_audio_format: NotRequired[RealtimeAudioFormat]
    output_audio_format: NotRequired[RealtimeAudioFormat]
    input_audio_transcription: NotRequired[RealtimeInputAudioTranscriptionConfig]
    turn_detection: NotRequired[RealtimeTurnDetectionConfig]

    tool_choice: NotRequired[ToolChoice]
    tools: NotRequired[list[FunctionTool]]

    # TODO (rm) Add tracing support
    # tracing: NotRequired[RealtimeTracingConfig | None]
