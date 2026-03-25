#!/usr/bin/env python3

import asyncio
import websockets
import json
import signal
import sys

connected_clients = set()


async def echo_handler(websocket: websockets.ServerConnection):
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
    finally:
        print("Client disconnected")
        connected_clients.remove(websocket)


async def main():
    async with websockets.serve(echo_handler, "0.0.0.0", 1409):
        print("Server started on 0.0.0.0:1409. Press Ctrl+C to stop.")

        loop = asyncio.get_running_loop()
        stop_future = loop.create_future()

        try:
            loop.add_signal_handler(signal.SIGINT, stop_future.set_result, None)
            loop.add_signal_handler(signal.SIGTERM, stop_future.set_result, None)
        except Exception as e:
            print("Can't set signal")
            print(e)
            return

        await stop_future

        print("Closing all client connections...")
        await asyncio.gather(
            *[ws.close() for ws in connected_clients], return_exceptions=True
        )
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
