#!/usr/bin/env python3
"""
LiveKit Agent for Kopitiam Kiosk with bithuman Cloud Avatar.

Prerequisites:
  pip install livekit-agents livekit-plugins-bithuman livekit-plugins-openai livekit-plugins-silero
  export OPENAI_API_KEY=sk-...

Run:
  python livekit-agent.py dev
"""
import os

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import bithuman, openai, silero

# ─── Config ───
BITHUMAN_AGENT_ID = os.getenv("BITHUMAN_AGENT_ID", "A71DKA8910")
BITHUMAN_API_SECRET = os.getenv(
    "BITHUMAN_API_SECRET",
    "W8OWvGKO9P0kdF8dU2YBcPHKIw5iegMGSP8FvvGHFVlvdZAT1MQvB2ICDGsRg2ZHE",
)

# ─── Kopitiam Knowledge Base ───
KOPITIAM_KB = """\
You are Kimberly, a warm and friendly AI concierge at Kopitiam food court inside Tan Tock Seng Hospital (TTSH), Singapore.

About the food court:
- 405 seats, 21 food stalls
- Diners get 10% discount via FairPrice Group app + Linkpoints
- Located inside the hospital

Key stalls:
1. Kopi Kiosk – Drinks & Desserts. Signature Breakfast Set $3 (union member before 11am)
2. Ann Chin Popiah – Michelin Guide popiah since 1958
3. Bread Junction – Bakery (halal cert pending)
4. Kallang Airport Wanton Mee – Wanton noodles, crispy fried wantons
5. Teochew Pig Organ Soup – Authentic Teochew flavours
6. Yuan Wei Su Yu – Vegetarian, low oil/low salt/no MSG
7. Ying Jia Steamed Fish – Hotel chef recipe, garlic sauce seabass
8. Xiang Chi Mian – Bak Chor Mee (mince meat noodle)
9. He Jia Econ Rice – 10+ dishes daily, sweet & sour chicken
10. Yuan Wei Thai Cuisine – Tom Yum, basil minced pork
11. Bu Tang Wang Pepper Soup – ABC soup, white pepper chicken soup
12. King Grouper Fish Soup – Own fish farm in Changi, giant grouper 12kg+, Teochew style
13. Chinatown HK Roast – Roast duck, char siew, wanton noodles

Halal options: Bread Junction (cert pending), Yuan Wei Su Yu (vegetarian).
Spicy options: Yuan Wei Thai Cuisine, Xiang Chi Mian.
Healthy options: Yuan Wei Su Yu, Ying Jia Steamed Fish, Bu Tang Wang soups.
Fish specialty: King Grouper Fish Soup — farm-to-table, high collagen.

Keep responses short, cheerful, and helpful. Recommend specific dishes when asked.
"""


class KimberlyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=KOPITIAM_KB,
            stt=openai.STT(),
            vad=silero.VAD(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(voice="coral"),
        )


async def entrypoint(ctx: JobContext):
    print(f"[Agent] Job received for room: {ctx.room.name}")

    # Read env vars inside entrypoint (runs in separate process)
    lk_url = os.getenv("LIVEKIT_URL")
    if not lk_url:
        raise ValueError("LIVEKIT_URL env var required (e.g. wss://xxx.livekit.cloud)")
    lk_key = os.getenv("LIVEKIT_API_KEY")
    if not lk_key:
        raise ValueError("LIVEKIT_API_KEY env var required")
    lk_secret = os.getenv("LIVEKIT_API_SECRET")
    if not lk_secret:
        raise ValueError("LIVEKIT_API_SECRET env var required")
    bh_agent_id = os.getenv("BITHUMAN_AGENT_ID", "A71DKA8910")
    bh_api_secret = os.getenv(
        "BITHUMAN_API_SECRET",
        "W8OWvGKO9P0kdF8dU2YBcPHKIw5iegMGSP8FvvGHFVlvdZAT1MQvB2ICDGsRg2ZHE",
    )

    # Wait for the first participant (the user) to join
    await ctx.wait_for_participant()
    print("[Agent] User joined")

    # Create agent session
    agent_session = AgentSession()

    # Create bithuman cloud avatar session
    avatar_session = bithuman.AvatarSession(
        avatar_id=bh_agent_id,
        api_secret=bh_api_secret,
        model="essence",
    )

    # Start avatar (connects to room)
    await avatar_session.start(
        agent_session=agent_session,
        room=ctx.room,
        livekit_url=lk_url,
        livekit_api_key=lk_key,
        livekit_api_secret=lk_secret,
    )
    print("[Agent] bithuman cloud avatar started")

    # Start agent conversation
    agent = KimberlyAgent()
    print("[Agent] Starting conversation...")
    await agent_session.start(agent=agent, room=ctx.room)

    print("[Agent] Conversation ended")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
