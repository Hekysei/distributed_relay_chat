from src.message import Message

from typing import Callable

from src.bot import Bot

from src.relay.server import ConnectionHandler

from uuid import uuid4

class Room:
    def __init__(self):
        pass

# Dependency Injection
# Pub/Sub
class Dispatcher:
    def __init__(self):
        self.rooms: dict[str, Room] = {}
        self.handlers: set[ClientHandler] = set()

    async def send_message(self, msg: Message):
        print("send", msg)

    async def call(self, msg: Message):
        print("call", msg)


RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class ClientHandler:
    def __init__(
        self,
        dispatcher: Dispatcher,
        connection_handler: ConnectionHandler,
    ):
        uuid = str(uuid4())
        # while uuid in self.handlers:
        #     uuid = str(uuid4())
        self.uuid = uuid
        self.dispatcher = dispatcher
        self.connection_handler = connection_handler

        self.send_message_to_client = connection_handler.send_message

    async def run(self):
        await self.on_start()
        async for msg in self.connection_handler.recv_loop():
            await self.on_msg(msg)

    async def on_start(self):
        await self.send_text_to_client("Welcome to relay")

    async def on_msg(self, msg: Message):
        if msg.chat[:2] in ("r/", "m/"):
            msg.set_user_uuid(self.uuid)
        if msg.chat == RELAY_CHAT_NAME:
            await self.dispatcher.call(msg)
        else:
            await self.dispatcher.send_message(msg)

    async def send_text_to_client(self, text: str):
        await self.send_message_to_client(
            Message(RELAY_CHAT_NAME, RELAY_BOT_NAME, text)
        )
