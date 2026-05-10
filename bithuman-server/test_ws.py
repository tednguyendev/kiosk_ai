import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8766/ws'
    async with websockets.connect(uri) as ws:
        # Send ping
        await ws.send(json.dumps({'action': 'ping'}))
        resp = await asyncio.wait_for(ws.recv(), timeout=5)
        print('Response:', resp)
        
        # Wait for a frame
        data = await asyncio.wait_for(ws.recv(), timeout=10)
        print('Frame received, type:', type(data), 'size:', len(data))
        
        # Send speak
        await ws.send(json.dumps({'action': 'speak', 'text': 'Hello world'}))
        print('Sent speak')
        
        # Wait for frames after speak
        for i in range(5):
            data = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f'Frame {i}, size:', len(data))

asyncio.run(test())
