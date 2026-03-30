from typing import Callable

from threading import Thread


from src.client.net_client import NetClient
from src.package.package import Message, TimestampResponse, SystemMessage
from src.package.package_factory import PackageFactory
from src.chat import Chat


from datetime import datetime


class Client:
    def __init__(self, package_factory: PackageFactory):
        self.user_name = "blank_name"
        self.chats: dict[str, Chat] = {}

        self.messages_wait_for_sync: dict[int, Message] = dict()
        self.messages_sync_count = 0

        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        self.net_client = NetClient(package_factory)

        self.connection_thread: Thread | None = None

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    def connect_to_relay(self, ip: str, port: str) -> bool:
        if self.net_client.connect(ip, port):
            return True
        return False

    def run_net_client(self):
        res: Message = self.net_client.run()
        self.__add_message(res)

    def start_connection_thread(self, ip: str, port: str) -> bool:
        if self.net_client.ws.connected:
            return False
        else:
            if self.connect_to_relay(ip, port):
                self.connection_thread = Thread(target=self.run_net_client)
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

    ### HANDLERS ###
    def on_msg(self, msg: Message):
        self.__add_message(msg)

    def on_ts_response(self, tsr: TimestampResponse):
        self.messages_wait_for_sync.pop(tsr.message_id).timestamp = tsr.timestamp
        self.on_message_callback()

    def on_sys_msg(self, sys_msg: SystemMessage):
        pass

    ### ОТПРАВКА ТЕКСТА ###
    def send_user_text(self, chat: str, text: str) -> bool:
        msg = Message(
            chat=chat,
            sender=self.user_name,
            text=text,
        )

        if msg.chat.startswith("c/"):
            msg.timestamp = datetime.now()
            self.__add_message(msg)
            return True

        self.messages_sync_count += 1
        msg.message_id = self.messages_sync_count
        self.messages_wait_for_sync[self.messages_sync_count] = msg

        self.__add_message(msg)
        return self.net_client.send(msg)
