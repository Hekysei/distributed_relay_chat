import websockets

from websockets.protocol import State
from websockets.exceptions import ConnectionClosed
from src.package.package import Message, SystemMessage, TimestampResponse

from src.package_handler.package_factory import PackageFactory


class ConnectionHandler:
    def __init__(
        self,
        ws: websockets.ClientConnection | websockets.ServerConnection | None = None,
    ):
        self.ws: websockets.ClientConnection | websockets.ServerConnection | None = ws
        self.package_factory: PackageFactory

    async def connect(self, ip: str, port: str):
        try:
            self.ws = await websockets.connect(f"ws://{ip}:{port}")
            # return True
        except (ConnectionRefusedError, OSError):
            return Message(chat="c/client", sender="net_client", text="No connection")
            # return False
        if not self.ws:
            return Message(chat="c/client", sender="net_client", text="No connection")

    async def run(self) -> Message:
        if self.ws:
            try:
                async for data in self.ws:
                    await self.package_factory.process_json(data)
            except ConnectionClosed:
                pass
            except Exception as e:
                return Message(chat="c/client", sender="net_client", text=str(e))

        return Message(chat="c/client", sender="net_client", text="breaker")

    async def send_message(self, msg: Message):
        if self.ws:
            await self.ws.send(msg.to_json())

    async def send_tsr(self, tsr: TimestampResponse):
        if self.ws:
            await self.ws.send(tsr.to_json())

    async def send_sys_message(self, sys_msg: SystemMessage):
        if self.ws:
            await self.ws.send(sys_msg.to_json())

    async def disconnect(self):
        if self.ws:
            await self.ws.close()

    def is_connected(self):
        return self.ws is not None and self.ws.state == State.OPEN
