from src.package.package import Message, TimestampResponse, SystemMessage

class PackageHandler:
    def __init__(self):
        pass

    async def on_msg(self, msg: Message):
        pass

    async def on_ts_response(self, tsr: TimestampResponse):
        pass

    async def on_sys_msg(self, sys_msg: SystemMessage):
        pass

class NamedPackageHandler(PackageHandler):
    def __init__(self):
        super().__init__()
        self.username = "blank_name"
