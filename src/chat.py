from abc import ABC

from src.package.package import Message, TimestampResponse
from src.bot import Bot
from src.connection_handler import ConnectionHandler


class Chat(ABC):
    def __init__(self, name):
        self.name = name
        self.messages: list[Message] = []

    def add_message(self, msg: Message):
        self.messages.append(msg)

    async def send_message(self, msg: Message):
        self.add_message(msg)


class ChatBot(Chat):
    def __init__(self, name, bot_name):
        super().__init__(name)
        self.bot = Bot(name, bot_name, self.add_message)

    def add_commands(self, commands: list):
        self.bot.add_commands(commands)

    async def send_message(self, msg: Message):
        msg.set_timestamp_now()
        await super().send_message(msg)
        self.bot.on_text(msg.text)


class RemoteChat(Chat):
    def __init__(self, name, net_client: ConnectionHandler):
        super().__init__(name)
        self.net_client = net_client

        self.messages_wait_for_sync: dict[int, Message] = dict()
        self.messages_sync_count = 0

    async def send_message(self, msg: Message):
        await super().send_message(msg)

        self.messages_sync_count += 1
        msg.message_id = self.messages_sync_count
        self.messages_wait_for_sync[self.messages_sync_count] = msg

        await self.net_client.send_message(msg)

    def on_tsr(self, tsr: TimestampResponse):
        self.messages_wait_for_sync.pop(tsr.message_id).timestamp = tsr.timestamp
