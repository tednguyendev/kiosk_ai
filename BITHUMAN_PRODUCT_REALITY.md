# bithuman Product Reality Check

> Date: 2026-05-11  
> Branch: `heygen-realtime` (analysis spans `liveavatar-attempt`, `bithuman-cloud-livekit`, `livekit-bithuman-cloud`)  
> Status: **Key finding — bithuman "Cloud" may not exist as a verified product**

## TL;DR

We assumed bithuman offered **two** products: **Local** (Python SDK) and **Cloud** (LiveKit plugin).  
**In reality, we only verified one.** The "Cloud" path was built from documentation assumptions, not working code.

This discovery explains why the bithuman branches were abandoned and validates the pivot to HeyGen LiveAvatar.

---

## The Assumption Tree (What We Believed)

From bithuman's documentation and marketing materials, we understood their product matrix as:

| # | Surface | Custom UI? | Needs Server? | Source |
|---|---------|-----------|---------------|--------|
| 1 | **Cloud (LiveKit)** | ✅ Yes | Agent worker | bithuman docs |
| 2 | **Cloud (Embed/iframe)** | ❌ No | ❌ No | bithuman docs |
| 3 | **Cloud (REST API)** | ⚠️ Control only | ❌ No | bithuman docs |
| 4 | **Local Python SDK** | ✅ Yes | ✅ Yes (4GB+ RAM) | Verified |
| 5 | **GPU Docker** | ✅ Yes | ✅ Yes (NVIDIA) | bithuman docs |
| 6 | **Swift SDK** | ✅ Yes | ❌ No | bithuman docs |
| 7 | **Halo / CLI** | ❌ No | ❌ No | bithuman docs |

We treated #1 and #4 as equally real. **They are not.**

---

## Verified Products (We Touched Them)

### 1. Local Python SDK (`AsyncBithuman`)

**Evidence:**
- Installed via `pip install bithuman`
- Imported `AsyncBithuman` from `bithuman` package
- Loaded `avatar.imx` (83MB Essence model) into memory
- Called `push_audio()`, `flush()`, `start()` successfully
- Served MJPEG stream via `StreamServer`
- Pushed OpenAI TTS audio and observed lip-sync output

**Code:** `bithuman-server/kiosk_server.py` + `index-bithuman.html`

**Problems discovered (all real):**
- No native TTS in Python SDK (`AsyncBithuman` only lip-syncs external audio)
- ~1.8GB RAM usage (Essence model + runtime)
- Memory leaks on macOS (Cython frame buffer leaks)
- Flaky A/V sync (independent MJPEG + WebSocket transports)
- Server froze on Hetzner 4GB VPS

**Status:** ✅ **Real product. Rejected due to operational issues.**

---

### 2. iframe / Embed Widget

**Evidence:**
- Documented in bithuman docs with configuration options
- Has a `/v1/agent/{code}/speak` REST endpoint
- Returns `404 NO_ACTIVE_ROOMS` when no session exists
- Pricing mentioned: "2 cr/min (Essence cloud)"

**What we know:**
- Zero backend required
- bithuman handles everything internally (STT + LLM + TTS + lip-sync)
- Customizable: theme, colors, greeting, avatar model
- **NOT** customizable: layout, fonts, chat bubbles, custom panels, full-screen kiosk

**Status:** ⚠️ **Real product, but unsuitable for custom kiosk UI.**

---

## Unverified Products (Assumed from Documentation)

### 3. "Cloud via LiveKit Plugin"

**What we built:**
- Branch `bithuman-cloud-livekit` (`livekit-agent.py`)
- Branch `livekit-bithuman-cloud` (`livekit-token-server.py`, `livekit-kiosk.html`)

**Code we wrote:**
```python
from livekit.plugins import bithuman, openai, silero

class KimberlyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=KOPITIAM_KB,
            stt=openai.STT(),
            vad=silero.VAD(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(voice="coral"),
        )
```

**Why it never ran:**
> "Never fully worked due to lack of LiveKit Cloud credentials"

**The real question: Does `livekit.plugins.bithuman` even exist?**

