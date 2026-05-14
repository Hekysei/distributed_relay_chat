#!/usr/bin/env python3

import argparse
import asyncio

from src.connection_handler import ConnectionHandler
from src.relay.server import Server
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

    async def run(self, host: str = "0.0.0.0", port: int = 12021):
        await self.server.run(host, port)

    async def start_handler(self, connection_handler: ConnectionHandler):
        client_handler = ClientHandler(self.proxy_dispatcher, connection_handler, self.bot)
        await client_handler.run()


async def _amain() -> None:
    parser = argparse.ArgumentParser(description="Relay WebSocket server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Listen address (default: all interfaces)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=12021,
        help="WebSocket port (use the same value in moderator.py and clients)",
    )
    args = parser.parse_args()

    relay = Relay()
    await relay.run(host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(_amain())
