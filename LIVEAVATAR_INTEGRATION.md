# LiveAvatar Integration Summary

**Date:** 2025-05-05
**Status:** ⚠️ Incomplete - Avatar not responding to voice input
**Credits Used:** ~125 credits during testing

## Overview

Attempted to integrate LiveAvatar as a replacement for D-ID AI avatar service. The goal was to create a kiosk AI concierge that could interact with users via voice.

## What Was Built

### Files Created
- `index-liveavatar.html` - Main kiosk application with LiveAvatar integration
- `test-liveavatar.html` - Simple test page for LiveAvatar
- `gemini-proxy/` - Proxy server for Gemini API calls (to avoid CORS)

### Technical Architecture

```
User → Microphone → LiveKit WebRTC → LiveAvatar API → Avatar Video
                              ↓
                         (STT + LLM + TTS)
```

## LiveAvatar Modes

### FULL Mode (Attempted)
- **What it does:** Handles STT, LLM, and TTS automatically
- **Configuration:**
  ```javascript
  {
    avatar_id: "513fd1b7-7ef9-466d-9af2-344e51eeb833",
    mode: "FULL",
    avatar_persona: {
      first_message: "Hello! I'm Kimberly...",
      system_prompt: "You are Kimberly, AI concierge..."
    }
  }
  ```
- **Requirement:** Must publish microphone audio to LiveKit

### CUSTOM Mode (Also Attempted)
- **What it does:** Only provides video streaming. No TTS.
- **Limitation:** Would need separate TTS service (ElevenLabs, browser TTS, etc.)

## Issues Encountered

### 1. Microphone Not Detected
```
Microphone audio level: 1.46 (should be >0 when speaking)
WARNING: Microphone level is very low! Check permissions.
```
- The microphone was being published but LiveKit detected silence
- This prevented FULL mode from working (avatar couldn't hear user)

### 2. API Endpoints Don't Exist
- `/v1/sessions/{id}/speak` → 404 Not Found
- `/v1/sessions/{id}/stream` → 404 Not Found
- Data channel events (`avatar.speak_text`, `conversation.chat`) were ignored

### 3. FULL Mode Greeting Not Triggering
- Even with `avatar_persona.first_message` set, avatar didn't greet automatically
- May require additional configuration or API calls

## What Works

✅ Session creation with LiveAvatar API
✅ LiveKit WebRTC connection
✅ Video stream received from avatar
✅ Microphone track published to LiveKit
✅ Web Speech API for transcription (when used)

## What Doesn't Work

❌ Avatar speaking (no TTS in CUSTOM mode)
❌ Avatar responding to voice (mic issue in FULL mode)
❌ Automatic greeting in FULL mode
❌ `/speak` and `/stream` API endpoints

## LiveAvatar API Details

### Endpoints Used
- `POST https://api.liveavatar.com/v1/sessions/token` - Create session
- `POST https://api.liveavatar.com/v1/sessions/start` - Start session

### Configuration Required
- `X-API-KEY` header with LiveAvatar API key
- Avatar ID, mode, video settings, voice ID
- For FULL mode: `avatar_persona` object

## Possible Next Steps

1. **Fix Microphone Issue**
   - Test microphone at https://webcammictest.com/
   - Check browser permissions
   - Try different audio constraints

2. **Contact LiveAvatar Support**
   - Ask why FULL mode isn't working
   - Get correct API documentation for CUSTOM mode
   - Ask about `/speak` or `/stream` endpoints

3. **Alternative Approaches**
   - Use D-ID (was working before)
   - Use ElevenLabs for TTS + LiveAvatar video only
   - Build custom TTS with browser Speech Synthesis API

4. **Debug Further**
   - Add more logging to see data channel messages
   - Test with a different avatar ID
   - Try LiveAvatar's official SDK if available

## References

- LiveAvatar API: https://api.liveavatar.com/v1
- LiveKit Client SDK: https://cdn.jsdelivr.net/npm/livekit-client@2.6.2/dist/livekit-client.umd.min.js
