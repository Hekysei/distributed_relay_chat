import asyncio

from src.chat import RemoteChat, Chat
from src.client.client import Client
from src.client.client_chat_bot import ClientChatBot

from typing import cast

from src.package.package import Message, TimestampResponse


class UserClient(Client):
    def __init__(self):
        super().__init__()
        self.chats: dict[str, Chat] = {}

        self.chat_bot = ClientChatBot(self)
        self.add_chat(self.chat_bot)

    ### РАБОТА С ЧАТАМИ ###
    def add_chat(self, chat: Chat):
        self.chats[chat.name] = chat

    def create_chat(self, chat_name: str):
        self.add_chat(RemoteChat(chat_name, self.connection_handler))

    def remove_chat(self, chat_name):
        self.chats.pop(chat_name)

    ### HANDLERS ###
    async def on_msg(self, msg: Message):
        if msg.chat not in self.chats:
            self.create_chat(msg.chat)
        await self.chats[msg.chat].add_message(msg)

    async def on_tsr(self, tsr: TimestampResponse):
        cast(RemoteChat, self.chats[tsr.chat]).on_tsr(tsr)

    ### ОТПРАВКА ###
    async def send_text_to_user(self, text: str):
        await self.chat_bot.bot.async_send_text(text)

    async def send_user_message(self, msg: Message):
        await self.chats[msg.chat].send_message(msg)

    def send_user_text(self, chat: str, text: str):
        msg = Message(
            chat=chat,
            sender=self.username,
            text=text,
        )

        asyncio.run(self.send_user_message(msg))
