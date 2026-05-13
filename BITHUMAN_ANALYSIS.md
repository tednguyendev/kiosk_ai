# bithuman Analysis & Decision Record

## TL;DR

**bithuman was evaluated and rejected** for the Kopitiam kiosk project.

- Local Python SDK: memory leaks, no native voice, requires dedicated server
- Cloud via LiveKit: requires third-party streaming service, complex architecture
- iframe embed: no custom UI possible

**Decision: Use Anam** (already in `index.html`) — single API, full SaaS, works on static hosting.

---

## What bithuman Offers

### 7 Runtime Surfaces

| # | Surface | Custom UI? | Needs Server? | Needs LiveKit? | Best For |
|---|---------|-----------|---------------|----------------|----------|
| 1 | **Cloud (LiveKit)** | ✅ Yes | Agent worker | ✅ Yes | Full custom web apps |
| 2 | **Cloud (Embed/iframe)** | ❌ No | ❌ No | ❌ No | Quick website integration |
| 3 | **Cloud (REST API)** | ⚠️ Control only | ❌ No | ❌ No | Trigger speech in sessions |
| 4 | **Local Python SDK** | ✅ Yes | ✅ Yes (4GB+ RAM) | ❌ No | On-prem, edge, kiosks |
| 5 | **GPU Docker** | ✅ Yes | ✅ Yes (NVIDIA) | ❌ No | High-quality dynamic faces |
| 6 | **Swift SDK** | ✅ Yes | ❌ No | ❌ No | Native Apple apps |
| 7 | **Halo / CLI** | ❌ No | ❌ No | ❌ No | Personal use, demos |

### For Web Kiosk: Only 2 Allow Full Custom UI

1. **LiveKit + cloud** — WebRTC streams
2. **Local Python SDK** — MJPEG + WebSocket

---

## Detailed Findings

### 1. Local Python SDK (`AsyncBithuman`)

**What we built:** `bithuman-server/kiosk_server.py` + `index-bithuman.html`

**Architecture:**
```
User speech → Whisper API → Gemini → OpenAI TTS → bithuman runtime
                                               ↓
                                    MJPEG stream + WebSocket audio
                                               ↓
                                          Browser
```

**Problems discovered:**

| Problem | Root Cause | Severity |
|---------|-----------|----------|
| **No native voice** | `AsyncBithuman` only does lip-sync, no TTS | Critical |
| **Lip-sync looks off** | TTS audio is "too clean" for Essence model | High |
| **A/V sync flaky** | MJPEG + WebSocket are independent transports | High |
| **Memory leaks** | Cython runtime leaks frame buffers on macOS | High |
| **Needs 4GB+ RAM** | Essence model minimum spec | High |
| **No bithuman voice** | `bithuman_local_voice` doesn't exist on PyPI | Critical |
| **Audio chunk artifacts** | WebSocket PCM chunk boundaries | Medium |
| **Port conflicts** | Auto-restart wrapper spawns multiple instances | Low |

**Attempted fixes:**
- `output_buffer_size=2`, `PRELOAD_TO_MEMORY=false`, `FPS=15` — reduced memory but didn't eliminate leaks
- 400ms jitter buffer — improved sync but added latency
- Dithering noise (`std=1e-4`) on TTS audio — marginal lip-sync improvement
- Auto-restart wrapper with RSS monitor — band-aid for memory leaks

**Deployment attempt:** Deployed to Hetzner VPS (4GB RAM). Server froze because Rails apps + bithuman exceeded RAM capacity. Required 8GB minimum or dedicated server.

**Verdict:** ❌ Rejected. Too complex, no native voice, operational nightmare.

---

### 2. Cloud via LiveKit Plugin

**What we built:** Branch `livekit-bithuman-cloud` (`livekit-agent.py`, `livekit-token-server.py`, `livekit-kiosk.html`)

**Architecture:**
```
Browser ──WebRTC──→ LiveKit Cloud Room ←── bithuman Cloud Avatar
                         ↑
                    Agent Worker (Python)
                    - OpenAI STT
                    - OpenAI LLM
                    - OpenAI TTS
                    - bithuman AvatarSession
```

**Problems discovered:**

| Problem | Root Cause | Severity |
|---------|-----------|----------|
| **Requires LiveKit Cloud** | bithuman offloaded streaming to LiveKit | Critical |
| **Requires agent worker** | You must run Python worker 24/7 | High |
| **Requires token server** | Frontend needs JWT tokens for LiveKit | High |
| **Still no bithuman voice** | Uses OpenAI TTS, bithuman only does video | Critical |
| **Two separate bills** | LiveKit + bithuman | Medium |
| **Previous ngrok failure** | Local LiveKit + ngrok free tier doesn't work | High |
| **Three services stitched** | OpenAI + LiveKit + bithuman | High |

**Why not just "call an API" like Anam:**

