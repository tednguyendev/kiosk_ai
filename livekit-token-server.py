#!/usr/bin/env python3
"""Minimal token server for LiveKit dev testing."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

from livekit import api

LIVEKIT_API_KEY = "devkey"
LIVEKIT_API_SECRET = "secret"


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
    print("[TokenServer] Starting on http://localhost:8081")
    HTTPServer(("0.0.0.0", 8082), Handler).serve_forever()
