# HeyGen LiveAvatar Integration — Kopitiam Kiosk

> Branch: `heygen-realtime`
> Date: 2026-05-11
> Status: **Prototype — needs API keys to test**

## Overview

This branch implements **HeyGen LiveAvatar LITE Mode** for the Kopitiam AI concierge kiosk. HeyGen is the only remaining untried provider that offers:

- **Full body avatar** (Avatar IV with gestures)
- **Real-time streaming** via WebRTC/LiveKit
- **Custom UI** (we control the frontend completely)
- **Non-enterprise pricing** (~$6/hr, 1 credit/minute in LITE mode)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER (Kiosk)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Whisper    │→ │   Gemini    │→ │   OpenAI TTS (PCM)      │  │
│  │  VAD + STT  │  │   LLM       │  │   24kHz 16-bit mono     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                              │                  │
│                                              ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  HeyGen WebSocket  →  agent.speak (Base64 PCM chunks)   │   │
│  │  (LITE mode control channel)                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                              │                  │
│                                              ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LiveKit Room  ←  avatar video track (WebRTC)           │   │
│  │  (displayed in <video> element)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HEYGEN LIVEAVATAR CLOUD                       │
│         (avatar rendering + lip-sync + video streaming)          │
└─────────────────────────────────────────────────────────────────┘
```

## LITE Mode vs FULL Mode

| Aspect | LITE Mode (this branch) | FULL Mode |
|--------|------------------------|-----------|
| **STT** | Our Whisper | HeyGen (Deepgram/AssemblyAI) |
| **LLM** | Our Gemini + custom prompt | HeyGen (OpenAI 4o-mini) |
| **TTS** | Our OpenAI TTS | HeyGen (ElevenLabs Flash) |
| **Avatar** | HeyGen renders + streams | HeyGen renders + streams |
| **Price** | 1 credit/minute | 2 credits/minute |
| **Control** | Full (our pipeline) | Limited (HeyGen's pipeline) |
| **Knowledge** | Custom system prompt | Context/knowledge base |

We chose **LITE mode** because:
1. We need our custom Gemini system prompt with the full stall directory
2. We need Whisper for robust multilingual STT (English + Chinese)
3. We need fine-grained control over the conversation flow
4. It's cheaper (1 vs 2 credits/minute)

## Files

| File | Purpose |
|------|---------|
| `index-heygen.html` | Main kiosk frontend with HeyGen LITE mode integration |
| `heygen-server/server.py` | Optional Flask backend to hide API keys |
| `heygen-server/requirements.txt` | Python dependencies |
| `HEYGEN_INTEGRATION.md` | This document |

## Quick Start

### 1. Get HeyGen credentials

1. Sign up at [https://app.liveavatar.com](https://app.liveavatar.com)
2. Go to **Settings → API Keys** → copy your API key
3. Go to **Avatars** → choose an avatar → copy the avatar ID
   - For full body, look for **Avatar IV** or video avatars
   - Custom avatars require video + consent verification

### 2. Option A: Frontend-only (quick test)

Edit `index-heygen.html` and replace the placeholder config:

```javascript
window.__CONFIG = {
  HEYGEN_API_KEY: 'your_actual_api_key_here',
  HEYGEN_AVATAR_ID: 'your_actual_avatar_id_here',
  // ... keep other keys
};
```

Then serve the file with any static server:

```bash
python -m http.server 8080
# Open http://localhost:8080/index-heygen.html
```

### 3. Option B: With backend (recommended for production)

```bash
cd heygen-server
pip install -r requirements.txt

export HEYGEN_API_KEY="your_key"
export HEYGEN_AVATAR_ID="your_avatar_id"
export OPENAI_API_KEY="your_key"
export GEMINI_API_KEY="your_key"

python server.py
# Open http://localhost:8080
```

The backend:
- Hides all API keys from the frontend
- Proxies session creation, TTS, Whisper, and Gemini calls
- Serves the frontend automatically

## Audio Pipeline Detail

### PCM Format (perfect match!)

| Requirement | OpenAI TTS `pcm` | HeyGen LITE |
|-------------|------------------|-------------|
| Sample rate | 24,000 Hz | 24,000 Hz ✅ |
| Bit depth | 16-bit | 16-bit ✅ |
| Channels | mono | mono ✅ |
| Encoding | raw PCM | raw PCM ✅ |
| Chunk size | configurable | ~1 second recommended |

This is a **perfect format match** — no audio conversion needed in the browser!

### Chunking strategy

```
OpenAI TTS PCM → Uint8Array
→ Split into 0.5s chunks (24,000 bytes each)
→ Base64 encode each chunk
→ Send via WebSocket: {"type": "agent.speak", "audio": "<base64>"}
→ Throttle sends to ~70% of real-time to avoid buffer overflow
```

### WebSocket Events

**Commands we send:**
- `agent.speak` — stream audio chunk
- `agent.speak_end` — signal end of speech
- `agent.interrupt` — stop current speech (barge-in)
- `session.keep_alive` — extend session (every 60s)

**Events we receive:**
- `session.state_updated` — wait for `state: "connected"`
- `agent.speak_started` — avatar started lip-syncing
- `agent.speak_ended` — avatar finished, unlock mic

## Barge-in / Interruption

When the user starts speaking while the avatar is talking:

1. VAD detects speech → `speakingRef = true`
2. Send `agent.interrupt` via WebSocket
3. Avatar stops immediately
4. `agent.speak_ended` event fires
5. Mic unlocks → new turn begins

This is much cleaner than the bithuman MJPEG+WebSocket approach because the interrupt is handled by HeyGen's infrastructure.

## Comparison with Previous Attempts

| Provider | Body | Custom UI | Our LLM | A/V Sync | Deployable | Status |
|----------|------|-----------|---------|----------|------------|--------|
| **Anam** | Face only | Yes | Yes | Native | Static | ✅ Working |
| **bithuman local** | Full | Yes | Yes | Flaky (MJPEG+WS) | Needs server | ❌ Server overload |
| **bithuman cloud** | Full | Yes | Yes | Native (LiveKit) | Needs server | ❌ No LiveKit creds |
| **HeyGen LITE** | Full | Yes | Yes | Native (LiveKit) | Static* | 🔄 **This branch** |

*Static if API keys are exposed; backend recommended for production.

## Known Issues / TODO

1. **API key setup required** — Need actual HeyGen credentials to test
2. **Avatar ID selection** — Need to verify Avatar IV (full body) IDs work in LITE mode
3. **WebSocket URL** — The start session response format is inferred from docs; may need adjustment
4. **Audio chunk timing** — 0.5s chunks at 70% throttle is a guess; may need tuning
5. **LiveKit track handling** — Video track attachment logic may need refinement
6. **Backend integration** — Frontend still has hardcoded keys; backend proxy needs testing

## Pricing Estimate

For a kiosk running 8 hours/day:

- LITE mode: 1 credit/minute = 60 credits/hour = 480 credits/day
- ~$6/hour = ~$48/day = ~$1,440/month

Compare:
- Anam: ~$0.50/minute = ~$240/day (but face-only)
- bithuman local: $0 (but needs $20-40/month server)
- bithuman cloud: similar to HeyGen

## Next Steps

1. [ ] Get HeyGen API key and avatar ID
2. [ ] Test session creation + start flow
3. [ ] Verify WebSocket URL format
4. [ ] Test PCM audio streaming
5. [ ] Tune chunk size and throttle rate
6. [ ] Test barge-in/interrupt
7. [ ] Test Chinese language support
8. [ ] Deploy backend to server
9. [ ] Stress test for 30+ minute sessions
