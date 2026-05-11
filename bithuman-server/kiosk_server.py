"""
bitHuman Kiosk Server
Subclasses the built-in StreamServer to add a /speak-text endpoint
that generates TTS and drives the local avatar for lip-sync.

TTS: Microsoft Edge TTS (free, high-quality neural voices)
  - English: en-SG-LunaNeural  (Singapore English ~ Malaysian)
  - Chinese: zh-CN-XiaoxiaoNeural
  - Auto-detects language from text

Endpoints:
  GET  /           — Built-in HTML viewer (fullscreen MJPEG)
  GET  /stream     — MJPEG multipart video stream
  POST /speak      — Accept audio file, feed to runtime
  POST /speak-text — Accept JSON {text}, generate TTS, feed to runtime
  GET  /ws/audio   — WebSocket for raw PCM audio output
  GET  /health     — Health check + runtime status
"""

import asyncio
import os
import tempfile

import edge_tts
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
MODEL_PATH = "avatar.imx"
HOST = "0.0.0.0"
PORT = 3001

# Edge TTS voices
VOICE_EN = "en-SG-LunaNeural"      # Singapore English (closest to Malaysian)
VOICE_ZH = "zh-CN-XiaoxiaoNeural"  # Chinese (Mainland)


def detect_language(text: str) -> str:
    """Detect if text is Chinese or English."""
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "zh"
    return "en"


class KioskServer(StreamServer):
    """StreamServer extended with Edge TTS text-to-speech."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    # ─── Text-to-Speech endpoint ───

    async def _handle_speak_text(self, request: web.Request) -> web.Response:
        """POST /speak-text — accept JSON {text}, generate Edge TTS, feed to runtime."""
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

        # 1. Detect language and pick voice
        lang = detect_language(text)
        voice = VOICE_ZH if lang == "zh" else VOICE_EN
        print(f"[TTS] lang={lang}, voice={voice}, text={text[:50]}...")

        # 2. Generate TTS via Edge TTS
        try:
            fd, tmp_mp3 = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp_mp3)

            # 3. Load MP3 → PCM int16
            audio_float, sample_rate = load_audio(tmp_mp3, target_sr=16000)
            os.unlink(tmp_mp3)

            audio_int16 = float32_to_int16(audio_float)
            duration = len(audio_int16) / sample_rate

            # 4. Push to runtime in FPS-aligned chunks
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
                "lang": lang,
                "voice": voice,
            })

        except Exception as e:
            return web.json_response(
                {"error": f"TTS failed: {e}"}, status=500
            )


if __name__ == "__main__":
    server = KioskServer(
        model_path=MODEL_PATH,
        api_key=API_SECRET,
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
