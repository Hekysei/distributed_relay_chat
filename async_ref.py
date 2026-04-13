import asyncio
import websockets
import json

async def send_messages(websocket):
    """Пример отправки сообщений каждые 5 секунд."""
    while True:
        message = {"type": "ping", "timestamp": asyncio.get_event_loop().time()}
        await websocket.send(json.dumps(message))
        await asyncio.sleep(5)

async def receive_messages(websocket):
    """Постоянно читает входящие сообщения."""
    async for message in websocket:
        data = json.loads(message)
        print(f"Received from server: {data}")

async def client():
    uri = "ws://localhost:1409"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to server")
                # Запускаем две задачи: отправку и приём
                await asyncio.gather(
                    send_messages(websocket),
                    receive_messages(websocket)
                )
        except (ConnectionRefusedError, websockets.exceptions.ConnectionClosed) as e:
            print(f"Connection failed or lost: {e}. Reconnecting in 3 seconds...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(client())

