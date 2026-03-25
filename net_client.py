import websocket
from typing import Generator

from message import Message, json_to_message, message_to_json


class NetClient:
    def __init__(self, chat_for_logs):
        self.ws: websocket.WebSocket = websocket.WebSocket()

        self.chat_for_logs = chat_for_logs

    def connect(self, ip: str, port: str) -> bool:
        try:
            self.ws.connect(f"ws://{ip}:{port}")
            return True
        except ConnectionRefusedError, OSError:
            return False

    def recv_loop(self) -> Generator[Message]:
        while True:
            try:
                data: str | bytes = self.ws.recv()
                if not data:
                    print("Connection closed")
                    break
                yield json_to_message(data)
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as e:
                yield Message(self.chat_for_logs, "net_client", str(e))
                break

    def send(self, msg: Message):
        if self.ws.connected:
            self.ws.send(message_to_json(msg))
            return True
        return False
