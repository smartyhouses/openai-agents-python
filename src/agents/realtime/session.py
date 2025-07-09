"""Minimal realtime session implementation for voice agents."""

from __future__ import annotations

import abc
import asyncio
from collections.abc import Awaitable
from typing import Any, Callable, Literal

from typing_extensions import TypeAlias

from agents.realtime.events import RealtimeSessionEvent

from ..run import RunContextWrapper
from ..tool import Tool
from .agent import RealtimeAgent
from .config import RealtimeSessionConfig
from .items import RealtimeItem
from .transport import (
    APIKeyOrKeyFunc,
    OpenAIRealtimeWebSocketTransport,
    RealtimeModelName,
    RealtimeSessionTransport,
)


class RealtimeSessionListener(abc.ABC):
    """A listener for realtime session events."""

    @abc.abstractmethod
    async def on_event(self, event: RealtimeSessionEvent) -> None:
        """Called when an event is emitted by the realtime session."""
        pass


RealtimeSessionListenerFunc: TypeAlias = Callable[[RealtimeSessionEvent], Awaitable[None]]
"""A function that can be used as a listener for realtime session events."""


class _RealtimeFuncListener(RealtimeSessionListener):
    """A listener that wraps a function."""

    def __init__(self, func: RealtimeSessionListenerFunc) -> None:
        self._func = func

    async def on_event(self, event: RealtimeSessionEvent) -> None:
        """Call the wrapped function with the event."""
        await self._func(event)


class RealtimeSession:
    """A `RealtimeSession` is the equivalent of `Runner` for realtime agents. It automatically
    handles multiple turns by maintaining a persistent connection with the underlying transport
    layer.

    The session manages the local history copy, executes tools, runs guardrails and facilitates
    handoffs between agents.

    Since this code runs on your server, it uses WebSockets by default. You can optionally create
    your own custom transport layer by implementing the `RealtimeSessionTransport` interface.
    """

    def __init__(
        self,
        starting_agent: RealtimeAgent,
        *,
        context: Any | None = None,
        transport: Literal["websocket"] | RealtimeSessionTransport = "websocket",
        api_key: APIKeyOrKeyFunc | None = None,
        model: RealtimeModelName | None = None,
        config: RealtimeSessionConfig | None = None,
        # TODO (rm) Add guardrail support
        # TODO (rm) Add tracing support
        # TODO (rm) Add history audio story config
    ) -> None:
        """Initialize the realtime session.

        Args:
            starting_agent: The agent to start the session with.
            context: The context to use for the session.
            transport: The transport to use for the session. Defaults to using websockets.
            api_key: The API key to use for the session.
            model: The model to use. Must be a realtime model.
            config: Override parameters to use.
        """
        self._current_agent = starting_agent
        self._context_wrapper = RunContextWrapper(context)
        self._override_config = config
        self._history: list[RealtimeItem] = []

        if transport == "websocket":
            self._transport = OpenAIRealtimeWebSocketTransport()
        else:
            self._transport = transport

        self._current_tools: list[Tool] = []
        self._listeners: list[RealtimeSessionListener] = []

    async def __aenter__(self) -> RealtimeSession:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.end()

    async def start(self) -> None:
        """Start the session: connect to the model and start the connection."""
        config = await self.create_session_config(
            overrides=self._override_config,
        )

        await self._transport.connect(config)

    async def end(self) -> None:
        """End the session: disconnect from the model and close the connection."""
        pass

    async def add_listener(
        self, listener: RealtimeSessionListener | RealtimeSessionListenerFunc
    ) -> None:
        """Add a listener to the session."""
        if isinstance(listener, RealtimeSessionListener):
            self._listeners.append(listener)
        else:
            self._listeners.append(_RealtimeFuncListener(listener))

    async def remove_listener(
        self, listener: RealtimeSessionListener | RealtimeSessionListenerFunc
    ) -> None:
        """Remove a listener from the session."""
        if isinstance(listener, RealtimeSessionListener):
            self._listeners.remove(listener)
        else:
            for x in self._listeners:
                if isinstance(x, _RealtimeFuncListener) and x._func == listener:
                    self._listeners.remove(x)
                    break

    async def create_session_config(
        self, overrides: RealtimeSessionConfig | None = None
    ) -> RealtimeSessionConfig:
        """Create the session config."""
        agent = self._current_agent
        instructions, tools = await asyncio.gather(
            agent.get_system_prompt(self._context_wrapper),
            agent.get_all_tools(self._context_wrapper),
        )
        config = RealtimeSessionConfig(
            model=self._model,
            instructions=instructions,
            tools=tools,
        )

        if overrides:
            config.update(overrides)

        return config


