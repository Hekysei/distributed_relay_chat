import websockets

from websockets.protocol import State
from websockets.exceptions import ConnectionClosed
from src.package.package import Message, SystemMessage

from src.package.package_factory import PackageFactory


class NetClient:
    def __init__(self, package_factory: PackageFactory):
        self.package_factory = package_factory
        self.ws: websockets.ClientConnection | None = None

    async def run(self, ip: str, port: str) -> Message:
        try:
            self.ws = await websockets.connect(f"ws://{ip}:{port}")
            # return True
        except (ConnectionRefusedError, OSError):
            return Message(chat="c/client", sender="net_client", text="No connection")
            # return False
        if not self.ws:
            return Message(chat="c/client", sender="net_client", text="No connection")

        while True:
            try:
                data: str | bytes = await self.ws.recv()
                if not data:
                    break

                await self.package_factory.process_json(data)

            except ConnectionClosed:
                break
            except Exception as e:
                return Message(chat="c/client", sender="net_client", text=str(e))

        return Message(chat="c/client", sender="net_client", text="breaker")

    async def send_message(self, msg: Message):
        if self.ws:
            await self.ws.send(msg.to_json())

    async def send_sys_message(self, sys_msg: SystemMessage):
        if self.ws:
            await self.ws.send(sys_msg.to_json())

    async def disconnect(self):
        if self.ws:
            await self.ws.close()

    def is_connected(self):
        return self.ws is not None and self.ws.state == State.OPEN
