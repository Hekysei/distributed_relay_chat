from typing import Callable

from net_client import NetClient
from message import Message
# from bot import Bot

from threading import Thread


greetings = [
    "Welcome!",
    "Commands:",
    "/c, /connect - connect to relay",
    "/d - disconnect",
]

from command_router import CommandRouter


class Bot:
    def __init__(self, send_text):
        self.command_router = CommandRouter()

        self.send_text: Callable[[str]] = send_text
        for greet in greetings:
            self.send_text(greet)

    def add_command(self, command: str, function: Callable[...], args: dict[str, str]):
        self.command_router.add_command(command, function, args)

    def on_text(self, text: str):
        if text.startswith("/") and not self.command_router.route(text):
            self.send_text("Unknown or Error")


class Chat:
    def __init__(self, name):
        self.name = name
        self.messages: list[Message] = []

    def _add_message(self, msg: Message):
        self.messages.append(msg)

    def send_message(self, msg: Message):
        self._add_message(msg)


class ChatBot(Chat):
    def __init__(self, name, bot_name):
        super().__init__(name)
        self.bot = Bot(
            lambda text: self._add_message(Message(name, bot_name, text)),
        )

    def add_commands(self, commands: list):
        for command in commands:
            self.bot.add_command(*command)

    def send_message(self, msg: Message):
        super().send_message(msg)
        self.bot.on_text(msg.text)


class ClientChatBot(ChatBot):
    def __init__(self, client):
        super().__init__("c/client", "client")

        CONNECT_ARGS = {"ip": "localhost", "port": "1409"}
        CLIENT_COMMANDS = [
            ("/connect", client.start_connection_thread, CONNECT_ARGS),
            ("/c", client.start_connection_thread, CONNECT_ARGS),
            ("/d", client.stop, {}),
        ]
        self.add_commands(CLIENT_COMMANDS)


class Client:
    def __init__(self):
        self.user_name = "blank_name"
        self.chats: dict[str, Chat] = {}

        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        self.chat_bot = ClientChatBot(self)
        self.add_chat(self.chat_bot)
        self.net_client = NetClient(self.chat_bot.name)

        self.connection_thread: Thread | None = None

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def start_connection_thread(self, ip: str, port: str):
        if self.connection_thread and self.connection_thread.is_alive():
            self.__send_text_to_user("Already connected")
        else:
            self.connection_thread = Thread(
                target=self.connect_to_relay, args=(ip, port)
            )
            self.connection_thread.start()

    def connect_to_relay(self, ip: str, port: str):
        if not self.net_client.connect(ip, port):
            self.__send_text_to_user("Connection refused")
            return
        self.__send_text_to_user("Connected")
        for msg in self.net_client.recv_loop():
            msg: Message
            self.__add_message(msg)
        self.__send_text_to_user("Сonnection lost")

        for chat_name in list(self.chats.keys()):
            if chat_name != self.chat_bot.name:
                self.remove_chat(chat_name)

    def stop(self):
        if self.net_client.ws.connected:
            self.net_client.ws.close()

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

    def send_user_text(self, chat: str, text: str):
        msg = Message(chat, self.user_name, text)
        self.__add_message(msg)

        if not chat.startswith("c/") and not self.net_client.send(msg):
            self.__send_text_to_user("No server")

    def __send_text_to_user(self, text: str):
        self.chat_bot.bot.send_text(text)
