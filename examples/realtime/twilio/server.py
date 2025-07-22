import asyncio
import base64
import json
import logging
import os
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from agents import function_tool
from agents.realtime import RealtimeAgent, RealtimeRunner, RealtimeSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@function_tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."


@function_tool
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime

    return f"The current time is {datetime.now().strftime('%H:%M:%S')}"


agent = RealtimeAgent(
    name="Twilio Assistant",
    instructions="You are a helpful assistant that starts every conversation with a creative greeting. Keep responses concise and friendly since this is a phone conversation.",
    tools=[get_weather, get_current_time],
)


class TwilioWebSocketManager:
    def __init__(self):
        self.active_sessions: dict[str, RealtimeSession] = {}
        self.session_contexts: dict[str, Any] = {}
        self.websockets: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, call_sid: str):
        await websocket.accept()
        self.websockets[call_sid] = websocket
        logger.info(f"WebSocket connection accepted for call {call_sid}")

        runner = RealtimeRunner(agent)
        session_context = await runner.run()
        session = await session_context.__aenter__()
        self.active_sessions[call_sid] = session
        self.session_contexts[call_sid] = session_context

        # Start event processing task
        asyncio.create_task(self._process_events(call_sid))

    async def disconnect(self, call_sid: str):
        logger.info(f"Disconnecting call {call_sid}")
        if call_sid in self.session_contexts:
            await self.session_contexts[call_sid].__aexit__(None, None, None)
            del self.session_contexts[call_sid]
        if call_sid in self.active_sessions:
            del self.active_sessions[call_sid]
        if call_sid in self.websockets:
            del self.websockets[call_sid]

    async def handle_twilio_message(self, call_sid: str, message: dict[str, Any]):
        """Handle incoming Twilio WebSocket messages"""
        event = message.get("event")

        if event == "connected":
            logger.info(f"Twilio media stream connected for call {call_sid}")
        elif event == "start":
            logger.info(f"Media stream started for call {call_sid}")
        elif event == "media":
            # Handle audio data from Twilio
            payload = message.get("media", {})
            audio_data = payload.get("payload", "")
            if audio_data and call_sid in self.active_sessions:
                # Decode base64 audio and send to OpenAI
                try:
                    audio_bytes = base64.b64decode(audio_data)
                    await self.active_sessions[call_sid].send_audio(audio_bytes)
                except Exception as e:
                    logger.error(f"Error processing audio for call {call_sid}: {e}")
        elif event == "stop":
            logger.info(f"Media stream stopped for call {call_sid}")

    async def send_audio_to_twilio(self, call_sid: str, audio_bytes: bytes):
        """Send audio back to Twilio"""
        if call_sid in self.websockets:
            websocket = self.websockets[call_sid]
            # Encode audio as base64 for Twilio
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            message = {"event": "media", "streamSid": call_sid, "media": {"payload": audio_base64}}

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending audio to Twilio for call {call_sid}: {e}")

    async def _process_events(self, call_sid: str):
        """Process events from OpenAI Realtime API and send audio to Twilio"""
        try:
            session = self.active_sessions[call_sid]

            async for event in session:
                if event.type == "audio":
                    # Send audio back to Twilio
                    await self.send_audio_to_twilio(call_sid, event.audio.data)
                elif event.type == "error":
                    logger.error(f"OpenAI Realtime API error for call {call_sid}: {event}")

        except Exception as e:
            logger.error(f"Error processing events for call {call_sid}: {e}")


manager = TwilioWebSocketManager()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Twilio Media Stream Server is running!"}


@app.post("/incoming-call")
@app.get("/incoming-call")
async def incoming_call():
    """Handle incoming Twilio phone calls"""
    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello! You're now connected to an AI assistant. You can start talking!</Say>
    <Connect>
        <Stream url="wss://your-ngrok-url.ngrok.io/media-stream" />
    </Connect>
</Response>"""
    return PlainTextResponse(content=twiml_response, media_type="text/xml")


@app.websocket("/media-stream")
async def media_stream_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Twilio Media Streams"""
    call_sid = None

    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Extract call SID from the first message
            if call_sid is None:
                call_sid = message.get("streamSid", "unknown")
                await manager.connect(websocket, call_sid)

            await manager.handle_twilio_message(call_sid, message)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        if call_sid:
            await manager.disconnect(call_sid)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if call_sid:
            await manager.disconnect(call_sid)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