# class RealtimeSessionConfig(TypedDict):
#     """Configuration for realtime session."""

#     instructions: NotRequired[str]
#     model: NotRequired[str]
#     voice: NotRequired[str]
#     modalities: NotRequired[list[str]]
#     input_audio_format: NotRequired[str]
#     output_audio_format: NotRequired[str]
#     input_audio_transcription: NotRequired[dict[str, Any]]
#     turn_detection: NotRequired[dict[str, Any]]
#     tool_choice: NotRequired[str]
#     tools: NotRequired[list[dict[str, Any]]]


# class RealtimeSessionOptions(TypedDict, Generic[TContext]):
#     """Options for creating a realtime session."""

#     api_key: str | Callable[[], MaybeAwaitable[str]]
#     transport: NotRequired[str]
#     model: NotRequired[str]
#     context: NotRequired[TContext]
#     config: NotRequired[RealtimeSessionConfig]
#     history_store_audio: NotRequired[bool]
#     tracing_disabled: NotRequired[bool]
#     group_id: NotRequired[str]
#     trace_metadata: NotRequired[dict[str, Any]]
#     workflow_name: NotRequired[str]


# class RealtimeConnectOptions(TypedDict):
#     """Options for connecting to realtime API."""

#     api_key: str | Callable[[], str | MaybeAwaitable[str]]
#     model: NotRequired[str]
#     url: NotRequired[str]


# class RealtimeItem(TypedDict):
#     """A realtime conversation item."""

#     item_id: str
#     type: str
#     role: NotRequired[str]
#     content: NotRequired[list[dict[str, Any]]]
#     status: NotRequired[str]


# class RealtimeContextData(TypedDict, Generic[TContext]):
#     """Context data for realtime session."""

#     history: list[RealtimeItem]


# class RealtimeSession(Generic[TContext]):
#     """
#     A minimal realtime session for building voice agents.

#     This is a simplified Python implementation inspired by the JavaScript version,
#     focusing on core functionality without tracing, guardrails, or hooks.
#     """

#     def __init__(
#         self,
#         initial_agent: RealtimeAgent[TContext] | RealtimeAgent[RealtimeContextData[TContext]],
#         options: RealtimeSessionOptions[TContext] | None = None,
#     ) -> None:
#         """Initialize the realtime session."""
#         self._initial_agent = initial_agent
#         self._options = options or cast(RealtimeSessionOptions[TContext], {})
#         self._current_agent = initial_agent
#         self._history: list[RealtimeItem] = []
#         self._connected = False
#         self._status = "disconnected"

#         # Validate required options
#         if "api_key" not in self._options:
#             raise ValueError("api_key is required in options")

#     @property
#     def status(self) -> str:
#         """Get the current connection status."""
#         return self._status

#     @property
#     def history(self) -> list[RealtimeItem]:
#         """Get the current conversation history."""
#         return self._history.copy()

#     @property
#     def current_agent(
#         self,
#     ) -> RealtimeAgent[TContext] | RealtimeAgent[RealtimeContextData[TContext]]:
#         """Get the current active agent."""
#         return self._current_agent

#     async def connect(self, options: RealtimeConnectOptions | None = None) -> None:
#         """
#         Connect to the realtime API.

#         Args:
#             options: Connection options. If not provided, uses session options.
#         """
#         if self._connected:
#             logger.warning("Session is already connected")
#             return

#         connect_opts: RealtimeConnectOptions = options or cast(RealtimeConnectOptions, {})
#         api_key = connect_opts.get("api_key") or self._options.get("api_key")

#         if not api_key:
#             raise ValueError("api_key is required for connection")

