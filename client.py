from typing import Callable

from net_client import NetClient
from message import Message

from threading import Thread

greetings = [
    "Welcome! Commands:",
    "/connect - connect to relay",
]


class Client:
    def __init__(self):
        self.user_name = "blank_name"
        self.client_chat_name = "c/client"

        self.on_message_callback: Callable[[], None] = lambda: None
        self.on_chat_added_callback: Callable[[], None] = lambda: None
        self.on_chat_removed_callback: Callable[[], None] = lambda: None

        self.net_client = NetClient(self.client_chat_name)

        self.chats: dict[str, list[Message]] = {}
        self.add_chat(self.client_chat_name)

        for greet in greetings:
            self.add_client_text(greet)

        self.connection_thread: Thread | None = None

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def run(self):
        if not self.net_client.connect():
            self.add_client_text("Connection refused")
            return
        self.add_client_text("Connected")
        self.add_chat("r/relay")
        for msg in self.net_client.recv_loop():
            msg: Message
            self.add_message(msg)
        self.add_client_text("Сonnection lost")
        self.remove_chat("r/relay")

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
    def add_message(self, msg: Message):
        if msg.chat not in self.chats:
            self.add_chat(msg.chat)
        self.chats[msg.chat].append(msg)
        self.on_message_callback()

    ### ОТПРАВКА ТЕКСТА ###
    def add_client_text(self, text: str):
        self.add_message(Message(self.client_chat_name, "client", text))

    def send_text(self, chat: str, text: str):
        msg = Message(chat, self.user_name, text)
        self.add_message(msg)
        if chat == self.client_chat_name:
            self.handle_client_msg(text)
        elif not self.net_client.send(msg):
            self.add_client_text("No server")
    
    def handle_client_msg(self, text: str):
        if text == "/connect":
            if self.connection_thread and self.connection_thread.is_alive():
                self.add_client_text("Already connected")
            else:
                self.start_connection_thread()

    def start_connection_thread(self):
        self.connection_thread = Thread(target=self.run)
        self.connection_thread.start()
