import websocket
from typing import Generator

from src.package.package import Message


class NetClient:
    def __init__(self):
        self.ws: websocket.WebSocket = websocket.WebSocket()

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
                    # print("Connection closed")
                    break
                yield Message.from_json(data)
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as e:
                yield Message(chat="e/error", sender="net_client", text=str(e))
                break

    def send(self, msg: Message):
        try:
            if self.ws.connected:
                self.ws.send(msg.to_json())
                return True
        except Exception as e:
            print(e)
        return False

    def disconnect(self):
        try:
            if self.ws:
                self.ws.close()
        except Exception as e:
            print(e)
