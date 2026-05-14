import asyncio

from src.client.chat import ChatBot
from src.client.client import Client

GREETINGS = [
    "Welcome!",
    "Commands:",
    "/c, /connect - connect to relay",
    "/d - disconnect",
    "/name - set username",
]


class ClientChatBot(ChatBot):
    def __init__(self, client: Client):
        super().__init__("c/client", "client")

        CONNECT_ARGS = {"ip": "localhost", "port": "12021"}
        CLIENT_COMMANDS = [
            ("/connect", client.start_connection_thread, CONNECT_ARGS),
            ("/c", client.start_connection_thread, CONNECT_ARGS),
            ("/d", client.disconnect, {}),
            (
                "/name",
                client.set_username,
                {
                    "name": "",
                },
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)

        asyncio.run(self.greet())

    async def greet(self):
        for greet in GREETINGS:
            await self.bot.async_send_text(greet)
