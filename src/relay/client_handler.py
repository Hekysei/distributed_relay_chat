from uuid import uuid4

from src.bot import Bot
from src.relay.server import ConnectionHandler
from src.relay.dispatcher import Dispatcher
from src.package.package import Message, TimestampResponse, SystemMessage

RELAY_CHAT_NAME = "r/relay"
RELAY_BOT_NAME = "relay"


class RelayBot(Bot):
    def __init__(self, client_handler):
        super().__init__(
            RELAY_CHAT_NAME, RELAY_BOT_NAME, client_handler.send_message_to_client
        )

        async def create_channel(name):
            await client_handler.dispatcher.create_channel(
                name, client_handler.username, client_handler.send_message_to_client
            )

        async def join_channel(name):
            await client_handler.dispatcher.subscribe(
                name, client_handler.username, client_handler.send_message_to_client
            )

        name_kwargs = {
            "name": "blank_name",
        }
        CLIENT_COMMANDS = [
            (
                "/create",
                create_channel,
                name_kwargs,
            ),
            (
                "/join",
                join_channel,
                name_kwargs,
            ),
            (
                "/name",
                client_handler.set_username,
                name_kwargs,
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)


class ClientHandler:
    def __init__(
        self,
        dispatcher: Dispatcher,
        connection_handler: ConnectionHandler,
    ):
        self.username = "empty"

        self.dispatcher = dispatcher
        self.dispatcher

        self.connection_handler = connection_handler
        self.send_message_to_client = connection_handler.send_message
        self.send_tsr_to_client = connection_handler.send_tsr

        self.bot = RelayBot(self)

    async def run(self):
        await self.on_start()
        async for msg in self.connection_handler.recv_loop():
            await self.on_msg(msg)

    async def on_start(self):
        await self.send_text_to_client("Welcome to relay")
        await self.set_username(str(uuid4()))

    async def on_msg(self, msg: Message):
        msg.set_timestamp_now()
        msg.sender = self.username

        await self.send_tsr_to_client(TimestampResponse.from_message(msg))

        if msg.chat == RELAY_CHAT_NAME:
            await self.bot.async_on_text(msg.text)
        else:
            await self.dispatcher.send_message(msg, self.send_message_to_client)

    async def send_text_to_client(self, text: str):
        await self.send_message_to_client(
            Message(
                chat=RELAY_CHAT_NAME, sender=RELAY_BOT_NAME, text=text
            ).set_timestamp_now()
        )

    async def send_username_to_client(self):
        await self.connection_handler.send_sys_message(
            SystemMessage(msg_type="set_username", body=self.username)
        )

    async def set_username(self, name: str):
        self.username = name
        await self.send_text_to_client(f"Your name is {self.username}")
        await self.send_username_to_client()
