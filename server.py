#!/usr/bin/env python3

import asyncio
import websockets
import json
import signal
import sys

from message import Message, json_to_message, message_to_json

connected_clients = set()


class ClientHandler:
    def __init__(self, websocket: websockets.ServerConnection):
        self.ws = websocket

    async def run(self):
        connected_clients.add(self)
        try:
            async for data in self.ws:
                await self.handle_recv(data)
        finally:
            print("Client disconnected")
            await self.close()

    async def handle_recv(self, data: str | bytes):
        msg = json_to_message(data)
        print(msg)
        await self.send_direct_message(msg.text)

    async def send_direct_message(self, text: str):
        await self.ws.send(message_to_json(Message("server", "relay", text)))

    async def close(self):
        connected_clients.remove(self)
        await self.ws.close()


async def echo_handler(websocket: websockets.ServerConnection):
    print("Client connected")
    response = {"status": "hii"}
    await websocket.send(json.dumps(response))


async def connection_factory(websocket):
    handler = ClientHandler(websocket)
    await handler.run()


async def main():
    async with websockets.serve(connection_factory, "0.0.0.0", 1409):
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
            *[client.close() for client in connected_clients], return_exceptions=True
        )
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
