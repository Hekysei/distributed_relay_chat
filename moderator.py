#!/usr/bin/env python3

import argparse
import asyncio

from src.client.client import Client
from src.package.package import Message, SystemMessage

RELAY_BOT_CHAT = "r/relay"
USER_DIRECT_PREFIX = "u/"


class ModeratorClient(Client):
    def __init__(self):
        super().__init__()

    async def on_connected(self):
        self.username = "moderator"
        await super().on_connected()
        await self._send_user_text(RELAY_BOT_CHAT, "/mod")
        print(
            "Moderator session started. Users can message you via m/moderator; ",
            "when someone sends 'login', this client asks the relay to verify their code."
        )

    async def _send_user_text(self, chat: str, text: str):
        msg = Message(
            chat=chat,
            sender=self.username,
            text=text,
            message_id=0,
        )
        await self.send_message(msg)

    async def on_msg(self, msg: Message):
        line = msg.text.replace("\n", " ").strip()
        print(f"[{msg.chat}] {msg.sender}: {line}")

        if msg.chat.startswith(USER_DIRECT_PREFIX) and line.lower() == "login":
            user_code = msg.chat[len(USER_DIRECT_PREFIX) :]
            print(f"Asking relay to verify user {user_code}.")
            await self._send_user_text(RELAY_BOT_CHAT, f"/verify {user_code}")

    # async def on_sys_msg(self, sys_msg: SystemMessage):
    #     if sys_msg.msg_type == "set_username":
    #         await self.set_username(sys_msg.body)
    #         return
    #     print(f"[system {sys_msg.msg_type}] {sys_msg.body}")


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
