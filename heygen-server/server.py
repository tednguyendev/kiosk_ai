"""
HeyGen LiveAvatar LITE Mode Proxy Server

This lightweight Flask server:
1. Serves the kiosk frontend (index-heygen.html)
2. Proxies HeyGen session creation (keeps API key server-side)
3. Optionally proxies OpenAI Whisper/TTS and Gemini calls

Usage:
    export HEYGEN_API_KEY="your_key"
    export HEYGEN_AVATAR_ID="your_avatar_id"
    python server.py

The frontend reads config from /api/config instead of hardcoded keys.
"""

import os
import json
import asyncio
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import httpx

app = Flask(__name__)
CORS(app)

# ─── Configuration ───

HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "")
HEYGEN_AVATAR_ID = os.environ.get("HEYGEN_AVATAR_ID", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

HEYGEN_API_BASE = "https://api.liveavatar.com/v1"

# ─── Helpers ───

def require_env(*keys):
    missing = [k for k in keys if not globals().get(k)]
    if missing:
        return jsonify({"error": f"Missing env vars: {', '.join(missing)}"}), 500
    return None

# ─── API Routes ───

@app.route("/api/config")
def api_config():
    """Public config for the frontend (no secrets)."""
    return jsonify({
        "HEYGEN_AVATAR_ID": HEYGEN_AVATAR_ID,
        "GEMINI_MODEL": GEMINI_MODEL,
    })


@app.route("/api/heygen/session", methods=["POST"])
def create_session():
    """Create a HeyGen LITE mode session (API key hidden server-side)."""
    err = require_env("HEYGEN_API_KEY", "HEYGEN_AVATAR_ID")
    if err:
        return err

    data = request.get_json() or {}
    avatar_id = data.get("avatar_id", HEYGEN_AVATAR_ID)
    mode = data.get("mode", "LITE")

    payload = {
        "mode": mode,
        "avatar_id": avatar_id,
        "is_sandbox": False,
        "interactivity_type": "CONVERSATIONAL",
        "video_settings": {"quality": "high"}
    }

    try:
        resp = httpx.post(
            f"{HEYGEN_API_BASE}/sessions/token",
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": HEYGEN_API_KEY,
            },
            json=payload,
            timeout=30.0,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/heygen/start", methods=["POST"])
def start_session():
    """Start a HeyGen session (API key + Bearer token server-side)."""
    err = require_env("HEYGEN_API_KEY")
    if err:
        return err

    data = request.get_json() or {}
    session_id = data.get("session_id")
    session_token = data.get("session_token")

    if not session_id or not session_token:
        return jsonify({"error": "session_id and session_token required"}), 400

    try:
        resp = httpx.post(
            f"{HEYGEN_API_BASE}/sessions/start",
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": HEYGEN_API_KEY,
                "Authorization": f"Bearer {session_token}",
            },
            json={"session_id": session_id},
            timeout=30.0,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/heygen/stop", methods=["POST"])
def stop_session():
    """Stop a HeyGen session."""
    err = require_env("HEYGEN_API_KEY")
    if err:
        return err

    data = request.get_json() or {}
    session_id = data.get("session_id")
    session_token = data.get("session_token")

    if not session_id or not session_token:
        return jsonify({"error": "session_id and session_token required"}), 400

    try:
        resp = httpx.post(
            f"{HEYGEN_API_BASE}/sessions/{session_id}/stop",
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": HEYGEN_API_KEY,
                "Authorization": f"Bearer {session_token}",
            },
            timeout=30.0,
        )
        return jsonify(resp.json() if resp.text else {"stopped": True}), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Optional: Proxy TTS / LLM / STT to hide keys ───

@app.route("/api/openai/tts", methods=["POST"])
def proxy_openai_tts():
    """Proxy OpenAI TTS (hides API key, forces PCM format)."""
    err = require_env("OPENAI_API_KEY")
    if err:
        return err

    data = request.get_json() or {}
    data["response_format"] = "pcm"  # Force PCM for HeyGen compatibility

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=data,
            timeout=60.0,
        )
        # Return raw PCM bytes
        return resp.content, resp.status_code, {"Content-Type": "audio/pcm"}
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/openai/whisper", methods=["POST"])
def proxy_openai_whisper():
    """Proxy OpenAI Whisper transcription."""
    err = require_env("OPENAI_API_KEY")
    if err:
        return err

    try:
        files = {"file": (request.files["file"].filename, request.files["file"].stream, request.files["file"].content_type)}
        data = {k: v for k, v in request.form.items()}

        resp = httpx.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files=files,
            data=data,
            timeout=60.0,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gemini/generate", methods=["POST"])
def proxy_gemini():
    """Proxy Gemini generateContent."""
    err = require_env("GEMINI_API_KEY")
    if err:
        return err

    data = request.get_json() or {}
    model = data.get("model", GEMINI_MODEL)

    try:
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=60.0,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Static files ───

@app.route("/")
def serve_index():
    return send_from_directory("..", "index-heygen.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("..", path)


# ─── Main ───

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    print(f"[HeyGen Server] Starting on port {port}")
    print(f"[HeyGen Server] Avatar ID: {HEYGEN_AVATAR_ID or 'NOT SET'}")
    print(f"[HeyGen Server] API Key: {'SET' if HEYGEN_API_KEY else 'NOT SET'}")
    app.run(host="0.0.0.0", port=port, debug=debug)
