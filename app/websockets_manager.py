from fastapi import WebSocket
from typing import List


class WebSocketManager:
    clients: List[WebSocket] = []

    @classmethod
    async def connect(cls, websocket: WebSocket):
        await websocket.accept()
        cls.clients.append(websocket)

    @classmethod
    async def disconnect(cls, websocket: WebSocket):
        cls.clients.remove(websocket)

    @classmethod
    async def notify_clients(cls, topic, message):
        for client in cls.clients:
            await client.send_json({
                "topic": topic,
                "message": message  # Now this is always a dictionary
            })

    @classmethod
    async def websocket_endpoint(cls, websocket: WebSocket):
        await cls.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()  # Or handle client messages if needed
        except Exception as e:
            print(f"WebSocket error: {e}")
            pass
        finally:
            await cls.disconnect(websocket)
