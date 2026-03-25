from typing import Callable

from net_client import NetClient
from message import Message


class Client:
    def __init__(self):
        self.user_name = "blank_name"
        self.client_chat_name = "c/client"

        self.on_message_callback: Callable[[], None] = lambda: None
        self.on_chat_added_callback: Callable[[], None] = lambda: None

        self.net_client = NetClient()

        self.chats: dict[str, list[Message]] = {}
        self.add_chat(self.client_chat_name)

    def run(self):
        self.add_client_message("welcome")
        if self.net_client.connect():
            self.add_chat("r/relay")
            for msg in self.net_client.recv_loop():
                msg: Message
                self.add_message(msg)
        self.add_client_message("Сonnection lost")

    def add_chat(self, chat_name):
        self.chats[chat_name] = []
        self.on_chat_added_callback()

    def add_message(self, msg: Message):
        self.chats[msg.chat].append(msg)
        self.on_message_callback()

    def stop(self):
        self.net_client.ws.close()

    def add_client_message(self, text: str):
        self.add_message(Message(self.client_chat_name, "client", text))

    def send_text(self, chat: str, text: str):
        msg = Message(chat, self.user_name, text)
        self.add_message(msg)
        if chat == self.client_chat_name:
            pass
        elif not self.net_client.send(msg):
            self.add_client_message("No server")
