"""Minimal realtime session implementation for voice agents."""

from __future__ import annotations

import asyncio
from typing import Literal

from agents.realtime.connection import RealtimeSession
from agents.realtime.openai_realtime import OpenAIRealtimeWebSocketModel

from ..run_context import RunContextWrapper, TContext
from .agent import RealtimeAgent
from .config import (
    RealtimeModelName,
    RealtimeRunConfig,
    RealtimeSessionModelSettings,
)
from .events import (
    RealtimeEventInfo,
    RealtimeHandoffEvent,  # noqa: F401
)
from .items import RealtimeItem
from .model import (
    RealtimeModel,
    RealtimeModelConfig,
)


class RealtimeRunner:
    """A `RealtimeRunner` is the equivalent of `Runner` for realtime agents. It automatically
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
        context: TContext | None = None,
        transport: Literal["websocket"] | RealtimeModel = "websocket",
        model: RealtimeModelName | None = None,
        config: RealtimeRunConfig | None = None,
    ) -> None:
        """Initialize the realtime runner.

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
        self._event_info = RealtimeEventInfo(context=self._context_wrapper)
        self._override_config = config
        self._history: list[RealtimeItem] = []
        self._model = model

        if transport == "websocket":
            self._transport: RealtimeModel = OpenAIRealtimeWebSocketModel()
        else:
            self._transport = transport

    async def run(self, *, model_config: RealtimeModelConfig | None = None) -> RealtimeSession:
        """Start the session and return a session.

        Returns:
            RealtimeSession: A session object that supports async context management
                               and async iteration for streaming events.

        Example:
            ```python
            runner = RealtimeRunner(agent)
            async with await runner.run() as session:
                await session.send_message("Hello")
                async for event in session:
                    print(event)
            ```
        """
        model_settings = await self._get_model_settings(
            initial_settings=model_config.get("initial_model_settings") if model_config else None,
            overrides=self._override_config.get("model_settings")
            if self._override_config
            else None,
        )

        model_config = model_config.copy() if model_config else {}
        model_config["initial_model_settings"] = model_settings

        # Create and return the connection
        session = RealtimeSession(
            transport=self._transport,
            agent=self._current_agent,
            context_wrapper=self._context_wrapper,
            event_info=self._event_info,
            history=self._history.copy(),
            model_config=model_config,
        )

        return session

    async def _get_model_settings(
        self,
        initial_settings: RealtimeSessionModelSettings | None = None,
        overrides: RealtimeSessionModelSettings | None = None,
    ) -> RealtimeSessionModelSettings:
        model_settings = initial_settings.copy() if initial_settings else {}

        agent = self._current_agent
        instructions, tools = await asyncio.gather(
            agent.get_system_prompt(self._context_wrapper),
            agent.get_all_tools(self._context_wrapper),
        )

        if instructions is not None:
            model_settings["instructions"] = instructions
        if tools is not None:
            model_settings["tools"] = tools

        if overrides:
            model_settings.update(overrides)

        return model_settings
