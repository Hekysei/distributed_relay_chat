from src.connection_handler import ConnectionHandler
from src.relay.dispatcher.dispatcher_interface import DispatcherInterface
from src.relay.message_factory import make_system_message
from src.package.package import Message, TimestampResponse, SystemMessage
from src.package_handler.active_package_handler import ActivePackageHandler
from src.relay.relay_bot import RelayBot

CHAT_PREFIX_LENGTH = 2
ROOM_CHAT_PREFIX = "c/"
DIRECT_CHAT_PREFIX = "u/"


class ClientHandler(ActivePackageHandler):
    def __init__(
        self,
        dispatcher: DispatcherInterface,
        connection_handler: ConnectionHandler,
        relay_bot: RelayBot,
    ):
        super().__init__(connection_handler)

        self.dispatcher = dispatcher

        self.bot = relay_bot
        self.user_code = ""

    async def run(self):
        await self.on_start()
        await self.connection_handler.run()
        await self.on_end()

    async def on_start(self):
        self.user_code, _ = await self.dispatcher.add_user(self.send_message)
        await self.send_text_to_client("Welcome to relay")
        await self.send_text_to_client(f"Your relay code is {self.user_code}")
        await self._send_auto_moderator_direct_message()

    async def on_end(self):
        if self.user_code:
            await self.dispatcher.remove_user(self.user_code)

    ### HANDLERS ###
    async def on_msg(self, msg: Message):
        msg.set_timestamp_now()
        msg.sender = self.username

        await self.send_tsr(TimestampResponse.from_message(msg))

        chat_prefix = msg.chat[:CHAT_PREFIX_LENGTH]

        if msg.chat == self.bot.chat_name:
            await self._handle_bot_message(msg)
        elif chat_prefix == DIRECT_CHAT_PREFIX:
            await self._handle_direct_message(msg)
        elif chat_prefix == ROOM_CHAT_PREFIX:
            await self._handle_room_message(msg)
        else:
            await self._handle_unsupported_prefix(msg, chat_prefix)

    async def _handle_bot_message(self, msg: Message):
        await self.bot.async_on_text_for(self, msg.text)

    async def _handle_direct_message(self, msg: Message):
        recipient_code = msg.chat[CHAT_PREFIX_LENGTH:]
        res = await self.dispatcher.direct_message(self.user_code, recipient_code, msg)
        if not res.ok:
            await self._send_error_message(msg.chat, res.format_error())

    async def _handle_room_message(self, msg: Message):
        res = await self.dispatcher.broadcast(self.user_code, msg)
        if not res.ok:
            await self._send_error_message(msg.chat, res.format_error())

    async def _handle_unsupported_prefix(self, msg: Message, prefix: str):
        await self._send_error_message(msg.chat, f"Unsupported chat prefix: {prefix}")

    async def _send_error_message(self, chat: str, text: str):
        await self.send_message(
            make_system_message(
                chat=chat,
                sender=self.bot.bot_name,
                text=text,
            )
        )

    async def on_sys_msg(self, sys_msg: SystemMessage):
        if sys_msg.msg_type == "set_username":
            await self.set_username(sys_msg.body)

    async def send_text_to_client(self, text: str):
        await self.send_message(
            make_system_message(
                chat=self.bot.chat_name,
                sender=self.bot.bot_name,
                text=text,
            )
        )

    async def _send_auto_moderator_direct_message(self):
        moderator_code = await self.dispatcher.get_moderator_code()
        if not moderator_code:
            return
        await self.send_message(
            make_system_message(
                chat=f"{DIRECT_CHAT_PREFIX}{moderator_code}",
                sender="moderator",
                text=(
                    "Welcome! This is an automatic direct message from the moderator."
                ),
            )
        )

    async def set_username(self, name: str):
        self.username = name
        await self.send_text_to_client(f"Your name is {self.username}")
