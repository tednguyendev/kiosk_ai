"""
bitHuman Kiosk Server
Subclasses the built-in StreamServer.

Audio pipeline (NEW):
  - OpenAI TTS generates MP3 → saved to tts_output/
  - Browser fetches MP3 and plays directly (high quality)
  - MP3 is ALSO pushed to bithuman runtime for lip-sync video only

Endpoints:
  GET  /           — Built-in HTML viewer
  GET  /stream     — MJPEG multipart video stream
  POST /speak      — Accept audio file, feed to runtime
  POST /speak-text — Accept JSON {text}, generate TTS, return MP3 URL
  GET  /tts-output/<file> — Serve generated MP3 files
  GET  /ws/audio   — WebSocket for raw PCM audio (kept for backwards compat)
  GET  /health     — Health check
"""

import asyncio
import os
import tempfile
import glob
import time

from openai import AsyncOpenAI
from aiohttp import web
from aiohttp.web_middlewares import middleware

from bithuman import AsyncBithuman
from bithuman.stream_server import StreamServer, float32_to_int16, load_audio

TTS_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "tts_output")
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)

@middleware
async def cors_middleware(request, handler):
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
API_SECRET = "W8OWvGKO9P0kdF8dU2YBcPHKIw5iegMGSP8FvvGHFVlvdZAT1MQvB2ICDGsRg2ZHE"
MODEL_PATH = "avatar.imx"
HOST = "0.0.0.0"
PORT = 3001

OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
OPENAI_VOICE = "nova"

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def detect_language(text: str) -> str:
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "zh"
    return "en"


def _cleanup_old_tts(max_age_seconds=300):
    """Remove MP3 files older than 5 minutes to prevent disk bloat."""
    now = time.time()
    for path in glob.glob(os.path.join(TTS_OUTPUT_DIR, "*.mp3")):
        if now - os.path.getmtime(path) > max_age_seconds:
            try:
                os.unlink(path)
            except OSError:
                pass


class KioskServer(StreamServer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_app(self) -> web.Application:
        app = super().create_app()
        app.middlewares.append(cors_middleware)
        app.router.add_get("/viewer", self._handle_kiosk_viewer)
        app.router.add_post("/speak-text", self._handle_speak_text)
        app.router.add_static("/tts-output", TTS_OUTPUT_DIR)
        return app

    async def _init_runtime(self) -> None:
        self._runtime = await AsyncBithuman.create(
            model_path=self.model_path,
            api_secret=self.api_key,
            output_buffer_size=2,
        )
        script = self._runtime.video_graph.videos_script
        script.BACK_TO_IDLE = 2
        for action in script.idle_actions:
            action.interval = (5.0, 15.0)
        script.set_next_idle_action()
        await self._runtime.start()

    async def _handle_kiosk_viewer(self, request: web.Request) -> web.Response:
        html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>bitHuman Local Kiosk</title>
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
      const audio = new Audio(data.audio_url);
      audio.play();
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

    async def _handle_speak_text(self, request: web.Request) -> web.Response:
        if self._runtime is None:
            return web.json_response({"error": "Runtime not initialized"}, status=503)

        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        text = data.get("text", "").strip()
        if not text:
            return web.json_response({"error": "No text provided"}, status=400)

        lang = detect_language(text)
        print(f"[TTS] lang={lang}, text={text[:60]}...")

        try:
            _cleanup_old_tts()

            # 1. Generate TTS via OpenAI
            response = await openai_client.audio.speech.create(
                model="tts-1",
                voice=OPENAI_VOICE,
                input=text,
                response_format="mp3",
                speed=1.0,
            )

            # 2. Save MP3 to tts_output/ with timestamp
            ts = int(time.time() * 1000)
            mp3_filename = f"tts_{ts}.mp3"
            mp3_path = os.path.join(TTS_OUTPUT_DIR, mp3_filename)
            with open(mp3_path, "wb") as f:
                f.write(response.content)

            # 3. Load MP3 → PCM int16 for lip-sync
            fd, tmp_mp3 = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            with open(tmp_mp3, "wb") as f:
                f.write(response.content)

            audio_float, sample_rate = load_audio(tmp_mp3, target_sr=16000)
            os.unlink(tmp_mp3)

            audio_int16 = float32_to_int16(audio_float)
            duration = len(audio_int16) / sample_rate

            # 4. Push to runtime for lip-sync video
            chunk_size = sample_rate // 25
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
                "voice": OPENAI_VOICE,
                "tts": "openai",
                "audio_url": f"/tts-output/{mp3_filename}",
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
