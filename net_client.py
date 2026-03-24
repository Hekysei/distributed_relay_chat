import json
import websocket
from typing import Generator, Any, Dict


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

    def recv_loop(self) -> Generator[Dict[str, Any], None, None]:
        while True:
            try:
                message = self.ws.recv()
                if not message:
                    print("Connection closed")
                    break
                data: dict = json.loads(message)
                yield data
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as e:
                yield {"error": str(e)}
                break

    def send(self, data: dict):
        if self.ws.connected:
            self.ws.send(json.dumps(data))
            return True
        return False
