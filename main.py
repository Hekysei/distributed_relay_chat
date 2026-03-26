#!/usr/bin/env python3


from client import Client
from chat import ChatBot
from tui_adapter import TUI_Adapter


class ClientChatBot(ChatBot):
    def __init__(self, client: Client):
        super().__init__("c/client", "client")

        CONNECT_ARGS = {"ip": "localhost", "port": "1409"}
        CLIENT_COMMANDS = [
            ("/connect", client.start_connection_thread, CONNECT_ARGS),
            ("/c", client.start_connection_thread, CONNECT_ARGS),
            ("/d", client.disconnect, {}),
        ]
        self.add_commands(CLIENT_COMMANDS)


class APPClient(Client):
    def __init__(self):
        super().__init__()
        self.chat_bot = ClientChatBot(self)
        self.add_chat(self.chat_bot)

    def __send_text_to_user(self, text: str):
        self.chat_bot.bot.send_text(text)
    
    def send_user_text(self, chat: str, text: str) -> bool:
        if not chat.startswith("c/"):
            res = super().send_user_text(chat, text)
            if not res:
                self.__send_text_to_user("No server")
            return res
        self.on_message_callback()
        return True
    
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

    def recv_loop(self):
        super().recv_loop()
        self.__send_text_to_user("Сonnection lost")
    
        for chat_name in list(self.chats.keys()):
            if chat_name != self.chat_bot.name:
                self.remove_chat(chat_name)


class APP:
    def __init__(self):
        self.client = APPClient()
        self.tui_adapter = TUI_Adapter(self.client)

        self.client.on_message_callback = self.tui_adapter.update_messages
        self.client.on_chat_added_callback = self.tui_adapter.update_bar
        self.client.on_chat_removed_callback = self.tui_adapter.handle_chat_removed

    def run(self):
        self.tui_adapter.run()
        self.client.disconnect()


if __name__ == "__main__":
    app = APP()
    app.run()
