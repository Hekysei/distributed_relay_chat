from src.chat import ChatBot

greetings = [
    "Welcome!",
    "Commands:",
    "/c, /connect - connect to relay",
    "/d - disconnect",
]


class ClientChatBot(ChatBot):
    def __init__(self, client):
        super().__init__("c/client", "client")

        CONNECT_ARGS = {"ip": "localhost", "port": "1409"}
        CLIENT_COMMANDS = [
            ("/connect", client.start_connection_thread, CONNECT_ARGS),
            ("/c", client.start_connection_thread, CONNECT_ARGS),
            ("/d", client.disconnect, {}),
            (
                "/name",
                client.set_username,
                {
                    "name": "blank_name",
                },
            ),
        ]
        self.add_commands(CLIENT_COMMANDS)
        for greet in greetings:
            self.bot.send_text(greet)
