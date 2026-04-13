from typing import Callable

from src.client.user_client import UserClient


class APPClient(UserClient):
    def __init__(self):
        self.on_message_callback: Callable[[]] = lambda: None
        self.on_chat_added_callback: Callable[[]] = lambda: None
        self.on_chat_removed_callback: Callable[[]] = lambda: None

        super().__init__()

    ### TODO сделать обработку чатов после отключения
    async def run_net(self, ip, port):
        await super().run_net(ip, port)

        for chat_name in list(self.chats.keys()):
            if chat_name != self.chat_bot.name:
                self.remove_chat(chat_name)

    ### CALLBACKS ###
    def add_chat(self, *args, **kwargs):
        super().add_chat(*args, **kwargs)
        self.on_chat_added_callback()

    def remove_chat(self, *args, **kwargs):
        super().remove_chat(*args, **kwargs)
        self.on_chat_removed_callback()

    async def on_msg(self, *args, **kwargs):
        await super().on_msg(*args, **kwargs)
        self.on_message_callback()

    async def send_user_message(self, *args, **kwargs):
        await super().send_user_message(*args, **kwargs)
        self.on_message_callback()

    async def on_tsr(self, *args, **kwargs):
        await super().on_tsr(*args, **kwargs)
        self.on_message_callback()

    ### ОПОВЕЩЕНИЕ ПОЛЬЗОВАТЕЛЯ ###
    async def start_connection_thread(self, ip: str, port: str) -> bool:
        res = await super().start_connection_thread(ip, port)
        if not res:
            await self.send_text_to_user("Already connected")
        else:
            await self.send_text_to_user(f"Start connecting to {ip}:{port}")
        return res

    async def connect(self, *args, **kwargs) -> str:
        res = await super().connect(*args, **kwargs)
        if res == "ok":
            await self.send_text_to_user("Connected")
        else:
            await self.send_text_to_user("Connection refused")
        return res

    async def disconnect(self) -> bool:
        res = await super().disconnect()
        if res:
            await self.send_text_to_user("Disconnected")
        else:
            await self.send_text_to_user("Already disconnected")
        return res
