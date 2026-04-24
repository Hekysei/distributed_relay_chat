from src.relay.server import ConnectionHandler
from src.relay.dispatcher import Dispatcher
from src.package.package import Message, TimestampResponse, SystemMessage
from src.relay.relay_bot import RelayBot
from src.package.package_factory import PackageFactory


class RelayPackageFactory(PackageFactory):
    def __init__(self, connection_handler):
        self._handlers = {
            "message_request": connection_handler.on_msg,
            "system_message": connection_handler.on_sys_msg,
        }


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
        self.connection_handler.package_factory = RelayPackageFactory(self)
        self.send_message_to_client = connection_handler.send_message
        self.send_tsr_to_client = connection_handler.send_tsr

        self.bot = RelayBot(self)

    async def run(self):
        await self.on_start()
        await self.connection_handler.run()

    async def on_start(self):
        await self.send_text_to_client("Welcome to relay")

    async def on_msg(self, msg: Message):
        msg.set_timestamp_now()
        msg.sender = self.username

        await self.send_tsr_to_client(TimestampResponse.from_message(msg))

        if msg.chat == self.bot.chat_name:
            await self.bot.async_on_text(msg.text)
        else:
            await self.dispatcher.send_message(msg, self.send_message_to_client)

    async def on_sys_msg(self, sys_msg: SystemMessage):
        if sys_msg.msg_type == "set_username":
            await self.set_username(sys_msg.body)

    async def send_text_to_client(self, text: str):
        await self.send_message_to_client(
            Message(
                chat=self.bot.chat_name, sender=self.bot.bot_name, text=text
            ).set_timestamp_now()
        )

    async def set_username(self, name: str):
        self.username = name
        await self.send_text_to_client(f"Your name is {self.username}")
