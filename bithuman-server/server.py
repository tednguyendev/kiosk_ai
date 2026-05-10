"""
bitHuman Self-Hosted Server (DEPRECATED — use kiosk_server.py instead)

This was an early attempt using FastAPI + WebSocket for frame streaming.
It had websockets library compatibility issues (AssertionError on keepalive ping)
and has been superseded by kiosk_server.py which subclasses the built-in
bithuman StreamServer for reliable MJPEG streaming + OpenAI TTS integration.

Loads .imx model locally, streams video frames via WebSocket.
Receives text, generates TTS audio, pushes to bithuman runtime for lip-sync.
"""

import asyncio
import io
import json
import base64
import numpy as np
from PIL import Image
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# bitHuman
from bithuman import AsyncBithuman

# TTS
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Config ───
API_SECRET = "dOIQCNkA6HbqHDvh5JqzKIhr1Cku48P4SzLBlXicA39XED7vdUDFPBh3lMCbt37Gy"
OPENAI_KEY = "YOUR_OPENAI_API_KEY"
MODEL_PATH = "avatar.imx"
SAMPLE_RATE = 24000  # OpenAI TTS sample rate

# ─── Globals ───
runtime = None
clients = set()
frame_queue = asyncio.Queue(maxsize=5)  # drop old frames if browser can't keep up


async def encode_frame(frame) -> bytes:
    """Encode bithuman frame video to JPEG bytes."""
    if not frame.has_image:
        return None
    video = frame.rgb_image  # numpy array [H, W, 3], uint8 RGB
    if video is None:
        return None
    img = Image.fromarray(video)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def frame_producer():
    """Continuously read frames from bithuman and put in queue."""
    global runtime
    if runtime is None:
        print("[Server] Loading model...")
        runtime = await AsyncBithuman.create(
            model_path=MODEL_PATH,
            api_secret=API_SECRET,
        )
        # Don't call start() here - the run() method handles it
        print(f"[Server] Model loaded.")

    async for frame in runtime.run():
        jpeg = await encode_frame(frame)
        if jpeg is None:
            continue
        # Drop old frame if queue is full (browser can't keep up)
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        await frame_queue.put(jpeg)


async def broadcast_frames():
    """Send frames from queue to all connected WebSocket clients."""
    while True:
        jpeg = await frame_queue.get()
        disconnected = []
        for ws in clients:
            try:
                await ws.send_bytes(jpeg)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            clients.discard(ws)


@app.on_event("startup")
async def startup():
    asyncio.create_task(frame_producer())
    asyncio.create_task(broadcast_frames())
    print("[Server] Started frame producer and broadcaster")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    print(f"[Server] Client connected. Total: {len(clients)}")
    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            action = data.get("action")

            if action == "speak":
                text = data.get("text", "")
                await handle_speak(text)
            elif action == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        print("[Server] Client disconnected")
    finally:
        clients.discard(ws)


async def handle_speak(text: str):
    """Generate TTS audio and push to bithuman runtime."""
    print(f"[Server] speak: {text[:60]}...")

    # 1. Generate TTS audio via OpenAI
    try:
        audio_bytes = await generate_tts(text)
        print(f"[Server] TTS audio: {len(audio_bytes)} bytes")
    except Exception as e:
        print(f"[Server] TTS error: {e}")
        return

    # 2. Convert MP3 to raw PCM int16
    audio_pcm = await mp3_to_pcm(audio_bytes)
    if audio_pcm is None:
        print("[Server] Failed to decode MP3")
        return

    # 3. Push to bithuman runtime
    if runtime:
        runtime.push_audio(audio_pcm, SAMPLE_RATE)
        runtime.flush()
        print("[Server] Audio pushed to runtime")


async def mp3_to_pcm(mp3_bytes: bytes) -> bytes:
    """Convert MP3 bytes to raw PCM int16 bytes using ffmpeg."""
    import subprocess
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", "pipe:0", "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-f", "s16le", "-",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=mp3_bytes)
    if proc.returncode != 0:
        print(f"[Server] ffmpeg error: {stderr.decode()[:200]}")
        return None
    return stdout


async def generate_tts(text: str) -> bytes:
    """Call OpenAI TTS API."""
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "tts-1",
                "input": text,
                "voice": "alloy",
                "response_format": "mp3",
            },
            timeout=30,
        ),
    )
    response.raise_for_status()
    return response.content


@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(clients), "runtime_loaded": runtime is not None}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8766)
