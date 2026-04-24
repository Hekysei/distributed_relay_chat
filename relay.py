#!/usr/bin/env python3

import asyncio

from src.relay.server import Server, ConnectionHandler
from src.relay.dispatcher.dispatcher import Dispatcher
from src.relay.dispatcher.proxy_dispatcher import ProxyDispatcher
from src.relay.client_handler import ClientHandler
from src.relay.relay_bot import RelayBot

class Relay:
    def __init__(self):
        self.server = Server()
        self.dispatcher = Dispatcher()
        self.proxy_dispatcher = ProxyDispatcher(self.dispatcher)
        self.bot = RelayBot(self.proxy_dispatcher)

        self.server.on_connection_callback = self.start_handler

    async def run(self):
        await self.server.run()

    async def start_handler(self, connection_handler: ConnectionHandler):
        client_handler = ClientHandler(self.proxy_dispatcher, connection_handler, self.bot)
        await client_handler.run()


if __name__ == "__main__":
    relay = Relay()
    asyncio.run(relay.run())
