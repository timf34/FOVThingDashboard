from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
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
        # make *anything* JSON-serialisable (datetime, Decimal, UUID …)
        safe_message = jsonable_encoder(message)

        disconnected_clients = []
        for client in cls.clients:
            try:
                await client.send_json({"topic": topic, "message": safe_message})
            except Exception as e:
                print(f"Error sending to client - removing: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in cls.clients:
                cls.clients.remove(client)

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
