#!/usr/bin/env python3
"""Token server for LiveKit Cloud + bithuman Cloud Kiosk.

Usage:
  export LIVEKIT_API_KEY=your_key
  export LIVEKIT_API_SECRET=your_secret
  python livekit-token-server.py
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

from livekit import api

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    raise RuntimeError(
        "LIVEKIT_API_KEY and LIVEKIT_API_SECRET env vars required.\n"
        "Get them from https://cloud.livekit.io → Settings → Keys"
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/token":
            params = urllib.parse.parse_qs(parsed.query)
            identity = params.get("identity", ["user"])[0]
            room = params.get("room", ["kiosk-room"])[0]

            token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            token.with_identity(identity)
            token.with_name(identity)
            token.with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            jwt = token.to_jwt()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"token": jwt}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[TokenServer] {args[0]}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8082"))
    print(f"[TokenServer] Starting on http://0.0.0.0:{port}")
    print("[TokenServer] CORS enabled for all origins")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
