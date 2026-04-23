import asyncio
import websockets
import signal

from typing import Callable

from src.connection_handler import ConnectionHandler


class Server:
    def __init__(self):
        self.active_connections: set[websockets.ServerConnection] = set()

        self.on_connection_callback: Callable[[ConnectionHandler]] = lambda _: None

    async def handler_factory(self, ws: websockets.ServerConnection):
        print("Client connected")
        self.active_connections.add(ws)

        connection_handler = ConnectionHandler(ws)

        try:
            await self.on_connection_callback(connection_handler)
        finally:
            await ws.close()
            self.active_connections.remove(ws)
            print("Client disconnected")

    async def run(self):
        async with websockets.serve(self.handler_factory, "localhost", 1409):
            print("Server started. Press Ctrl+C to stop.")

            loop = asyncio.get_running_loop()
            stop_future = loop.create_future()

            try:
                loop.add_signal_handler(signal.SIGINT, stop_future.set_result, None)
                loop.add_signal_handler(signal.SIGTERM, stop_future.set_result, None)
            except Exception as e:
                print("Can't set signal")
                print(e)
                print("It looks like you are using Windows")
            
            try:
                await stop_future
            finally:
                print("Closing active connections")
                await self.close_active_connections()

    async def close_active_connections(self):
        if self.active_connections:
            print(f"Closing {len(self.active_connections)} active connections...")
            close_tasks = [ws.close() for ws in self.active_connections]
            await asyncio.gather(*close_tasks, return_exceptions=True)
