from src.package_handler.package_handler import PackageHandler
from src.package_handler.package_factory import PackageFactory
from src.connection_handler import ConnectionHandler


class ActivePackageHandler(PackageHandler):
    def __init__(self, connection_handler: ConnectionHandler):
        super().__init__()
        self.username = "blank_name"
        self.connection_handler = connection_handler
        self.connection_handler.package_factory = PackageFactory(self)
