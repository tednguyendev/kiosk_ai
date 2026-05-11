#!/usr/bin/env python3
"""
Test bithuman cloud REST API.
No local model. Just HTTP calls to api.bithuman.ai
"""
import os
import sys
import json
import time
import requests

API_BASE = "https://api.bithuman.ai/v1"
API_SECRET = "dOIQCNkA6HbqHDvh5JqzKIhr1Cku48P4SzLBlXicA39XED7vdUDFPBh3lMCbt37Gy"

headers = {"api-secret": API_SECRET}


def validate():
    """Check API secret is valid."""
    r = requests.post(f"{API_BASE}/validate", headers=headers)
    print(f"[/v1/validate] {r.status_code}")
    print(r.text)
    return r.ok


def list_agents():
    """Get existing agents. There is no list endpoint in the docs,
    so we try to infer from what we can access."""
    # The REST API docs don't show a list endpoint.
    # We'll need an agent ID to test /speak.
    print("\n[bithuman cloud] REST API /speak requires an AGENT_ID.")
    print("You get one from https://www.bithuman.ai → Dashboard → Agents")
    return []


def speak(agent_id: str, text: str):
    """POST /v1/agent/{code}/speak — returns avatar video speaking the text."""
    url = f"{API_BASE}/agent/{agent_id}/speak"
    payload = {"text": text}
    print(f"\n[POST {url}]")
    print(f"Payload: {payload}")

    start = time.time()
    r = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=payload)
    elapsed = time.time() - start

    print(f"Status: {r.status_code}  ({elapsed:.2f}s)")
    print(f"Content-Type: {r.headers.get('Content-Type', 'unknown')}")
    print(f"Content-Length: {r.headers.get('Content-Length', len(r.content))} bytes")

    if r.status_code == 200:
        ct = r.headers.get("Content-Type", "")
        if "video" in ct or "mp4" in ct or len(r.content) > 100_000:
            out = "bithuman-cloud-speech.mp4"
            with open(out, "wb") as f:
                f.write(r.content)
            print(f"Saved video: {out}  ({len(r.content)/1024/1024:.1f} MB)")
            return out
        else:
            print(f"Response body:\n{r.text[:2000]}")
    else:
        print(f"Error body:\n{r.text[:2000]}")
    return None


def generate_agent(name: str, image_path: str = None):
    """POST /v1/agent/generate — create a new agent."""
    url = f"{API_BASE}/agent/generate"
    payload = {"name": name}
    print(f"\n[POST {url}]")
    print(f"Payload: {payload}")

    # If image provided, upload it first
    files = None
    if image_path and os.path.exists(image_path):
        print(f"Uploading image: {image_path}")
        files = {"image": open(image_path, "rb")}

    r = requests.post(url, headers=headers, data=payload, files=files)
    print(f"Status: {r.status_code}")
    print(r.text)
    if r.ok:
        data = r.json()
        return data.get("code") or data.get("id") or data.get("agent_id")
    return None


def check_credits():
    """GET /v2/credit-summaries"""
    url = f"{API_BASE.replace('/v1', '/v2')}/credit-summaries"
    r = requests.get(url, headers=headers)
    print(f"\n[/v2/credit-summaries] {r.status_code}")
    print(r.text)


if __name__ == "__main__":
    print("=" * 60)
    print("bithuman Cloud API Test")
    print("=" * 60)

    # 1. Validate API key
    if not validate():
        print("\n❌ API secret invalid. Check your key at bithuman.ai")
        sys.exit(1)
    print("✅ API secret valid")

    # 2. Check credits
    check_credits()

    # 3. Need an agent ID
    agent_id = os.environ.get("BITHUMAN_AGENT_ID", "").strip()
    if not agent_id:
        print("\n⚠️  No BITHUMAN_AGENT_ID set.")
        print("   You have two options:")
        print("   A) Set env var: export BITHUMAN_AGENT_ID=YOUR_AGENT_CODE")
        print("   B) I can try to create a new agent for you")
        choice = input("\nCreate new agent? (y/n): ").strip().lower()
        if choice == "y":
            name = input("Agent name: ").strip() or "Kiosk Kimberly"
            agent_id = generate_agent(name)
            if agent_id:
                print(f"\n🎉 Created agent: {agent_id}")
                print(f"   Set this in your env: export BITHUMAN_AGENT_ID={agent_id}")
            else:
                print("\n❌ Failed to create agent")
                sys.exit(1)
        else:
            print("\nExiting. Set BITHUMAN_AGENT_ID and run again.")
            sys.exit(0)

    # 4. Test speak
    text = input(f"\nText for agent {agent_id} to speak (default: 'Hello, welcome to Kopitiam!'): ").strip()
    if not text:
        text = "Hello, welcome to Kopitiam!"

    video_path = speak(agent_id, text)
    if video_path:
        print(f"\n✅ Success! Video saved: {video_path}")
        # Try to open it
        os.system(f"open {video_path}")
    else:
        print("\n❌ Speak request failed")
