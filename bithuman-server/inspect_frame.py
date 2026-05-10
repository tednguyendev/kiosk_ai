import asyncio
import numpy as np
from bithuman import AsyncBithuman

async def main():
    runtime = await AsyncBithuman.create(
        model_path="avatar.imx",
        api_secret="dOIQCNkA6HbqHDvh5JqzKIhr1Cku48P4SzLBlXicA39XED7vdUDFPBh3lMCbt37Gy"
    )
    await runtime.start()
    
    count = 0
    async for frame in runtime.run():
        count += 1
        print(f"Frame type: {type(frame)}")
        if hasattr(frame, 'video'):
            print(f"  video shape: {frame.video.shape}, dtype: {frame.video.dtype}")
        if hasattr(frame, 'audio'):
            print(f"  audio shape: {frame.audio.shape}, dtype: {frame.audio.dtype}")
        if hasattr(frame, '__dict__'):
            print(f"  attrs: {list(frame.__dict__.keys())}")
        if count >= 3:
            break
    print(f"Inspected {count} frames")

asyncio.run(main())
