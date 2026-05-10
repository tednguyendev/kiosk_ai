import asyncio
import numpy as np
from bithuman import AsyncBithuman

async def main():
    runtime = await AsyncBithuman.create(
        model_path="avatar.imx",
        api_secret="dOIQCNkA6HbqHDvh5JqzKIhr1Cku48P4SzLBlXicA39XED7vdUDFPBh3lMCbt37Gy"
    )
    # Don't call start() - let the frame producer thread handle it
    # Actually we need start() to begin producing frames
    
    count = 0
    async for frame in runtime.run():
        print(f"Frame type: {type(frame)}")
        print(f"  frame_index: {frame.frame_index}")
        print(f"  has_image: {frame.has_image}")
        print(f"  end_of_speech: {frame.end_of_speech}")
        print(f"  source_message_id: {frame.source_message_id}")
        
        if frame.has_image:
            rgb = frame.rgb_image
            print(f"  rgb_image type: {type(rgb)}")
            if isinstance(rgb, np.ndarray):
                print(f"  rgb_image shape: {rgb.shape}, dtype: {rgb.dtype}")
                print(f"  rgb_image min/max: {rgb.min()}/{rgb.max()}")
            else:
                print(f"  rgb_image: {rgb}")
        
        if frame.audio_chunk is not None:
            audio = frame.audio_chunk
            print(f"  audio_chunk type: {type(audio)}")
            if isinstance(audio, np.ndarray):
                print(f"  audio_chunk shape: {audio.shape}, dtype: {audio.dtype}")
                print(f"  audio_chunk min/max: {audio.min()}/{audio.max()}")
        
        count += 1
        if count >= 3:
            break
    
    print("Done")

asyncio.run(main())
