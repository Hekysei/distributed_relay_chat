from typing import Callable

from net_client import NetClient
from message import Message
from chat_bot import ChatBot

from threading import Thread



class Client:
    def __init__(self):
        self.user_name = "blank_name"
        self.chats: dict[str, list[Message]] = {}

        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        self.chat_bot = ChatBot("c/client", "client", self.send_text)
        self.net_client = NetClient(self.chat_bot.chat_name)

        self.__setup_chat_bot()

        self.connection_thread: Thread | None = None

    def __setup_chat_bot(self):
        connect_args = {"ip": "localhost", "port": "1409"}
        self.chat_bot.add_command(
            "/connect", self.start_connection_thread, connect_args
        )
        self.chat_bot.add_command("/c", self.start_connection_thread, connect_args)

        self.chat_bot.add_command("/d", self.stop, {})

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def connect_to_relay(self, ip: str, port: str):
        if not self.net_client.connect(ip, port):
            self.send_text_to_user("Connection refused")
            return
        self.send_text_to_user("Connected")
        for msg in self.net_client.recv_loop():
            msg: Message
            self.__add_message(msg)
        self.send_text_to_user("Сonnection lost")

        for chat_name in list(self.chats.keys()):
            if chat_name != self.chat_bot.chat_name:
                self.remove_chat(chat_name)

    def stop(self):
        if self.net_client.ws.connected:
            self.net_client.ws.close()

    ### РАБОТА С ЧАТАМИ ###
    def add_chat(self, chat_name):
        self.chats[chat_name] = []
        self.on_chat_added_callback()

    def remove_chat(self, chat_name):
        self.chats.pop(chat_name)
        self.on_chat_removed_callback()

    ### ДОБАВЛЕНИЕ СООБЩЕНИЯ В ЧАТ ###
    def __add_message(self, msg: Message):
        if msg.chat not in self.chats:
            self.add_chat(msg.chat)
        self.chats[msg.chat].append(msg)
        self.on_message_callback()

    ### ОТПРАВКА ТЕКСТА ###
    def send_text(self, chat: str, author: str, text: str):
        msg = Message(chat, author, text)
        self.__add_message(msg)

        if not chat.startswith("c/") and not self.net_client.send(msg):
            self.send_text_to_user("No server")

    def send_user_text(self, chat: str, text: str):
        if chat == self.chat_bot.chat_name:
            self.chat_bot.on_text(text)
        self.send_text(chat, self.user_name, text)

    def send_text_to_user(self, text: str):
        self.chat_bot.send_text(text)

    def start_connection_thread(self, ip: str, port: str):
        if self.connection_thread and self.connection_thread.is_alive():
            self.send_text_to_user("Already connected")
        else:
            self.connection_thread = Thread(
                target=self.connect_to_relay, args=(ip, port)
            )
            self.connection_thread.start()
