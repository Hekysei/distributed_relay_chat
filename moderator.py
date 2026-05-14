#!/usr/bin/env python3

import argparse
import asyncio

from src.client.moderator_client import ModeratorClient


async def _amain() -> None:
    parser = argparse.ArgumentParser(description="Relay moderator client")
    parser.add_argument("--host", default="localhost", help="Relay WebSocket host")
    parser.add_argument(
        "--port",
        type=int,
        default=12021,
        help="Relay WebSocket port (must match relay server)",
    )
    args = parser.parse_args()

    moderator = ModeratorClient()
    await moderator.run_net(args.host, str(args.port))


if __name__ == "__main__":
    asyncio.run(_amain())
