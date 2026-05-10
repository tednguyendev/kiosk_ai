import asyncio
import inspect
from bithuman import AsyncBithuman

async def main():
    runtime = await AsyncBithuman.create(
        model_path="avatar.imx",
        api_secret="dOIQCNkA6HbqHDvh5JqzKIhr1Cku48P4SzLBlXicA39XED7vdUDFPBh3lMCbt37Gy"
    )
    await runtime.start()

    count = 0
    async for frame in runtime.run():
        print(f"Frame type: {type(frame)}")
        print(f"Frame dir: {[a for a in dir(frame) if not a.startswith('_')]}")
        if hasattr(frame, 'video'):
            print(f"  video type: {type(frame.video)}")
            if hasattr(frame.video, 'shape'):
                print(f"  video shape: {frame.video.shape}")
            if hasattr(frame.video, 'dtype'):
                print(f"  video dtype: {frame.video.dtype}")
        if hasattr(frame, 'audio'):
            print(f"  audio type: {type(frame.audio)}")
            if hasattr(frame.audio, 'shape'):
                print(f"  audio shape: {frame.audio.shape}")
            if hasattr(frame.audio, 'dtype'):
                print(f"  audio dtype: {frame.audio.dtype}")

        # Also check if it's a tuple
        if isinstance(frame, tuple):
            print(f"  Tuple length: {len(frame)}")
            for i, item in enumerate(frame):
                print(f"  [{i}] type: {type(item)}")
                print(f"  [{i}] dir: {[a for a in dir(item) if not a.startswith('_')]}")

        count += 1
        if count >= 3:
            break

    print("Done")

asyncio.run(main())
