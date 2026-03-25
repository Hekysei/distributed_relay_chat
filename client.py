from typing import Callable

from net_client import NetClient
from message import Message


class Client:
    def __init__(self):
        self.name = "blank_name"
        self.net_client = NetClient()
        self.messages: list[Message] = []
        self.chats: dict[str, list[Message] |str] = {"c/": [], "r/": []}

        self.on_message_callback: Callable[[], None] = lambda: None

    def run(self):
        self.add_sys_message("welcome")
        if self.net_client.connect():
            for msg in self.net_client.recv_loop():
                msg: Message
                self.add_message(msg)
        self.add_sys_message("Сonnection lost")

    def stop(self):
        self.net_client.ws.close()

    def add_message(self, msg: Message):
        self.messages.append(msg)
        self.on_message_callback()

    def add_sys_message(self, text: str):
        self.add_message(Message("local", "sys", text))

    def add_client_message(self, text: str):
        self.add_message(Message("local", self.name, text))

    def send_text(self, text: str):
        self.add_client_message(text)
        if not self.net_client.send(self.messages[-1]):
            self.add_sys_message("No server")
