from dataclasses import dataclass
from typing import Literal, Union

from typing_extensions import TypeAlias

from ..run import RunContextWrapper
from ..tool import Tool
from .agent import RealtimeAgent
from .items import RealtimeItem
from .transport_events import RealtimeTransportAudioEvent, RealtimeTransportEvent


@dataclass
class RealtimeEventInfo:
    context: RunContextWrapper
    """The context for the event."""


@dataclass
class RealtimeAgentStartEvent:
    """A new agent has started."""

    type: Literal["agent_start"] = "agent_start"

    agent: RealtimeAgent
    """The new agent."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeAgentEndEvent:
    """An agent has ended."""

    type: Literal["agent_end"] = "agent_end"

    agent: RealtimeAgent
    """The agent that ended."""

    output: str
    """The output of the agent."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeHandoffEvent:
    """An agent has handed off to another agent."""

    type: Literal["handoff"] = "handoff"

    from_agent: RealtimeAgent
    """The agent that handed off."""

    to_agent: RealtimeAgent
    """The agent that was handed off to."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeToolStart:
    """An agent is starting a tool call."""

    type: Literal["tool_start"] = "tool_start"

    agent: RealtimeAgent
    """The agent that updated."""

    tool: Tool

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeToolEnd:
    """An agent has ended a tool call."""

    type: Literal["tool_end"] = "tool_end"

    agent: RealtimeAgent
    """The agent that ended the tool call."""

    tool: Tool
    """The tool that was called."""

    output: str
    """The output of the tool call."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeRawTransportEvent:
    """Forwards raw events from the transport layer."""

    type: Literal["raw_transport_event"] = "raw_transport_event"

    data: RealtimeTransportEvent
    """The raw data from the transport layer."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeAudioStart:
    """Triggered when the agent starts generating audio."""

    type: Literal["audio_start"] = "audio_start"

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeAudioEnd:
    """Triggered when the agent stops generating audio."""

    type: Literal["audio_end"] = "audio_end"

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeAudio:
    """Triggered when the agent generates new audio to be played."""

    type: Literal["audio"] = "audio"

    audio: RealtimeTransportAudioEvent
    """The audio event from the transport layer."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeAudioInterrupted:
    """Triggered when the agent is interrupted. Can be listened to by the user to stop audio playback
    or give visual indicators to the user.
    """

    type: Literal["audio_interrupted"] = "audio_interrupted"

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeError:
    """An error has occurred."""

    type: Literal["error"] = "error"

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeHistoryUpdated:
    """The history has been updated. Contains the full history of the session."""

    type: Literal["history_updated"] = "history_updated"

    history: list[RealtimeItem]
    """The full history of the session."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


@dataclass
class RealtimeHistoryAdded:
    """A new item has been added to the history."""

    type: Literal["history_added"] = "history_added"

    item: RealtimeItem
    """The new item that was added to the history."""

    info: RealtimeEventInfo
    """Common info for all events, such as the context."""


# TODO (rm) Add guardrails

RealtimeSessionEvent: TypeAlias = Union[
    RealtimeAgentStartEvent,
    RealtimeAgentEndEvent,
    RealtimeHandoffEvent,
    RealtimeToolStart,
    RealtimeToolEnd,
    RealtimeRawTransportEvent,
    RealtimeAudioStart,
    RealtimeAudioEnd,
    RealtimeAudio,
    RealtimeAudioInterrupted,
    RealtimeError,
    RealtimeHistoryUpdated,
    RealtimeHistoryAdded,
]
"""An event emitted by the realtime session."""
