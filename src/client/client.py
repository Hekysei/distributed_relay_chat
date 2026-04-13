import asyncio

from src.package_handler.active_package_handler import ActivePackageHandler
from src.connection_handler import ConnectionHandler


class Client(ActivePackageHandler):
    def __init__(self):
        super().__init__(ConnectionHandler())
        self.run_loop : asyncio.AbstractEventLoop

    async def run_net(self, ip: str, port: str):
        self.run_loop = asyncio.get_running_loop()
        await self.connection_handler.connect(ip, port)
        await self.send_username()
        await self.connection_handler.run()

    async def disconnect(self):
        asyncio.run_coroutine_threadsafe(
            self.connection_handler.disconnect(), self.run_loop
        )
