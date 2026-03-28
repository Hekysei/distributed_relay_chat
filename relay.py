#!/usr/bin/env python3

import asyncio

from typing import Callable

from src.message import Message
from src.relay.server import Server, ConnectionHandler

RELAY_CHAT_NAME = "r/relay"


class ClientHandler:
    def __init__(
        self,
        connection_handler: ConnectionHandler,
        send_message_to_relay: Callable[[Message]],
    ):
        self.connection_handler = connection_handler
        self.send_message_to_client = connection_handler.send_message
        self.send_message_to_relay = send_message_to_relay

    async def run(self):
        await self.on_start()
        async for msg in self.connection_handler.recv_loop():
            await self.on_msg(msg)

    async def on_start(self):
        await self.send_text_to_client("Welcome to relay")

    async def on_msg(self, msg: Message):
        if msg.chat == RELAY_CHAT_NAME:
            await self.send_text_to_client("Got: " + msg.text)
        else:
            await self.send_message_to_relay(msg)

    async def send_text_to_client(self, text: str):
        await self.send_message_to_client(Message(RELAY_CHAT_NAME, "relay", text))


class Relay:
    def __init__(self):
        self.server = Server()
        self.server.on_connection_callback = self.start_handler
        self.handlers: set[ClientHandler] = set()
        self.rooms: dict[str, str] = {}

    async def run(self):
        await self.server.run()

    async def send_message(self, msg: Message):
        print(msg)

    async def start_handler(self, connection_handler: ConnectionHandler):
        client_handler = ClientHandler(connection_handler, self.send_message)

        self.handlers.add(client_handler)
        await client_handler.run()
        self.handlers.remove(client_handler)


if __name__ == "__main__":
    relay = Relay()
    asyncio.run(relay.run())
