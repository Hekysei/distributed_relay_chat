from src.message import Message

from typing import Callable

from src.bot import Bot

from src.relay.server import ConnectionHandler

from uuid import uuid4


class Channel:
    def __init__(self):
        self.members_funcs: dict[str, Callable[[Message]]] = dict()

    async def send_message(
        self, msg: Message, sender_func: Callable[[Message]] | None = None
    ):
        for func in self.members_funcs.values():
            if func != sender_func:
                await func(msg)

    def subscribe(self, username: str, send_func: Callable[[Message]]):
        self.members_funcs[username] = send_func

    def unsubscribe(self, username: str):
        self.members_funcs.pop(username)


# Dependency Injection
# Pub/Sub
class Dispatcher:
    def __init__(self):
        self.chanels: dict[str, Channel] = {}
        self.handlers: set[ClientHandler] = set()

    async def send_message(self, msg: Message, sender_func: Callable[[Message]]):
        await self.chanels[msg.chat].send_message(msg, sender_func)

    async def subscribe(
        self, channel_name: str, username: str, send_func: Callable[[Message]]
    ):
        self.chanels[channel_name].subscribe(username, send_func)
        await self.chanels[channel_name].send_message(
            Message(channel_name, RELAY_BOT_NAME, f"{username} has entered the chat.")
        )

    async def unsubscribe(self, channel_name: str, username: str):
        self.chanels[channel_name].unsubscribe(username)

    async def create_channel(
        self, channel_name: str, username: str, send_func: Callable[[Message]]
    ):
        self.chanels[channel_name] = Channel()
        await self.subscribe(channel_name, username, send_func)

    async def call(self, msg: Message):
        print("call", msg)


RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, client_handler):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, client_handler.send_message_to_client
        )

        async def create_channel(name):
            await client_handler.dispatcher.create_channel(
                name, client_handler.uuid, client_handler.send_message_to_client
            )

        async def join_channel(name):
            await client_handler.dispatcher.subscribe(
                name, client_handler.uuid, client_handler.send_message_to_client
            )

        channel_name_kwargs = {
            "name": "new_channel",
        }
        CLIENT_COMMANDS = [
            (
                "/create",
                create_channel,
                channel_name_kwargs,
            ),
            (
                "/join",
                join_channel,
                channel_name_kwargs,
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)


class ClientHandler:
    def __init__(
        self,
        dispatcher: Dispatcher,
        connection_handler: ConnectionHandler,
    ):
        uuid = str(uuid4())

        self.uuid = uuid
        self.dispatcher = dispatcher
        self.connection_handler = connection_handler
        self.send_message_to_client = connection_handler.send_message

        self.bot = RelayBot(self)

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
            await self.bot.async_on_text(msg.text)
        else:
            await self.dispatcher.send_message(msg, self.send_message_to_client)

    async def send_text_to_client(self, text: str):
        await self.send_message_to_client(
            Message(RELAY_CHAT_NAME, RELAY_BOT_NAME, text)
        )
