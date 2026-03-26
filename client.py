from typing import Callable

from net_client import NetClient
from message import Message
from command_router import CommandRouter

from threading import Thread

greetings = [
    "Welcome!",
    "Commands:",
    "/c, /connect - connect to relay",
    "/d - disconnect"
]


class Client:
    def __init__(self):
        self.user_name = "blank_name"
        self.client_chat_name = "c/client"

        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        self.net_client = NetClient(self.client_chat_name)

        self.command_router = CommandRouter()
        self.__setup_command_router()

        self.chats: dict[str, list[Message]] = {}
        self.add_chat(self.client_chat_name)

        for greet in greetings:
            self.add_client_text(greet)

        self.connection_thread: Thread | None = None

    def __setup_command_router(self):
        connect_args = {"ip": "localhost", "port": "1409"}
        self.command_router.add_command(
            "/connect", self.start_connection_thread, connect_args
        )
        self.command_router.add_command(
            "/c", self.start_connection_thread, connect_args
        )

        self.command_router.add_command("/d", self.stop, {})

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def connect_to_relay(self, ip: str, port: str):
        if not self.net_client.connect(ip, port):
            self.add_client_text("Connection refused")
            return
        self.add_client_text("Connected")
        for msg in self.net_client.recv_loop():
            msg: Message
            self.add_message(msg)
        self.add_client_text("Сonnection lost")

        for chat_name in list(self.chats.keys()):
            if chat_name != self.client_chat_name:
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
        if text.startswith("/") and not self.command_router.route(text):
            self.add_client_text("Unknown or Error")

    def start_connection_thread(self, ip: str, port: str):
        if self.connection_thread and self.connection_thread.is_alive():
            self.add_client_text("Already connected")
        else:
            self.connection_thread = Thread(
                target=self.connect_to_relay, args=(ip, port)
            )
            self.connection_thread.start()
