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
            ("/d", client.disconnect, {}),
        ]
        self.add_commands(CLIENT_COMMANDS)


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
    def start_connection_thread(self, ip: str, port: str) -> bool:
        if self.connection_thread and self.connection_thread.is_alive():
            return False
        else:
            self.connection_thread = Thread(
                target=self.connect_to_relay, args=(ip, port)
            )
            self.connection_thread.start()
            return True

    def connect_to_relay(self, ip: str, port: str):
        if not self.net_client.connect(ip, port):
            # self.__send_text_to_user("Connection refused")
            return
        # self.__send_text_to_user("Connected")
        for msg in self.net_client.recv_loop():
            msg: Message
            self.__add_message(msg)

        # for chat_name in list(self.chats.keys()):
        #     if chat_name != self.chat_bot.name:
        #         self.remove_chat(chat_name)

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
        msg = Message(chat, self.user_name, text)
        self.__add_message(msg)
        
        return self.net_client.send(msg)



class APPClient(Client):
    def __init__(self):
        super().__init__()
        self.chat_bot = ClientChatBot(self)
        self.add_chat(self.chat_bot)

    def __send_text_to_user(self, text: str):
        self.chat_bot.bot.send_text(text)
    
    def send_user_text(self, chat: str, text: str) -> bool:
        res = super().send_user_text(chat,text)
        if not chat.startswith("c/") and not res:
            self.__send_text_to_user("No server")
        return res

    def start_connection_thread(self, ip: str, port: str) -> bool:
        res = super().start_connection_thread(ip,port)
        if res:
            self.__send_text_to_user(f"Start connecting to {ip}:{port}")
        else:
            self.__send_text_to_user("Already connected")
        return res

    def connect_to_relay(self, ip: str, port: str):
        super().connect_to_relay(ip,port)
        self.__send_text_to_user("Сonnection lost")

