#!/usr/bin/env python3

import asyncio
from uuid import uuid4, UUID

from typing import Callable

from src.message import Message
from src.relay.server import Server, ConnectionHandler

RELAY_CHAT_NAME = "r/relay"


class ClientHandler:
    def __init__(
        self,
        uuid: str,
        connection_handler: ConnectionHandler,
        send_message_to_relay: Callable[[Message]],
        relay_call: Callable[[Message]],
    ):
        self.uuid = uuid
        self.connection_handler = connection_handler
        self.send_message_to_client = connection_handler.send_message
        self.send_message_to_relay = send_message_to_relay
        self.relay_call = relay_call

    async def run(self):
        await self.on_start()
        async for msg in self.connection_handler.recv_loop():
            await self.on_msg(msg)

    async def on_start(self):
        await self.send_text_to_client("Welcome to relay")

    async def on_msg(self, msg: Message):
        if msg.chat[:2] in ("r/","m/"):
            msg.set_user_uuid(self.uuid)
        if msg.chat == RELAY_CHAT_NAME:
            await self.relay_call(msg)
        else:
            await self.send_message_to_relay(msg)

    async def send_text_to_client(self, text: str):
        await self.send_message_to_client(Message(RELAY_CHAT_NAME, "relay", text))


class Relay:
    def __init__(self):
        self.server = Server()
        self.server.on_connection_callback = self.start_handler
        self.handlers: dict[str, ClientHandler] = {}
        self.rooms: dict[str, str] = {}

    async def run(self):
        await self.server.run()

    async def send_message(self, msg: Message):
        print(msg)

    async def relay_call(self, msg: Message):
        if (msg.text):
            pass

    async def start_handler(self, connection_handler: ConnectionHandler):
        uuid = str(uuid4())
        while uuid in self.handlers:
            uuid = str(uuid4())

        client_handler = ClientHandler(
            uuid, connection_handler, self.send_message, self.relay_call
        )

        self.handlers[uuid] = client_handler
        await client_handler.run()
        self.handlers.pop(uuid)


if __name__ == "__main__":
    relay = Relay()
    asyncio.run(relay.run())
