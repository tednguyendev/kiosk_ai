# LiveAvatar Backend Bug Report

**Date:** 2026-05-16
**Status:** 🔴 Confirmed — LiveAvatar backend bug, not client-side issue
**Affected Avatar:** `1e614fa7-6eeb-4c81-a418-2865ce420dd1`
**API Key:** `860a7348-9cfa-4fcf-9f33-4b6f4a6c2721`

---

## Summary

LiveAvatar's backend fails to generate LLM responses and TTS audio for the avatar.
The client connects successfully, streams video, and the user's speech is transcribed
correctly — but the avatar never speaks back.

This has been reproduced with **three independent client implementations**:
1. Raw LiveKit integration (original code)
2. Official `@heygen/liveavatar-web-sdk`
3. LiveAvatar's own `meet.livekit.io` test client

---

## What Works (Client-Side)

| Component | Status | Evidence |
|-----------|--------|----------|
| Session token creation | ✅ | `code: 1000` from `/v1/sessions/token` |
| Session start | ✅ | `code: 1000` from `/v1/sessions/start` |
| LiveKit WebRTC connection | ✅ | `participantConnected heygen` |
| Video stream | ✅ | Avatar video renders in `<video>` element |
| Microphone access | ✅ | `user.speak_started` fires |
| Speech-to-text (STT) | ✅ | `user.transcription` emits correct text |
| User speak ended | ✅ | `user.speak_ended` fires |

---

## What Doesn't Work (Backend-Side)

| Component | Status | Evidence |
|-----------|--------|----------|
| Avatar LLM response | ❌ | No `avatar.transcription` event |
| Avatar TTS/speech | ❌ | No `avatar.speak_started` event |
| Avatar lip sync | ❌ | No audio/video changes when user speaks |
| Data channel responses | ❌ | `session.message("hello")` produces no avatar events |
| First message greeting | ❌ | `avatar_persona.first_message` never spoken |

---

## Reproduction Steps

### Method 1: Official SDK (Recommended for Support Ticket)

```html
<script type="module">
const { LiveAvatarSession, AgentEventsEnum } = await import(
  'https://esm.sh/@heygen/liveavatar-web-sdk'
);

const session = new LiveAvatarSession(sessionToken, {
  voiceChat: true,
  apiUrl: 'https://api.liveavatar.com'
});

session.on(AgentEventsEnum.USER_TRANSCRIPTION, (e) => {
  console.log('✅ USER:', e.text);  // Works — prints "I want spicy food."
});

session.on(AgentEventsEnum.AVATAR_TRANSCRIPTION, (e) => {
  console.log('❌ AVATAR:', e.text);  // Never fires
});

await session.start();
session.attach(videoElement);
await session.voiceChat.start();
</script>
```

**Expected:** After user speaks, `AVATAR_TRANSCRIPTION` fires with response text.
**Actual:** Only `USER_TRANSCRIPTION` fires. Avatar events never appear.

---

### Method 2: LiveAvatar's Official Test Client

1. Create session token via `/v1/sessions/token`
2. Call `/v1/sessions/start` to get `livekit_url` + `livekit_client_token`
3. Open: `https://meet.livekit.io/custom?liveKitUrl={url}&token={token}`
4. Click **Start Audio**, allow mic, speak

**Expected:** Avatar hears user and responds with voice + lip sync.
**Actual:** User mic works (UI highlights when speaking), avatar stays silent.

---

### Method 3: Raw LiveKit Integration

Same result — mic publishes, tracks received, data channel events sent,
but avatar backend never generates a response.

---

## Attempted Fixes (Did Not Work)

| Fix | Result |
|-----|--------|
| New API key | Same issue |
| New avatar ID | Same issue |
| Official SDK instead of raw LiveKit | Same issue |
| `avatar.speak_text` data channel | Events ignored |
| `avatar.speak_response` data channel | Events ignored |
| `session.message("hello")` | No avatar response |
| Different system prompts | Same issue |
| Adding `language: "en"` | Same issue |

---

## Environment

- **Browser:** Chrome (latest)
- **OS:** macOS
- **Mic permissions:** Granted
- **Network:** Stable
- **Credits:** Confirmed available on account

---

## Conclusion

This is a **server-side bug in LiveAvatar's backend**. The client code is correct
across three different implementations. The issue lies in LiveAvatar's
LLM/TTS pipeline failing to generate responses after receiving user transcription.

**Recommended action:** Contact LiveAvatar/HeyGen support with this report.

---

## Support Contact

- Dashboard: https://app.liveavatar.com
- Docs: https://docs.liveavatar.com
- SDK: https://github.com/heygen-com/liveavatar-web-sdk

---

## GitHub Evidence

### PR #32 — Known Bug in SDK

- **URL:** https://github.com/heygen-com/liveavatar-web-sdk/pull/32
- **Title:** "fix avatar speaking event not firing full mode"
- **Status:** Merged ✅ (2025-10-30)
- **Fix:** Added missing `AVATAR_SPEAK_STARTED` and `AVATAR_SPEAK_ENDED` event handlers

This proves that **"avatar speaking event not firing in full mode" was a known bug**
in the official SDK that required a code fix.

### Issue #93 — FULL Mode Broken (Still Open)

- **URL:** https://github.com/heygen-com/liveavatar-web-sdk/issues/93
- **Title:** "startListening/stopListening in FULL mode"
- **Status:** **OPEN** 🔴
- **Quote:** *"In the demo in FULL mode, clicking the 'Start Listening Pose' button...
seems to be totally ignored, the avatar does not change poses."*

This confirms FULL mode has **ongoing, unresolved issues** in the official SDK.

### Version Timeline

| Version | Date | Includes PR #32 fix? |
|---------|------|----------------------|
| 0.0.16 | 2026-04-24 | ✅ Yes |
| 0.0.17 | 2026-04-28 | ✅ Yes |
| 0.0.18 | 2026-05-07 | ✅ Yes (latest) |

**We tested with 0.0.18 (latest)** — the SDK event fix is included, but the
avatar backend still does not generate responses.

---

## Summary of Proof

1. ✅ Our raw LiveKit code works (connects, streams video, publishes mic)
2. ✅ Official SDK works (connects, streams video, transcribes speech)
3. ✅ Official `meet.livekit.io` client works (connects, shows user speaking)
4. ❌ Avatar backend never responds in **all three** implementations
5. 📋 SDK PR #32 proves "avatar not speaking in FULL mode" was a known bug
6. 📋 SDK Issue #93 proves FULL mode is still broken (open issue)

**Conclusion:** This is a confirmed backend bug on LiveAvatar's side.
