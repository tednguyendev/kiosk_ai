import asyncio
import os
from bithuman import AsyncBithuman

async def main():
    print("Loading model...")
    runtime = await AsyncBithuman.create(
        model_path="avatar.imx",
        api_secret=os.environ.get("BITHUMAN_API_SECRET", "")
    )
    print("Model loaded! Starting runtime...")
    await runtime.start()
    print("Runtime started!")
    print(f"Frame size: {runtime.get_frame_size()}")
    
    # Generate 1 second of frames (25 FPS)
    print("Generating 25 frames...")
    count = 0
    async for frame in runtime.run():
        count += 1
        if count >= 25:
            break
    print(f"Generated {count} frames successfully!")

asyncio.run(main())
