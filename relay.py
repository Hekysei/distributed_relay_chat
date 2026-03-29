#!/usr/bin/env python3

import asyncio

from src.relay.server import Server, ConnectionHandler
from src.relay.dispatcher import Dispatcher, ClientHandler


class Relay:
    def __init__(self):
        self.server = Server()
        self.dispatcher = Dispatcher()

        self.server.on_connection_callback = self.start_handler
        self.handlers: set[ClientHandler] = set()

    async def run(self):
        await self.server.run()

    async def start_handler(self, connection_handler: ConnectionHandler):

        client_handler = ClientHandler(self.dispatcher, connection_handler)

        self.handlers.add(client_handler)
        await client_handler.run()
        self.handlers.remove(client_handler)


if __name__ == "__main__":
    relay = Relay()
    asyncio.run(relay.run())