| Aspect | Anam | bithuman LiveKit |
|--------|------|-----------------|
| STT | ✅ Built-in | ❌ You bring OpenAI |
| LLM | ✅ Built-in | ❌ You bring OpenAI |
| TTS/Voice | ✅ Built-in | ❌ You bring OpenAI |
| Lip-sync | ✅ Built-in | ✅ bithuman does this |
| Streaming | ✅ Built-in | ❌ You bring LiveKit |
| API calls | 1 | 3 services |

bithuman is a **component** (lip-sync engine), not an **end-to-end product** like Anam.

**Verdict:** ❌ Rejected. Adds complexity without solving the voice problem.

---

### 3. iframe / Chat Widget / Web Gadget

**Architecture:**
```
Your Website → bithuman iframe/widget → bithuman handles everything
```

**What it offers:**
- Zero backend
- Works on Netlify
- bithuman handles STT + LLM + TTS + lip-sync internally
- Native bithuman voice (this is the only surface with it!)

**Customizable:**
- Theme (light/dark)
- Theme color (8 presets)
- Greeting/welcome messages
- Suggested questions
- Chat mode (text/voice/video)
- Avatar model (essence/expression)

**NOT customizable:**
- Layout/positioning
- Fonts
- Chat bubble styles
- Custom UI panels (restaurant data, stall listings)
- Circular avatar crop
- Exact brand colors
- Full-screen kiosk layout

**Verdict:** ⚠️ Not suitable. Cannot match Kopitiam kiosk design.

---

## Key Technical Findings

### bithuman Has No Standalone TTS

The Python `AsyncBithuman` class methods:
- `create`, `push_audio`, `run`, `process`, `flush`, `start`, `stop`
- **No `speak`, `synthesize`, or TTS method**

The `bithuman_local_voice` package is referenced in `plugins/stt.py` but **does not exist on PyPI**.

Native bithuman voice only exists in:
- **Swift SDK** (`bitHumanKit`) — Apple Silicon M3+ only
- **Halo macOS app** — closed-source desktop app
- **Cloud iframe/embed** — full SaaS mode

### Cloud `/speak` Endpoint Requires Active Session

`POST /v1/agent/{code}/speak` — "Triggers the agent to speak a message to users in the session."

Error code: `404 NO_ACTIVE_ROOMS` — no standalone generation. Requires an active room/session.

### Token-Based Licensing (Local Runtime)

Even though inference runs locally, bithuman validates API secrets via cloud tokens:
- `request_token()` calls `api.bithuman.ai`
- `start_token_refresh()` runs background heartbeat
- `is_token_validated()` checks license status
- Credits deducted per active minute

This is "local inference + cloud licensing" — common in AI SDKs.

---

## Comparison: bithuman vs Anam vs LiveAvatar vs Tavus

| Feature | bithuman Local | bithuman Cloud | Anam | LiveAvatar | Tavus |
|---------|---------------|----------------|------|------------|-------|
| **Custom UI** | ✅ Yes | ⚠️ LiveKit only | ✅ Yes | ✅ Yes | ✅ Yes |
| **Native voice** | ❌ No | ⚠️ Embed only | ✅ Yes | ✅ Yes | ✅ Yes |
| **One API call** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Static hosting** | ❌ No | ⚠️ Embed only | ✅ Yes | ✅ Yes | ✅ Yes |
| **Lip-sync quality** | ⚠️ TTS-confused | ✅ Good | ✅ Good | ✅ Good | ✅ Good |
| **A/V sync** | ⚠️ Flaky | ✅ WebRTC | ✅ WebRTC | ✅ WebRTC | ✅ WebRTC |
| **Ops burden** | 🔴 High | 🟡 Medium | 🟢 Low | 🟢 Low | 🟢 Low |
| **Monthly cost** | bithuman credits | bithuman + LiveKit | Anam credits | LiveAvatar credits | Tavus credits |

---

## Decision

**Use Anam** for the Kopitiam kiosk.

**Rationale:**
- Single API, single vendor
- Full custom UI possible
- Native voice included
- Deploys to Netlify (static hosting)
- No server management
- No memory leaks
- No A/V sync hacks

**Current state:** `index.html` is already the Anam integration. Ready to deploy.

---

## Files in This Branch

| File | Purpose | Status |
|------|---------|--------|
| `index.html` | **Anam version — active** | ✅ Use this |
| `index-anam.html` | Same as `index.html` | ✅ Reference |
| `index-bithuman.html` | bithuman local experiment | ❌ Archived |
| `bithuman-server/` | Python backend for local bithuman | ❌ Archived |
| `livekit-agent.py` | LiveKit agent worker | ❌ Archived |
| `livekit-token-server.py` | LiveKit JWT token server | ❌ Archived |
| `livekit-kiosk.html` | LiveKit frontend | ❌ Archived |
| `test-bithuman.html` | Test page | ❌ Archived |
| `test-chinese.html` | Whisper QA test | ✅ Keep |
| `test-tts-quality.html` | TTS comparison | ❌ Archived |

---

## References

- bithuman docs: https://docs.bithuman.ai
- LiveKit Cloud: https://cloud.livekit.io
- Anam SDK: https://docs.anam.ai
- Pricing: bithuman 1 cr/min (Essence self-hosted), 2 cr/min (Essence cloud)
