#!/usr/bin/env python3

import asyncio
import websockets
import signal

from message import Message, json_to_message, message_to_json

from typing import Callable


class ClientHandler:
    def __init__(self, send_message: Callable[[Message]], relay_call):
        self.relay_chat_name = "r/relay"
        self.send_message = send_message
        self.relay_call = relay_call

    async def on_start(self):
        await self.send_direct_text("Welcome to relay")

    async def on_msg(self, msg: Message):
        if msg.chat == self.relay_chat_name:
            await self.send_direct_text("Got: " + msg.text)
        else:
            await self.relay_call(msg)

    async def send_direct_text(self, text: str):
        await self.send_message(Message(self.relay_chat_name, "relay", text))


class Relay:
    def __init__(self):
        pass

    def on_message(self, msg: Message):
        pass


class Server:
    def __init__(self):
        self.relay = Relay()
        self.active_connections: set[websockets.ServerConnection] = set()

    async def handler_factory(self, ws: websockets.ServerConnection):
        self.active_connections.add(ws)

        async def send_message(msg: Message):
            await ws.send(message_to_json(msg))

        handler = ClientHandler(send_message, self.relay.on_message)
        await handler.on_start()

        try:
            async for data in ws:
                data: str | bytes
                await handler.on_msg(json_to_message(data))
        except Exception as e:
            print(e)

        await ws.close()
        self.active_connections.remove(ws)
        print("Client disconnected")

    async def run(self):
        async with websockets.serve(self.handler_factory, "localhost", 1409):
            print("Server started. Press Ctrl+C to stop.")

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

            await self.close_active_connections()

    async def close_active_connections(self):
        if self.active_connections:
            print(f"Closing {len(self.active_connections)} active connections...")
            close_tasks = [ws.close() for ws in self.active_connections]
            await asyncio.gather(*close_tasks, return_exceptions=True)


if __name__ == "__main__":
    relay = Server()
    asyncio.run(relay.run())
