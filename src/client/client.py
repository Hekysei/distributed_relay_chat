import asyncio
from threading import Thread

from src.package_handler.active_package_handler import ActivePackageHandler
from src.connection_handler import ConnectionHandler


class Client(ActivePackageHandler):
    def __init__(self):
        super().__init__(ConnectionHandler())
        self.run_loop: asyncio.AbstractEventLoop

    ### РАБОТА ПОДКЛЮЧЕНИЯ ###
    async def start_connection_thread(self, ip: str, port: str) -> bool:
        if self.connection_handler.is_connected():
            return False
        Thread(target=lambda: asyncio.run(self.run_net(ip, port))).start()
        return True

    async def run_net(self, ip: str, port: str):
        self.run_loop = asyncio.get_running_loop()

        connect_res = await self.connect(ip, port)
        if connect_res != "ok":
            return

        await self.on_connected()
        await self.connection_handler.run()

    async def connect(self, ip: str, port: str) -> str:
        return await self.connection_handler.connect(ip, port)

    async def on_connected(self):
        await self.send_username()

    async def disconnect(self) -> bool:
        if self.connection_handler.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.connection_handler.disconnect(), self.run_loop
            )
            return True
        return False
