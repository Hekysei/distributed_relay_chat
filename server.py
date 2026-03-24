#!/usr/bin/env python3

import asyncio
import websockets
import json

connected_clients = set()


async def handler(websocket: websockets.ServerConnection):
    connected_clients.add(websocket)
    print("Client connected")
    response = {"status": "hii"}
    await websocket.send(json.dumps(response))
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            response = {"status": "ok", "received": data}
            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connected_clients.remove(websocket)


async def main():
    async with websockets.serve(handler, "0.0.0.0", 1409):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
