# Real-Time 3D Full-Body Avatar Provider Analysis

**Date:** 2026-05-06  
**Project:** Kiosk AI — Avatar Integration  
**Requirements:** 3D (not photorealistic real people) + Full Body + Real-time Streaming + Custom Image Upload

---

## Executive Summary

After evaluating **all major real-time avatar providers**, no single turnkey service meets **all four** hard requirements at an accessible price point. The market bifurcates sharply:

| Segment | Providers | Body | 3D | Custom Upload | Price | Time-to-deploy |
|---------|-----------|------|----|---------------|-------|----------------|
| Face-only streaming | Anam, D-ID, Tavus, Hedra, LiveAvatar | ❌ Face/upper | Mixed | ✅ | $–$$$ | Minutes–days |
| Enterprise full-body | Soul Machines, RAVATAR | ✅ Full | ✅ 3D digital human | ⚠️ Custom build | $$$$$ | Weeks–months |
| Custom build | Ready Player Me + Three.js | ✅ Full | ✅ 3D | ✅ Photo→avatar | Free avatar + dev time | Days–weeks |

---

## 1. Soul Machines (soulmachines.com)

### Overview
Pioneer in "Digital Humans." Combines cognitive modeling + embodied cognition (patented "Experiential AI™") to create lifelike, emotionally responsive 3D avatars. Their avatars exhibit **facial micro-expressions, gestures, empathy, and natural body language** — genuinely impressive technology.

### Body & Visual Style
- **Full body:** ✅ Yes — their digital humans render full body with natural gestures and movement
- **3D / animated:** ✅ Yes — fully 3D rendered, not photorealistic video of a real person
- **Visual quality:** Industry-leading for expressive facial animation and emotional depth

### Custom Avatar Creation
- **Method:** "Digital DNA Blender" — a web-based tool to blend phenotypes (face types), features, clothing, etc.
- **From photo upload:** ❌ **No direct photo-to-avatar** — you **blend features** in their DNA Blender, not upload a single image and get an auto-generated avatar
- **Workflow:** Creative-team-led bespoke builds for enterprise clients; or self-serve DNA blending in Studio
- **Build time:** 30+ minutes for DNA Blender publishes; **months** for bespoke custom digital humans
- **Note:** Their Taras Shevchenko case study used MetaHuman + neural networks from a painting, not a simple photo upload

### Real-time Streaming
- ✅ Yes — real-time WebRTC streaming of full-body 3D avatar
- Emotionally responsive — avatar reacts with empathy, facial expressions, gestures
- Can be deployed web, kiosk, holographic displays

### Pricing

#### Soul Machines Studio (Developer/Self-Serve)
| Plan | Price | Minutes | Avatars | Notes |
|------|-------|---------|---------|-------|
| Free | $0 | 0 min | 1 | Exploration only |
| Basic | $1,069/yr | 480 min/yr | 1 | Experimentation |
| Plus | ~$2,700/yr | 4,200 min/yr | 3 | Validation |
| Pro | $29,160/yr | 120,000 min/yr | 6 | Scaling |
| Pro + Premium | $34,160/yr | 120,000 min/yr | 6 | + workflow integrations |

#### Digital Workforce (Enterprise)
- **$40,000/year** for 6 digital workers + 120,000 conversation minutes
- Custom enterprise contracts reported in **low-to-mid six figures annually**
- Professional services billed on top

### Integration
- SDK available (typically delivered with professional services)
- LLM-agnostic (GPT, custom LLMs)
- Web, kiosk, holographic display support
- Not truly self-serve API-first like Anam

### Pros
- ✅ Best-in-class emotional expressiveness and facial animation
- ✅ Full body with natural gestures
- ✅ 3D (not real people)
- ✅ Enterprise security (SOC 2, etc.)
- ✅ Proven at scale (Mercedes-Benz, P&G, Nestlé)

### Cons
- ❌ **No simple photo-to-avatar upload** — requires DNA blending or bespoke creative build
- ❌ Expensive for a prototype/demo ($1,069+/year minimum)
- ❌ Long deployment timeline (weeks–months for custom avatars)
- ❌ Not self-serve API-first; more of a creative services engagement
- ❌ At Pro tier ($29K/yr) you still only get 6 avatars

---

## 2. RAVATAR (ravatar.com)

### Overview
Platform for real-time interactive 3D AI avatars, digital humans, and holographic displays. Strong focus on **info kiosks, holographic displays (RAVABOX/HOLWALL), and live events**. Full-body 3D avatars with lip-sync, gesture, and real-time AI conversation.

### Body & Visual Style
- **Full body:** ✅ Yes — explicitly states "full-body AI Avatars"
- **3D / animated:** ✅ Yes — 3D rendered digital humans with true-to-life movements
- **Visual quality:** Professional, lifelike but not photorealistic video. Good for kiosk/event use cases.

