import websocket
from typing import Generator

from message import Message, json_to_message, message_to_json


class NetClient:
    def __init__(self):
        self.server_url = "ws://localhost:1409"
        self.ws: websocket.WebSocket = websocket.WebSocket()

    def connect(self) -> bool:
        try:
            self.ws.connect(self.server_url)
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
                yield Message("system", "net_client", str(e))
                break

    def send(self, msg: Message):
        if self.ws.connected:
            self.ws.send(message_to_json(msg))
            return True
        return False
