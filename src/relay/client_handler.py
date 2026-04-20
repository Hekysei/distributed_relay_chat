from src.connection_handler import ConnectionHandler
from src.relay.dispatcher.dispatcher import DispatchCode, Dispatcher
from src.package.package import Message, TimestampResponse, SystemMessage
from src.package_handler.active_package_handler import ActivePackageHandler
from src.relay.relay_bot import RelayBot


class ClientHandler(ActivePackageHandler):
    def __init__(
        self,
        dispatcher: Dispatcher,
        connection_handler: ConnectionHandler,
        relay_bot: RelayBot,
    ):
        super().__init__(connection_handler)

        self.dispatcher = dispatcher
        self.dispatcher

        self.bot = relay_bot

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
            await self.bot.async_on_text_for(self, msg.text)
        elif msg.chat.startswith("u/"):
            recipient_username = msg.chat[2:]
            res = await self.dispatcher.direct_message(
                self.username, recipient_username, msg
            )
            if not res.ok:
                error_text = "Cannot send direct message"
                if res.code == DispatchCode.USER_NOT_VERIFIED:
                    error_text = "Verify first with /v before sending direct messages"
                elif res.code == DispatchCode.CANNOT_DIRECT_SELF:
                    error_text = "You cannot send direct messages to yourself"
                elif res.code == DispatchCode.NO_SUCH_USER:
                    error_text = (
                        f"Cannot send direct message to {recipient_username}: user is offline or unknown"
                    )
                await self.send_message(
                    Message(
                        chat=msg.chat,
                        sender=self.bot.bot_name,
                        text=error_text,
                    ).set_timestamp_now()
                )
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
