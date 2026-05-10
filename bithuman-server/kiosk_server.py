"""
bitHuman Kiosk Server
Subclasses the built-in StreamServer to add a /speak-text endpoint
that generates TTS and drives the local avatar for lip-sync.

TTS strategy (fastest first):
  1. macOS `say` command — local, ~100-300ms, no network
  2. OpenAI TTS API — cloud, ~1-3s, higher quality fallback

Endpoints:
  GET  /           — Built-in HTML viewer (fullscreen MJPEG)
  GET  /stream     — MJPEG multipart video stream
  POST /speak      — Accept audio file (MP3/WAV/OGG/FLAC/AIFF), feed to runtime
  POST /speak-text — Accept JSON {text}, generate TTS, feed to runtime
  GET  /ws/audio   — WebSocket for raw PCM audio output
  GET  /health     — Health check + runtime status
"""

import asyncio
import os
import subprocess
import tempfile

import requests
from aiohttp import web
from aiohttp.web_middlewares import middleware

from bithuman.stream_server import StreamServer, float32_to_int16, load_audio


@middleware
async def cors_middleware(request, handler):
    """Add CORS headers to all responses."""
    if request.method == "OPTIONS":
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
    """StreamServer extended with local + cloud TTS text-to-speech."""

    def __init__(self, *args, openai_key: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.openai_key = openai_key

    def create_app(self) -> web.Application:
        app = super().create_app()
        app.middlewares.append(cors_middleware)
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

    # ─── TTS helpers ───

    def _pick_say_voice(self, text: str) -> str:
        """Pick an appropriate macOS `say` voice based on text language."""
        # Simple heuristic: Chinese characters -> Chinese voice
        if any("\u4e00" <= ch <= "\u9fff" for ch in text):
            return "Ting-Ting"
        return "Samantha"

    async def _generate_tts_local(self, text: str) -> bytes:
        """Generate TTS using macOS `say` command. Returns AIFF bytes."""
        voice = self._pick_say_voice(text)
        fd, tmp_path = tempfile.mkstemp(suffix=".aiff")
        try:
            os.close(fd)
            proc = await asyncio.create_subprocess_exec(
                "say", "-v", voice, "-o", tmp_path, text,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
            if proc.returncode != 0:
                raise RuntimeError(f"say exited with code {proc.returncode}")
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    async def _generate_tts_openai(self, text: str) -> bytes:
        """Generate TTS using OpenAI API. Returns MP3 bytes."""
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
        return resp.content

    async def _push_audio_to_runtime(self, audio_bytes: bytes, suffix: str) -> float:
        """Decode audio bytes and push to bithuman runtime. Returns duration."""
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            os.write(fd, audio_bytes)
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
        return duration

    # ─── Text-to-Speech endpoint ───

    async def _handle_speak_text(self, request: web.Request) -> web.Response:
        """POST /speak-text — accept JSON {text}, generate TTS, feed to runtime."""
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

        audio_bytes = None
        suffix = ".mp3"
        tts_source = "unknown"

        # 1. Try local macOS `say` first (fastest, ~100-300ms)
        if os.uname().sysname == "Darwin":
            try:
                audio_bytes = await self._generate_tts_local(text)
                suffix = ".aiff"
                tts_source = "local"
                print(f"[TTS] Local say: {text[:50]}...")
            except Exception as e:
                print(f"[TTS] Local say failed: {e}, falling back to OpenAI")

        # 2. Fall back to OpenAI TTS
        if audio_bytes is None:
            try:
                audio_bytes = await self._generate_tts_openai(text)
                suffix = ".mp3"
                tts_source = "openai"
                print(f"[TTS] OpenAI: {text[:50]}...")
            except Exception as e:
                return web.json_response(
                    {"error": f"TTS generation failed: {e}"}, status=500
                )

        # 3. Push to runtime
        try:
            duration = await self._push_audio_to_runtime(audio_bytes, suffix)
            return web.json_response({
                "status": "ok",
                "duration_seconds": round(duration, 2),
                "samples": int(duration * 16000),
                "tts_source": tts_source,
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
