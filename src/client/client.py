from typing import Callable, cast

from threading import Thread


from src.client.net_client import NetClient
from src.package.package import Message, TimestampResponse, SystemMessage
from src.package.package_factory import PackageFactory
from src.chat import RemoteChat, Chat


class Client:
    def __init__(self, package_factory: PackageFactory):
        self.username = "blank_name"
        self.chats: dict[str, Chat] = {}

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
        self.on_msg(res)

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
        self.add_chat(RemoteChat(chat_name, self.net_client))

    def remove_chat(self, chat_name):
        self.chats.pop(chat_name)
        self.on_chat_removed_callback()

    ### HANDLERS ###
    def on_msg(self, msg: Message):
        if msg.chat not in self.chats:
            self.create_chat(msg.chat)
        self.chats[msg.chat].add_message(msg)
        self.on_message_callback()

    def on_ts_response(self, tsr: TimestampResponse):
        cast(RemoteChat, self.chats[tsr.chat]).on_tsr(tsr)
        self.on_message_callback()

    def on_sys_msg(self, sys_msg: SystemMessage):
        if sys_msg.msg_type == "set_username":
            self.username = sys_msg.body

    ### ОТПРАВКА ТЕКСТА ###
    def send_user_text(self, chat: str, text: str):
        msg = Message(
            chat=chat,
            sender=self.username,
            text=text,
        )

        self.chats[chat].send_message(msg)
        self.on_message_callback()