#         # Resolve API key if it's a function
#         if callable(api_key):
#             resolved_key = api_key()
#             if hasattr(resolved_key, "__await__"):
#                 resolved_key = await resolved_key
#             api_key = resolved_key

#         self._status = "connecting"

#         try:
#             # In a full implementation, this would establish the actual connection
#             # For now, we'll simulate a successful connection
#             await asyncio.sleep(0.1)  # Simulate connection delay

#             self._connected = True
#             self._status = "connected"
#             logger.info("Realtime session connected successfully")

#         except Exception as e:
#             self._status = "disconnected"
#             logger.error(f"Failed to connect to realtime API: {e}")
#             raise

#     async def disconnect(self) -> None:
#         """Disconnect from the realtime API."""
#         if not self._connected:
#             return

#         self._status = "disconnecting"

#         try:
#             # In a full implementation, this would close the actual connection
#             await asyncio.sleep(0.1)  # Simulate disconnection delay

#             self._connected = False
#             self._status = "disconnected"
#             logger.info("Realtime session disconnected")

#         except Exception as e:
#             logger.error(f"Error during disconnect: {e}")
#             self._status = "disconnected"

#     async def send_message(self, message: str, **_kwargs: Any) -> None:
#         """
#         Send a text message to the realtime API.

#         Args:
#             message: The text message to send
#             **kwargs: Additional message options
#         """
#         if not self._connected:
#             raise RuntimeError("Session is not connected")

#         # Create a message item
#         item: RealtimeItem = {
#             "item_id": f"msg_{len(self._history)}",
#             "type": "message",
#             "role": "user",
#             "content": [{"type": "input_text", "text": message}],
#             "status": "completed",
#         }

#         # Add to history
#         self._history.append(item)

#         logger.debug(f"Sent message: {message}")

#         # In a full implementation, this would send to the actual API
#         # and handle the response

#     async def send_audio(self, audio_data: bytes, commit: bool = False) -> None:
#         """
#         Send audio data to the realtime API.

#         Args:
#             audio_data: The audio data to send
#             commit: Whether to commit the audio and trigger processing
#         """
#         if not self._connected:
#             raise RuntimeError("Session is not connected")

#         logger.debug(f"Sent audio data: {len(audio_data)} bytes, commit={commit}")

#         # In a full implementation, this would send audio to the actual API

#     async def handoff_to_agent(self, agent: RealtimeAgent[TContext]) -> None:
#         """
#         Hand off the conversation to a different agent.

#         Args:
#             agent: The agent to hand off to
#         """
#         if not self._connected:
#             raise RuntimeError("Session is not connected")

#         old_agent = self._current_agent
#         self._current_agent = agent

#         logger.info(f"Handed off from {old_agent.name} to {agent.name}")

#         # In a full implementation, this would update the session configuration
#         # with the new agent's instructions and tools

#     async def get_tools(self) -> list[Tool]:
#         """Get all available tools for the current agent."""
#         if hasattr(self._current_agent, "get_all_tools"):
#             # Create a minimal run context
#             context_data = cast(RealtimeContextData[TContext], {"history": self._history})
#             run_context = RunContextWrapper(context_data)
#             return await self._current_agent.get_all_tools(run_context)
#         return []

#     async def interrupt(self) -> None:
#         """Interrupt the current response."""
#         if not self._connected:
#             return

#         logger.debug("Interrupting current response")

#         # In a full implementation, this would send an interrupt signal

#     def update_session_config(self, config: RealtimeSessionConfig) -> None:
#         """
#         Update the session configuration.

#         Args:
#             config: The new configuration options
#         """
#         if not self._connected:
#             raise RuntimeError("Session is not connected")

#         logger.debug(f"Updating session config: {config}")

#         # In a full implementation, this would send the config to the API

#     def mute(self, muted: bool) -> None:
#         """
#         Mute or unmute the input audio.

#         Args:
#             muted: Whether to mute the input
#         """
#         if not self._connected:
#             return

#         logger.debug(f"Setting mute to: {muted}")

#         # In a full implementation, this would control the audio input

#     async def __aenter__(self) -> RealtimeSession[TContext]:
#         """Async context manager entry."""
#         await self.connect()
#         return self

#     async def __aexit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
#         """Async context manager exit."""
#         await self.disconnect()
