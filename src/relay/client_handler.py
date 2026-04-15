from src.connection_handler import ConnectionHandler
from src.relay.dispatcher.dispatcher import Dispatcher
from src.package.package import Message, TimestampResponse, SystemMessage
from src.relay.relay_bot import RelayBot
from src.package_handler.active_package_handler import ActivePackageHandler


class ClientHandler(ActivePackageHandler):
    def __init__(
        self,
        dispatcher: Dispatcher,
        connection_handler: ConnectionHandler,
    ):
        super().__init__(connection_handler)

        self.dispatcher = dispatcher
        self.dispatcher

        self.bot = RelayBot(self)

    async def run(self):
        await self.on_start()
        await self.connection_handler.run()
        await self.on_end()

    async def on_start(self):
        await self.send_text_to_client("Welcome to relay")

    async def on_end(self):
        await self.dispatcher.remove_user(self.username)

    ### HANDLERS ###
    async def on_msg(self, msg: Message):
        msg.set_timestamp_now()
        msg.sender = self.username

        await self.send_tsr(TimestampResponse.from_message(msg))

        if msg.chat == self.bot.chat_name:
            await self.bot.async_on_text(msg.text)
        else:
            await self.dispatcher.broadcast(msg)

    async def on_sys_msg(self, sys_msg: SystemMessage):
        if sys_msg.msg_type == "set_username":
            await self.set_username(sys_msg.body)

    async def send_text_to_client(self, text: str):
        await self.send_message(
            Message(
                chat=self.bot.chat_name, sender=self.bot.bot_name, text=text
            ).set_timestamp_now()
        )

    async def set_username(self, name: str):
        self.username = name
        await self.send_text_to_client(f"Your name is {self.username}")
