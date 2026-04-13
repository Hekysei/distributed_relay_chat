from typing import Callable, cast

from threading import Thread

import asyncio

from src.package.package import Message, TimestampResponse

from src.chat import RemoteChat, Chat


from src.client.client import Client
from src.app.client_chat_bot import ClientChatBot





class UserClient(Client):
    def __init__(self):
        super().__init__()
        self.chats: dict[str, Chat] = {}

        self.chat_bot = ClientChatBot(self)
        self.add_chat(self.chat_bot)

        self.connection_thread: Thread | None = None

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    async def start_connection_thread(self, ip: str, port: str) -> bool:
        if self.connection_handler.is_connected():
            return False
        else:
            self.connection_thread = Thread(
                target=lambda: asyncio.run(self.run_net(ip, port))
            )
            self.connection_thread.start()
            return True

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
        self.chats[msg.chat].add_message(msg)

    async def on_tsr(self, tsr: TimestampResponse):
        cast(RemoteChat, self.chats[tsr.chat]).on_tsr(tsr)



class APPClient(UserClient):
    def __init__(self):
        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        super().__init__()

    def add_chat(self, chat: Chat):
        super().add_chat(chat)
        self.on_chat_added_callback()

    def remove_chat(self, chat_name):
        super().remove_chat(chat_name)
        self.on_chat_removed_callback()

    async def on_msg(self, msg: Message):
        await super().on_msg(msg)
        self.on_message_callback()

    async def on_ts_response(self, tsr: TimestampResponse):
        await super().on_tsr(tsr)
        self.on_message_callback()

    ### ОТПРАВКА ТЕКСТА ###
    def send_user_text(self, chat: str, text: str):
        msg = Message(
            chat=chat,
            sender=self.username,
            text=text,
        )
 
        asyncio.run(self.chats[chat].send_message(msg))
        self.on_message_callback()

    # def __send_text_to_user(self, text: str):
    #     self.chat_bot.bot.send_text(text)

    # def send_user_text(self, chat: str, text: str):
    #     super().send_user_text(chat, text)
    #     # if not res:
    #     #     self.__send_text_to_user("No server")

    # def start_connection_thread(self, ip: str, port: str) -> bool:
    #     res = super().start_connection_thread(ip, port)
    #     if not res:
    #         self.__send_text_to_user("Already connected")
    #     # else:
    #     #     self.__send_text_to_user(f"Start connecting to {ip}:{port}")
    #     return res

    # def connect_to_relay(self, ip: str, port: str) -> bool:
    #     res = super().connect_to_relay(ip, port)
    #     if res:
    #         self.__send_text_to_user("Connected")
    #     else:
    #         self.__send_text_to_user("Connection refused")
    #     return res

    async def run_net(self, ip, port):
        await super().run_net(ip, port)
        # self.__send_text_to_user("Сonnection lost")
    
        for chat_name in list(self.chats.keys()):
            if chat_name != self.chat_bot.name:
                self.remove_chat(chat_name)
