from src.package_handler.package_handler import PackageHandler
from src.package_handler.package_factory import PackageFactory
from src.connection_handler import ConnectionHandler

from src.package.package import SystemMessage

class ActivePackageHandler(PackageHandler):
    def __init__(self, connection_handler: ConnectionHandler):
        super().__init__()
        self.username = "blank_name"
        self.connection_handler = connection_handler
        self.connection_handler.package_factory = PackageFactory(self)

        self.send_tsr = connection_handler.send_tsr
        self.send_message = connection_handler.send_message
        self.send_sys_message = connection_handler.send_sys_message

    async def send_username(self):
        await self.send_sys_message(
            SystemMessage(msg_type="set_username", body=self.username)
        )

    async def set_username(self, name: str):
        self.username = name
        if self.connection_handler.is_connected():
            await self.send_username()
