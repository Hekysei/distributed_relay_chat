import websocket

from src.package.package import Message

from src.package.package_factory import PackageFactory

class NetClient:
    def __init__(self, package_factory : PackageFactory):
        self.package_factory = package_factory
        self.ws: websocket.WebSocket = websocket.WebSocket()

    def connect(self, ip: str, port: str) -> bool:
        try:
            self.ws.connect(f"ws://{ip}:{port}")
            return True
        except ConnectionRefusedError, OSError:
            return False

    def run(self) -> Message:
        while True:
            try:
                data: str | bytes = self.ws.recv()
                if not data:
                    # print("Connection closed")
                    break
                self.package_factory.process_json(data)
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as e:
                return Message(chat="c/client", sender="net_client", text=str(e))

        return Message(chat="c/client", sender="net_client", text="breaker")

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
