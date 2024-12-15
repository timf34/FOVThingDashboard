import asyncio
import os
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fovdashboard.com",
        "https://www.fovdashboard.com",
        "http://fovdashboard.com",
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
    """Handle incoming MQTT messages"""
    try:
        message_str = payload.decode("utf-8")
        print(f"Received message from topic '{topic}': {message_str}")

        device_name = topic.split('/')[2]
        metric_type = topic.split('/')[-1]

        # Update device and get latest state
        device_data = device_manager.update_device(device_name, metric_type, message_str)

        # Notify WebSocket clients
        asyncio.run(WebSocketManager.notify_clients(device_name, device_data))
    except Exception as e:
        print(f"Error handling message: {e}")


def start_iot_client():
    """Start the IoT Client, connect, and subscribe to topics."""
    iot_client = initialize_iot_client()
    iot_client.connect()

    # Subscribe to the wildcard topics
    iot_client.subscribe(topic=config.version_topic, handler=message_handler)
    iot_client.subscribe(topic=config.battery_topic, handler=message_handler)
    iot_client.subscribe(topic=config.temperature_topic, handler=message_handler)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt")
    try:
        await WebSocketManager.connect(websocket)
        # Send current state of all devices
        for device_name, device_data in device_manager.devices.items():
            await websocket.send_json({device_name: device_data})

        # Keep connection alive and handle any client messages
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await WebSocketManager.disconnect(websocket)


@app.get("/api/devices")
async def get_devices():
    """Get all known devices and their current state"""
    return device_manager.devices


@app.get("/api/device/{device_name}/history")
async def get_device_history(
    device_name: str,
    metric_type: Optional[str] = None,
    hours: Optional[int] = 24
):
    """Get historical logs for a device"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours) if hours else None
        logs = device_manager.get_device_history(
            device_name,
            metric_type=metric_type,
            start_time=start_time
        )
        return logs
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
    iot_thread.daemon = True
    iot_thread.start()

    # Start the device status checker
    asyncio.create_task(check_device_status())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