- **Never tested:** `pip install livekit-plugins-bithuman` — unknown if this package is on PyPI
- **Never imported successfully:** The `livekit-agent.py` was written *before* verifying the package exists
- **No working example:** No proof this integration was ever functional
- **bithuman SDK has `utils/agent.py`:** This file has LiveKit hooks, but it's for **publishing local frames to a LiveKit room**, not for connecting to a "bithuman Cloud" avatar

**Status:** ❓ **Unverified. May not exist as a real product.**

---

## Critical Distinction

| | What we thought | What is likely true |
|---|---|---|
| **bithuman "Cloud"** | A separate cloud-rendered avatar service | Probably just the **iframe/embed** (SaaS widget) |
| **LiveKit integration** | A first-class plugin for cloud avatars | Only exists for **local runtime publishing** (`utils/agent.py`) |
| **Two modes** | Local SDK vs Cloud service | One SDK (local) + one iframe (SaaS) |

The `bithuman/utils/agent.py` in the SDK is **not** a cloud connector. It's a bridge to publish **locally rendered frames** into a LiveKit room:

```python
# bithuman/utils/agent.py — LOCAL runtime frames → LiveKit room
class VideoOutput(ABC):
    async def capture_frame(self, frame: VideoFrame, ...): ...
```

This would still require the 1.8GB local runtime. It does **not** offload rendering to bithuman's cloud.

---

## Evidence Summary

| Claim | Evidence | Confidence |
|-------|----------|------------|
| Local Python SDK exists | We installed and ran it | ✅ Certain |
| iframe/embed exists | Documented, has REST endpoint | ⚠️ High (but never wired up) |
| Cloud LiveKit plugin exists | `livekit.plugins.bithuman` import in our code | ❓ Unknown — never installed |
| Cloud avatar rendering exists | Mentioned in docs/pricing | ❓ Unknown — never verified |
| `livekit-plugins-bithuman` on PyPI | Never checked | ❓ Unknown |

---

## Impact on Project Decisions

### Why bithuman branches were abandoned

| Branch | Reason for abandonment | Root cause |
|--------|----------------------|------------|
| `liveavatar-attempt` | Server froze, no native voice, A/V sync flaky | Local runtime limitations |
| `bithuman-cloud-livekit` | "No LiveKit credentials" | **Possibly chasing a non-existent product** |
| `livekit-bithuman-cloud` | ngrok failure, complex stitching | Built on unverified foundation |

### Why HeyGen is the correct next step

| Factor | bithuman (verified) | HeyGen LiveAvatar (verified) |
|--------|---------------------|------------------------------|
| Real product | ✅ Local SDK only | ✅ Full platform (docs, SDK, dashboard) |
| Custom UI | ✅ Yes (local) | ✅ Yes (LITE mode) |
| Full body | ✅ Yes | ✅ Avatar IV |
| Cloud rendering | ❌ Unverified | ✅ Verified (their core business) |
| npm SDK | ❌ No | ✅ `@heygen/liveavatar-web-sdk` |
| REST API testable | ❌ No (local only) | ✅ `curl api.liveavatar.com` |
| Pricing transparency | ⚠️ Partial | ✅ Clear credit system |

---

## Recommended Action

1. **Do not invest further in bithuman "Cloud" paths** until `livekit-plugins-bithuman` is verified to exist on PyPI and has working documentation.
2. **Test HeyGen first** — it has verifiable infrastructure (npm SDK, REST API, live dashboard).
3. **If HeyGen fails**, the fallback is not bithuman Cloud — it's either:
   - Anam (already works, face-only)
   - Tavus (stub exists, never tested)
   - A different provider entirely

---

## Appendix: How to Verify bithuman Cloud

If future teams want to check whether bithuman Cloud is real:

```bash
# Check if the LiveKit plugin exists
pip install livekit-plugins-bithuman

# Check if bithuman has a cloud REST API beyond iframe
curl -X POST https://api.bithuman.ai/v1/sessions \
  -H "Authorization: Bearer $BITHUMAN_API_KEY" \
  -d '{"avatar_id": "..."}'

# Check pricing for "cloud" vs "local"
# bithuman docs claimed: 1 cr/min (self-hosted), 2 cr/min (cloud)
```

Without successful responses to the above, treat bithuman Cloud as **unverified**.
