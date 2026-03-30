from src.client.client import Client
from src.chat import ChatBot
from src.package.package_factory import PackageFactory

greetings = [
    "Welcome!",
    "Commands:",
    "/c, /connect - connect to relay",
    "/d - disconnect",
]


class APPClientChatBot(ChatBot):
    def __init__(self, client: Client):
        super().__init__("c/client", "client")

        CONNECT_ARGS = {"ip": "localhost", "port": "1409"}
        CLIENT_COMMANDS = [
            ("/connect", client.start_connection_thread, CONNECT_ARGS),
            ("/c", client.start_connection_thread, CONNECT_ARGS),
            ("/d", client.disconnect, {}),
        ]
        self.add_commands(CLIENT_COMMANDS)
        for greet in greetings:
            self.bot.send_text(greet)


class APPClientPackageFactory(PackageFactory):
    def __init__(self, client: Client):
        self._handlers = {
            "message_request": client.on_msg,
            "timestamp_response": client.on_ts_response,
            "system_message": client.on_sys_msg,
        }


class APPClient(Client):
    def __init__(self):
        super().__init__(APPClientPackageFactory(self))
        self.chat_bot = APPClientChatBot(self)
        self.add_chat(self.chat_bot)

    def __send_text_to_user(self, text: str):
        self.chat_bot.bot.send_text(text)

    def send_user_text(self, chat: str, text: str) -> bool:
        res = super().send_user_text(chat, text)
        if not res:
            self.__send_text_to_user("No server")
        return res

    def start_connection_thread(self, ip: str, port: str) -> bool:
        res = super().start_connection_thread(ip, port)
        if not res:
            self.__send_text_to_user("Already connected")
        # else:
        #     self.__send_text_to_user(f"Start connecting to {ip}:{port}")
        return res

    def connect_to_relay(self, ip: str, port: str) -> bool:
        res = super().connect_to_relay(ip, port)
        if res:
            self.__send_text_to_user("Connected")
        else:
            self.__send_text_to_user("Connection refused")
        return res

    def run_net_client(self):
        super().run_net_client()
        self.__send_text_to_user("Сonnection lost")

        for chat_name in list(self.chats.keys()):
            if chat_name != self.chat_bot.name:
                self.remove_chat(chat_name)
