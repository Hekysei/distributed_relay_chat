#!/usr/bin/env python3

import asyncio
import websockets

from typing import Callable

from message import Message, json_to_message, message_to_json
from server import Server


class ConnectionHandler:
    def __init__(self, ws: websockets.ServerConnection):
        self.ws = ws

    async def recv_loop(self):
        try:
            async for data in self.ws:
                data: str | bytes
                yield json_to_message(data)
        except Exception as e:
            print(e)

    async def send_message(self, msg: Message):
        await self.ws.send(message_to_json(msg))


class ClientHandler:
    def __init__(self, relay_call: Callable[[Message]]):
        self.connection_handler: ConnectionHandler
        self.relay_chat_name = "r/relay"

        self.relay_call = relay_call

    async def run(self, ws: websockets.ServerConnection):
        self.connection_handler = ConnectionHandler(ws)

        await self.on_start()
        async for msg in self.connection_handler.recv_loop():
            await self.on_msg(msg)

    async def on_start(self):
        await self.send_direct_text("Welcome to relay")

    async def on_msg(self, msg: Message):
        if msg.chat == self.relay_chat_name:
            await self.send_direct_text("Got: " + msg.text)
        else:
            await self.relay_call(msg)

    async def send_direct_text(self, text: str):
        await self.connection_handler.send_message(
            Message(self.relay_chat_name, "relay", text)
        )


class Relay:
    def __init__(self):
        self.server = Server()
        self.server.on_connection_callback = self.start_handler

    async def run(self):
        await self.server.run()

    async def on_message(self, msg: Message):
        print(msg)

    async def start_handler(self, ws: websockets.ServerConnection):
        client_handler = ClientHandler(self.on_message)
        await client_handler.run(ws)


if __name__ == "__main__":
    relay = Relay()
    asyncio.run(relay.run())
