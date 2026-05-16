"""
Start the built-in bithuman StreamServer for MJPEG streaming.

NOTE: Use kiosk_server.py instead — it extends StreamServer with an
OpenAI TTS /speak-text endpoint so the kiosk can send text directly.
This wrapper is kept for reference but is not needed for the full kiosk.
"""

import asyncio
import os
from bithuman.stream_server import StreamServer

API_SECRET = os.environ.get("BITHUMAN_API_SECRET", "")
MODEL_PATH = "avatar.imx"

async def main():
    server = StreamServer(
        model_path=MODEL_PATH,
        api_key=API_SECRET,
        host="0.0.0.0",
        port=3001,
        jpeg_quality=80,
    )
    await server.run_async()

if __name__ == "__main__":
    asyncio.run(main())
