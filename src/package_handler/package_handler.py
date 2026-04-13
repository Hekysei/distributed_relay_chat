from src.package.package import Message, TimestampResponse, SystemMessage


class PackageHandler:
    def __init__(self):
        pass

    async def on_msg(self, msg: Message):
        pass

    async def on_tsr(self, tsr: TimestampResponse):
        pass

    async def on_sys_msg(self, sys_msg: SystemMessage):
        pass
