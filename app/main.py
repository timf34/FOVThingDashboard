import asyncio
import json
import uvicorn

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials
from concurrent.futures import Future
from threading import Thread
from typing import List, Dict


from config import FOVDashboardConfig
from device import Device
from websockets_manager import WebSocketManager

config = FOVDashboardConfig()

devices: Dict[str, Device] = {}

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your React app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_iot_client() -> IOTClient:
    iot_context = IOTContext()

    if os.name == 'nt':
        client_id = "FOVDashboardClientLocal"
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
    message_str = payload.decode("utf-8")
    print(f"Received message from topic '{topic}': {message_str}")

    device_name = topic.split('/')[2]
    message_type = topic.split('/')[-1]

    if device_name not in devices:
        devices[device_name] = Device(device_name)

    try:
        value = json.loads(message_str)
    except json.JSONDecodeError:
        value = message_str.split(': ')[1] if ': ' in message_str else message_str

    devices[device_name].update(message_type, value)

    # Notify WebSocket clients
    asyncio.run(WebSocketManager.notify_clients(device_name, devices[device_name].to_dict()))


def start_iot_client():
    """Start the IoT Client, connect, and subscribe to topics."""
    iot_client = initialize_iot_client()
    iot_client.connect()

    # Subscribe to the wildcard topics
    iot_client.subscribe(topic=config.version_topic, handler=message_handler)
    iot_client.subscribe(topic=config.battery_topic, handler=message_handler)
    iot_client.subscribe(topic=config.temperature_topic, handler=message_handler)


# Start the AWS IoT client in a background thread
iot_thread = Thread(target=start_iot_client)
iot_thread.start()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await WebSocketManager.websocket_endpoint(websocket)
    for device in devices.values():
        print("endpoing: ", device)
        await websocket.send_json({device.name: device.to_dict()})


async def check_device_status():
    while True:
        for device in devices.values():
            print("check device status: ", device)
            device.check_wifi_status()
            await WebSocketManager.notify_clients(device.name, device.to_dict())
        await asyncio.sleep(5)  # Check every 5 seconds


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_device_status())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
