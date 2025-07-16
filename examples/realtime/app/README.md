# Realtime Demo App

A web-based realtime voice assistant demo with a FastAPI backend and clean HTML/JS frontend.

## Features

- **Connect/Disconnect**: Simple button to establish realtime session
- **Two-pane Interface**: 
  - Left pane: Message thread showing conversation transcript with user/assistant alignment
  - Right pane: Raw transport events display with collapsible event details
- **Voice Input**: Continuous microphone capture with mute/unmute control
- **Audio Playback**: Real-time audio output from the assistant
- **Clean UI**: Elegant, responsive design with smooth interactions

## Installation

Install the required dependencies:

```bash
uv add fastapi uvicorn websockets
```

## Usage

Start the application with a single command:

```bash
cd examples/realtime/app && uv run python server.py
```

Then open your browser to: http://localhost:8000

## How to Use

1. Click **Connect** to establish a realtime session
2. Audio capture starts automatically - just speak naturally
3. Click the **Mic On/Off** button to mute/unmute your microphone
4. Watch the conversation unfold in the left pane
5. Monitor raw events in the right pane (click to expand/collapse)
6. Click **Disconnect** when done

## Architecture

- **Backend**: FastAPI server with WebSocket connections for real-time communication
- **Session Management**: Each connection gets a unique session with the OpenAI Realtime API
- **Audio Processing**: 24kHz mono audio capture and playback
- **Event Handling**: Full event stream processing with transcript generation
- **Frontend**: Vanilla JavaScript with clean, responsive CSS

The demo showcases the core patterns for building realtime voice applications with the OpenAI Agents SDK.