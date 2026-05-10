"""
bitHuman Kiosk Server
Subclasses the built-in StreamServer to add a /speak-text endpoint
that generates TTS via OpenAI and drives the local avatar for lip-sync.

Endpoints:
  GET  /           — Built-in HTML viewer (fullscreen MJPEG)
  GET  /stream     — MJPEG multipart video stream
  POST /speak      — Accept audio file (MP3/WAV/OGG/FLAC), feed to runtime
  POST /speak-text — Accept JSON {text}, generate OpenAI TTS, feed to runtime
  GET  /ws/audio   — WebSocket for raw PCM audio output
  GET  /health     — Health check + runtime status
"""

import asyncio
import inspect
import os
import tempfile

import requests
from aiohttp import web
from aiohttp.web_middlewares import middleware

from bithuman.stream_server import StreamServer, float32_to_int16, load_audio


@middleware
async def cors_middleware(request, handler):
    """Add CORS headers to all responses."""
    if request.method == "OPTIONS":
        # Preflight request
        resp = web.Response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

# ─── Config ───
API_SECRET = "dOIQCNkA6HbqHDvh5JqzKIhr1Cku48P4SzLBlXicA39XED7vdUDFPBh3lMCbt37Gy"
OPENAI_KEY = "YOUR_OPENAI_API_KEY"
MODEL_PATH = "avatar.imx"
HOST = "0.0.0.0"
PORT = 3001


class KioskServer(StreamServer):
    """StreamServer extended with OpenAI TTS text-to-speech."""

    def __init__(self, *args, openai_key: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.openai_key = openai_key

    def create_app(self) -> web.Application:
        app = super().create_app()
        app.middlewares.append(cors_middleware)
        # Replace default / with our kiosk viewer
        app.router.add_get("/viewer", self._handle_kiosk_viewer)
        app.router.add_post("/speak-text", self._handle_speak_text)
        return app

    # ─── Kiosk Viewer ───

    async def _handle_kiosk_viewer(self, request: web.Request) -> web.Response:
        """GET /viewer — minimal test page for the local stream."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>bitHuman Local Kiosk</title>
<style>
body { background:#000; color:#fff; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; padding:20px; margin:0; }
#video { background:#111; border-radius:12px; max-width:100%; max-height:70vh; }
#controls { margin-top:20px; display:flex; gap:10px; flex-wrap:wrap; justify-content:center; }
input { padding:10px; font-size:16px; border-radius:6px; border:none; width:300px; }
button { padding:10px 20px; font-size:16px; border-radius:6px; border:none; cursor:pointer; background:#0a84ff; color:#fff; }
#status { margin-top:10px; color:#aaa; font-size:14px; }
</style>
</head>
<body>
<img id="video" src="/stream" alt="Avatar stream" />
<div id="status">Connecting to stream...</div>
<div id="controls">
  <input type="text" id="textInput" placeholder="Type something to speak..." value="Hello! Welcome to our restaurant!" />
  <button id="speakBtn">Speak</button>
</div>
<script>
const statusEl = document.getElementById('status');
const video = document.getElementById('video');
video.onload = () => { statusEl.textContent = 'Stream connected'; };
video.onerror = () => { statusEl.textContent = 'Stream error — is the server running?'; };

document.getElementById('speakBtn').addEventListener('click', async () => {
  const text = document.getElementById('textInput').value;
  statusEl.textContent = 'Generating speech...';
  try {
    const res = await fetch('/speak-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      statusEl.textContent = 'Speaking: ' + text.slice(0, 40) + (text.length > 40 ? '...' : '');
    } else {
      statusEl.textContent = 'Error: ' + (data.error || 'unknown');
    }
  } catch (e) {
    statusEl.textContent = 'Error: ' + e.message;
  }
});
document.getElementById('textInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('speakBtn').click();
});
</script>
</body>
</html>"""
        return web.Response(text=html, content_type="text/html")

    # ─── Text-to-Speech ───

    async def _handle_speak_text(self, request: web.Request) -> web.Response:
        """POST /speak-text — accept JSON {text}, generate OpenAI TTS, feed to runtime."""
        if self._runtime is None:
            return web.json_response(
                {"error": "Runtime not initialized"}, status=503
            )

        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        text = data.get("text", "").strip()
        if not text:
            return web.json_response({"error": "No text provided"}, status=400)

        # 1. Generate TTS audio via OpenAI
        try:
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
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
            resp.raise_for_status()
            mp3_data = resp.content
        except Exception as e:
            return web.json_response(
                {"error": f"TTS generation failed: {e}"}, status=500
            )

        # 2. Decode MP3 → PCM int16 and push to runtime in chunks
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            try:
                os.write(fd, mp3_data)
                os.close(fd)
                audio_float, sample_rate = load_audio(tmp_path, target_sr=16000)
            finally:
                os.unlink(tmp_path)

            audio_int16 = float32_to_int16(audio_float)
            duration = len(audio_int16) / sample_rate

            # Stream audio to runtime in FPS-aligned chunks
            chunk_size = sample_rate // 25  # 640 samples @ 16kHz
            for i in range(0, len(audio_int16), chunk_size):
                chunk = audio_int16[i : i + chunk_size]
                await self._runtime.push_audio(
                    chunk.tobytes(), sample_rate, last_chunk=False
                )

            await self._runtime.flush()

            return web.json_response({
                "status": "ok",
                "duration_seconds": round(duration, 2),
                "samples": len(audio_int16),
            })

        except Exception as e:
            return web.json_response(
                {"error": f"Audio processing failed: {e}"}, status=500
            )


if __name__ == "__main__":
    server = KioskServer(
        model_path=MODEL_PATH,
        api_key=API_SECRET,
        openai_key=OPENAI_KEY,
        host=HOST,
        port=PORT,
        jpeg_quality=80,
    )
    print(f"[KioskServer] Starting on http://{HOST}:{PORT}")
    print(f"[KioskServer] Viewer: http://{HOST}:{PORT}/viewer")
    print(f"[KioskServer] Stream: http://{HOST}:{PORT}/stream")
    print(f"[KioskServer] Speak (audio): POST http://{HOST}:{PORT}/speak")
    print(f"[KioskServer] Speak (text):  POST http://{HOST}:{PORT}/speak-text")
    asyncio.run(server.run_async())
