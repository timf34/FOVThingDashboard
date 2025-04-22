import asyncio
import os
import time
from datetime import timezone
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional

from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials
from database import init_db
from device import DeviceManager
from config import FOVDashboardConfig
from websockets_manager import WebSocketManager

app = FastAPI()
SessionFactory = init_db()
device_manager = DeviceManager(SessionFactory)
config = FOVDashboardConfig()

# from awscrt import io
# io.init_logging(io.LogLevel.Trace, 'stderr')     # <— full wire‑level trace


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fovdashboard.com",
        "https://www.fovdashboard.com",
        "http://fovdashboard.com",
        "https://aviva.fovdashboard.com",
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_iot_client() -> IOTClient:
    iot_context = IOTContext()

    if os.name == 'nt':
        client_id = "FOVDashboardClientLocalx"
    else:
        client_id = "FOVDashboardClient"

    print(f"Client ID: {client_id}")
    iot_credentials = IOTCredentials(
        cert_path=config.cert_path,
        client_id=client_id,
        endpoint=config.endpoint,
        priv_key_path=config.private_key_path,
        ca_path=config.root_ca_path
    )
    return IOTClient(iot_context, iot_credentials)


def message_handler(topic, payload):
    try:
        message_str = payload.decode("utf-8")
        print(f"Received message from topic '{topic}': {message_str}")

        device_name = topic.split('/')[2]
        metric_type = topic.split('/')[-1]

        # Update device and get latest state
        device_data = device_manager.update_device(device_name, metric_type, message_str)

        # Notify WebSocket clients with proper message format
        asyncio.run(WebSocketManager.notify_clients(device_name, device_data))
    except Exception as e:
        print(f"Error handling message: {str(e)}")
        import traceback
        traceback.print_exc()


def start_iot_client():
    """Start the IoT Client, connect, and subscribe to topics."""
    iot_client = initialize_iot_client()
    iot_client.connect()

    # Subscribe to the wildcard topics
    iot_client.subscribe(topic=config.version_topic, handler=message_handler)
    iot_client.subscribe(topic=config.battery_topic, handler=message_handler)
    iot_client.subscribe(topic=config.temperature_topic, handler=message_handler)
    iot_client.subscribe(topic=config.ota_topic, handler=message_handler)

    def watchdog():
        while True:
            if not iot_client.connected:
                print("⚠️  MQTT lost – forcing reconnect")
                try:
                    iot_client._mqtt.reconnect().result()
                except Exception as exc:
                    print("reconnect failed:", exc)
            time.sleep(10)

    Thread(target=watchdog, daemon=True).start()



@app.get("/api/status")
async def status():
    """Return system status information for debugging"""
    import psutil
    import os
    
    # Check if certificates exist
    cert_files = {
        "cert_path": os.path.exists(config.cert_path),
        "private_key_path": os.path.exists(config.private_key_path),
        "root_ca_path": os.path.exists(config.root_ca_path)
    }
    
    # Get system information
    mem = psutil.virtual_memory()
    
    return {
        "status": "online",
        "certificates": cert_files,
        "device_count": len(device_manager.devices),
        "websocket_connections": len(WebSocketManager.clients),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_used_percent": mem.percent,
            "memory_available_mb": mem.available / (1024 * 1024)
        },
        "server_time": datetime.utcnow().isoformat()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt")
    try:
        await WebSocketManager.connect(websocket)
        # Send current state of all devices
        for device_name, device_data in device_manager.devices.items():
            try:
                await websocket.send_json({
                    "topic": device_name,
                    "message": device_data
                })
            except Exception as e:
                print(f"Error sending initial device data: {e}")
        
        # Keep connection alive with ping/pong mechanism
        while True:
            try:
                # Use a timeout to detect stale connections
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                # Echo back as a simple ping/pong mechanism
                await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send a ping to check if connection is still alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    # Connection is dead, break loop
                    break
            except Exception as e:
                print(f"WebSocket receive error: {e}")
                break
    except Exception as e:
        print(f"WebSocket connection error: {str(e)}")
    finally:
        await WebSocketManager.disconnect(websocket)
        print("WebSocket connection closed")


@app.get("/api/devices")
async def get_devices():
    """Get all known devices and their current state"""
    return device_manager.devices


@app.get("/api/device/{device_name}/history")
async def get_device_history(
    device_name: str,
    metric_type: Optional[str] = None,
    hours: Optional[int] = 24,
    last_id: Optional[int] = None,
    page_size: int = 50
):
    """Get historical logs for a device with pagination"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours) if hours else None
        logs, has_more = device_manager.get_device_history(
            device_name,
            metric_type=metric_type,
            start_time=start_time,
            page_size=page_size,
            last_id=last_id
        )
        return {
            "logs": logs,
            "hasMore": has_more,
            "lastId": logs[-1]['id'] if logs else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def check_device_status():
    """Periodic task to update device WiFi status"""
    while True:
        device_manager.check_wifi_status()
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup_event():
    # Start the AWS IoT client in a background thread
    iot_thread = Thread(target=start_iot_client)
    iot_thread.daemon = False   # ✅ make it non-daemon so it keeps container alive
    iot_thread.start()

    # Start the device status checker
    asyncio.create_task(check_device_status())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
