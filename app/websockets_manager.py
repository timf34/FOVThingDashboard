from fastapi import WebSocket


class WebSocketManager:
    clients = []

    @classmethod
    async def websocket_endpoint(cls, websocket: WebSocket):
        """Handle WebSocket connections."""
        await websocket.accept()
        cls.clients.append(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            cls.clients.remove(websocket)

    @classmethod
    async def notify_clients(cls, topic, message):
        """Send real-time messages to all connected WebSocket clients."""
        for client in cls.clients:
            await client.send_json({topic: message})
