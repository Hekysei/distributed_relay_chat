from typing import Callable, cast

from threading import Thread

import asyncio

from src.client.net_client import NetClient
from src.package.package import Message, TimestampResponse, SystemMessage
from src.package.package_factory import PackageFactory
from src.chat import RemoteChat, Chat


class Client:
    def __init__(self, package_factory: PackageFactory):
        self.username = "blank_name"
        self.chats: dict[str, Chat] = {}

        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        self.net_client = NetClient(package_factory)

        self.connection_thread: Thread | None = None

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def start_connection_thread(self, ip: str, port: str) -> bool:
        if self.net_client.is_connected():
            return False
        else:
            self.connection_thread = Thread(
                target=lambda: asyncio.run(self.run_net(ip, port))
            )
            self.connection_thread.start()
            return True

    async def run_net(self, ip: str, port: str):
        self.loop = asyncio.get_running_loop()
        await self.net_client.run(ip, port)

    def disconnect(self):
        asyncio.run_coroutine_threadsafe(self.net_client.disconnect(), self.loop)

    ### РАБОТА С ЧАТАМИ ###
    def add_chat(self, chat: Chat):
        self.chats[chat.name] = chat
        self.on_chat_added_callback()

    def create_chat(self, chat_name: str):
        self.add_chat(RemoteChat(chat_name, self.net_client))

    def remove_chat(self, chat_name):
        self.chats.pop(chat_name)
        self.on_chat_removed_callback()

    ### HANDLERS ###
    async def on_msg(self, msg: Message):
        if msg.chat not in self.chats:
            self.create_chat(msg.chat)
        self.chats[msg.chat].add_message(msg)
        self.on_message_callback()

    async def on_ts_response(self, tsr: TimestampResponse):
        cast(RemoteChat, self.chats[tsr.chat]).on_tsr(tsr)
        self.on_message_callback()

    async def on_sys_msg(self, sys_msg: SystemMessage):
        pass

    ### ОТПРАВКА ТЕКСТА ###
    def send_user_text(self, chat: str, text: str):
        msg = Message(
            chat=chat,
            sender=self.username,
            text=text,
        )
 
        asyncio.run(self.chats[chat].send_message(msg))
        self.on_message_callback()

    async def set_username(self, name: str):
        self.username = name
        if self.net_client.is_connected():
            await self.send_username()

    async def send_username(self):
        await self.net_client.send_sys_message(
            SystemMessage(msg_type="set_username", body=self.username)
        )