### Custom Avatar Creation
- **Method:** Two paths:
  1. **Stock avatars** — pre-designed, customizable immediately
  2. **Fully custom avatars** — built from scratch by RAVATAR team
- **From photo upload:** ⚠️ **Partial** — for custom avatars, you work with their team. Their Taras Shevchenko case used "an iconic 1840 self-portrait using MetaHuman and neural network technology" — implies a creative/technical process, not a simple "upload photo → get avatar" self-serve flow
- **Workflow:** Contact form → scoping → estimate → agreement → prepayment → development → deployment
- **Build time:** 1–2 weeks for PoC, 2–4 weeks for MVP, 4+ weeks for full solution

### Real-time Streaming
- ✅ Yes — real-time full HD streaming
- Web widget, mobile app, messenger, holographic display, **AI kiosk**
- Supports 4K holographic output
- Multi-language support

### Pricing

#### Subscription (Cloud-hosted, per-avatar project)
| Plan | Price | Concurrent | Minutes/Month |
|------|-------|------------|---------------|
| Basic | €199/mo | 1 avatar | 1,900 min |
| Business | €499/mo | 4 avatars | 4,900 min |
| Corporate | €999/mo | 8 avatars | 9,800 min |
| Enterprise | Custom | Custom | 10,000+ min |

- **Discounts:** 10% for 1-year, 20% for 2-year commitments
- **Self-service portal:** Was planned for Q1 2025 GA release

#### Custom Development
- **Starting at €5,000** for PoC or MVP
- Final cost based on scope, quality, features
- Includes custom avatar design, AI integration, voice cloning

#### Holographic Displays
- RAVABOX (holobox) and RAVAWALL (holographic wall)
- Pricing: contact for quote (sale or rental)

### Integration
- Website widget (voice + text)
- REST API / SDK
- Integrates with public LLMs, TTS, STT
- Custom/on-premise AI services (Enterprise)
- RAG for knowledge base training
- CRM, Salesforce, ServiceNow integrations

### Pros
- ✅ Full body ✅ 3D ✅ Real-time
- ✅ Explicitly supports **AI kiosk** use case (matches your project!)
- ✅ More affordable entry point than Soul Machines (€199/mo)
- ✅ On-premise deployment option for security
- ✅ Holographic display support (future-proof)
- ✅ Multi-language out of the box

### Cons
- ❌ **No self-serve photo-to-avatar** — custom avatars require contacting their team
- ❌ Custom avatar build is €5,000+ and takes weeks
- ❌ Subscription is **per-avatar project** — each avatar needs its own subscription
- ❌ European timezone company (potential support latency)
- ❌ Self-service portal may still not have launched

---

## 3. Head-to-Head: Soul Machines vs RAVATAR

| Criteria | Soul Machines | RAVATAR |
|----------|---------------|---------|
| **Full body** | ✅ Yes | ✅ Yes |
| **3D / animated** | ✅ Yes (digital human) | ✅ Yes (digital human) |
| **Real-time streaming** | ✅ Yes | ✅ Yes |
| **Custom image upload** | ❌ DNA Blender only | ❌ Team-led custom build |
| **Self-serve** | ⚠️ Studio has limits | ⚠️ Subscription only, custom = contact |
| **Price (minimum viable)** | $1,069/yr (480 min) | €199/mo (~$2,388/yr, 1,900 min) |
| **Custom avatar cost** | $$$$ (enterprise) | €5,000+ |
| **Time to custom avatar** | Months | 2–4 weeks (MVP) |
| **Kiosk-ready** | ✅ Yes | ✅ Yes (explicitly) |
| **Emotional depth** | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Good |
| **API-first** | ❌ Services-led | ⚠️ Widget + API |

---

## 4. Assessment Against Your 4 Requirements

| Requirement | Soul Machines | RAVATAR |
|-------------|---------------|---------|
| **1. 3D (not real people)** | ✅ Fully 3D digital human | ✅ Fully 3D digital human |
| **2. Full body visible** | ✅ Yes with natural gestures | ✅ Yes with movements |
| **3. Real-time streaming** | ✅ Yes, WebRTC | ✅ Yes, WebRTC |
| **4. Custom image upload** | ❌ **No** — DNA Blender or bespoke | ❌ **No** — team build from reference |

