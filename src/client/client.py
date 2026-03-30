from typing import Callable

from threading import Thread


from src.client.net_client import NetClient
from src.message import Message
from src.chat import Chat


from datetime import datetime


class Client:
    def __init__(self):
        self.user_name = "blank_name"
        self.chats: dict[str, Chat] = {}

        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        self.net_client = NetClient()

        self.connection_thread: Thread | None = None

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def connect_to_relay(self, ip: str, port: str) -> bool:
        if self.net_client.connect(ip, port):
            return True
        return False

    def recv_loop(self):
        for msg in self.net_client.recv_loop():
            msg: Message
            self.__add_message(msg)

    def start_connection_thread(self, ip: str, port: str) -> bool:
        if self.net_client.ws.connected:
            return False
        else:
            if self.connect_to_relay(ip, port):
                self.connection_thread = Thread(target=self.recv_loop)
                self.connection_thread.start()
            return True

    def disconnect(self):
        self.net_client.disconnect()

    ### РАБОТА С ЧАТАМИ ###
    def add_chat(self, chat: Chat):
        self.chats[chat.name] = chat
        self.on_chat_added_callback()

    def create_chat(self, chat_name: str):
        self.add_chat(Chat(chat_name))

    def remove_chat(self, chat_name):
        self.chats.pop(chat_name)
        self.on_chat_removed_callback()

    ### ДОБАВЛЕНИЕ СООБЩЕНИЯ В ЧАТ ###
    def __add_message(self, msg: Message):
        if msg.chat not in self.chats:
            self.create_chat(msg.chat)
        self.chats[msg.chat].send_message(msg)
        self.on_message_callback()

    ### ОТПРАВКА ТЕКСТА ###
    def send_user_text(self, chat: str, text: str) -> bool:
        msg = Message(
            chat=chat,
            sender=self.user_name,
            text=text,
            message_id="1",
            timestamp=datetime.now(),
        )
        self.__add_message(msg)
        if msg.chat.startswith("c/"):
            return True
        return self.net_client.send(msg)