**Critical Finding:** Neither provider offers a simple "upload your photo → get a real-time 3D full-body avatar" self-serve workflow. Both require either:
- Blending features manually (Soul Machines DNA Blender)
- Working with their creative team (both, for true custom looks)
- Using neural network / MetaHuman pipelines from reference images (RAVATAR's case studies)

This is fundamentally different from Anam's "upload one photo → avatar in minutes" workflow.

---

## 5. Alternative: The "Custom Build" Path

If you absolutely need **all 4 requirements** and can invest dev time:

### Ready Player Me + Three.js + Lip Sync
1. **Upload photo** → Ready Player Me API generates 3D full-body `.glb` avatar (free)
2. **Render** in browser with Three.js
3. **Animate** mouth using audio viseme analysis (e.g., Rhubarb Lip Sync, Oculus Lipsync)
4. **Drive** with your existing Whisper → Gemini → TTS pipeline

**Pros:** ✅ Meets ALL 4 requirements, total cost = $0 (avatar creation), full control  
**Cons:** ❌ 2–3 days dev work, lip-sync quality < Anam/D-ID, no natural body gestures without mocap  
**Risk:** Medium — lip sync is achievable but won't be as polished as dedicated avatar platforms

### Inworld AI + Ready Player Me
- Inworld AI uses Ready Player Me for full-body 3D avatars
- Real-time AI conversations with emotional expression
- BUT: gaming-focused, complex integration, may not fit kiosk use case cleanly

---

## 6. Recommendations

### For Your PM Demo (Immediate)

**Option A: Stick with Anam (Recommended)**
- Anam is 3D, custom-uploadable from a single photo, real-time, and **already works**
- The stream is face-only, but the underlying avatar model is full-body
- For the demo: explain this is v1, and full-body rendering is a v2 upgrade
- **Cost:** Already integrated, minimal additional work
- **Risk:** Low — proven working system

**Option B: Use Anam + CSS trick**
- Try `object-fit: contain` with a portrait-oriented container
- Some Anam avatars have versions like `cara-4-3` (4:3 aspect ratio)
- May show more upper body/shoulders, but still won't show full body

### For Full-Body 3D (Post-Demo)

**If budget allows (€5,000–€10,000):**
- **RAVATAR** is the better fit for a kiosk project
- They explicitly support AI kiosks
- More affordable entry (€199/mo subscription + €5,000 custom build)
- 2–4 week MVP timeline
- Contact them with your reference image to discuss photo-to-avatar feasibility

**If budget is constrained:**
- **Custom build** with Ready Player Me + Three.js
- Invest 2–3 days of development
- Full control, meets all requirements
- Trade-off: lower animation quality than enterprise platforms

### If You Must Have Full Body for the Demo

**Fastest path:** RAVATAR PoC (€5,000, 1–2 weeks) OR Soul Machines Studio Pro ($29K/yr — overkill).

Given your timeline pressure for a PM demo, **the pragmatic choice is Anam for now, with a documented plan to evaluate RAVATAR for v2**.

---

## 7. Contact Information

### Soul Machines
- Website: https://www.soulmachines.com
- Studio: https://www.soulmachines.com/soul-machines-studio
- Pricing: https://www.soulmachines.com/studio-pricing
- Support: https://support.soulmachines.com

### RAVATAR
- Website: https://ravatar.com
- Pricing: https://ravatar.com/pricing/
- Genesis Studio: https://ravatar.com/docs/ai-avatar-studio-pricing/
- Contact form: Available on website

---

## Appendix: Full Provider Landscape

| Provider | 3D | Full Body | Real-time | Custom Image | Price | Notes |
|----------|----|-----------|-----------|--------------|-------|-------|
| **Anam** | ❌ 2D video | ❌ Face-only | ✅ | ✅ Photo→avatar | $/min | **Best integrated, but NOT 3D** |
| **D-ID** | ❌ 2D video | ❌ Face | ✅ | ✅ | $$ | Stable baseline |
| **Tavus** | ❌ 2D video | ❌ Upper | ✅ | ❌ | $$$ | Real people |
| **Hedra** | ❌ 2D/3D? | ❌ Face | ✅ | ✅ | Free tier | Face-focused |
| **LiveAvatar** | ⚠️ | ❌ | ✅ | ✅ | $$ | Mic bug, abandoned |
| **Azure TTS Avatar** | ❌ 2D video | ⚠️ Half | ✅ | ❌ | $$ | Needs training video |
| **Soul Machines** | ✅ 3D | ✅ | ✅ | ❌ DNA blend | $$$$$ | Enterprise, months |
| **RAVATAR** | ✅ 3D | ✅ | ✅ | ❌ Team build | $$$$ | Kiosk-focused |
| **Inworld AI** | ✅ 3D | ✅ | ✅ | ✅ via RPM | ? | Gaming focus |
| **Ready Player Me** | ✅ 3D | ✅ | N/A | ✅ Photo→avatar | Free | Creation only |
| **Synthesia** | ❌ 2D video | ⚠️ | ❌ | ✅ | $$ | Batch video, not real-time |
| **HeyGen** | ❌ 2D video | ⚠️ | ❌ | ✅ | $$ | Batch + streaming beta |
