import json
from fastapi import FastAPI, WebSocket
from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials
from concurrent.futures import Future
from threading import Thread
import asyncio

from config import FOVDashboardConfig
from websockets_manager import WebSocketManager

config = FOVDashboardConfig()

# Initialize FastAPI app
app = FastAPI()


def initialize_iot_client() -> IOTClient:
    iot_context = IOTContext()
    iot_credentials = IOTCredentials(
        cert_path=config.cert_path,
        client_id="FOVDashboardClientxxx",
        endpoint=config.endpoint,
        priv_key_path=config.private_key_path,
        ca_path=config.root_ca_path
    )
    return IOTClient(iot_context, iot_credentials)


def message_handler(topic, payload):
    """Handle incoming MQTT messages and notify WebSocket clients."""
    message_str = payload.decode("utf-8")  # Decode the payload from bytes to string
    print(f"Received message from topic '{topic}': {message_str}")

    try:
        # Try to load the message as JSON
        message = json.loads(message_str)
    except json.JSONDecodeError:
        # If it's not valid JSON, manually create a dictionary
        # TODO: I should actually format things better on the MQTT side!
        if "Temperature" in message_str:
            # Handle temperature message
            value = message_str.split(": ")[1]
            message = {"type": "temperature", "value": value}
        elif "Battery" in message_str:
            # Handle battery message
            value = message_str.split(": ")[1]
            message = {"type": "battery", "value": value}
        else:
            message = {"data": message_str}

    # Now call WebSocketManager with a dictionary object
    asyncio.run(WebSocketManager.notify_clients(topic, message))


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


# WebSocket route for real-time communication with frontend
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket route for the frontend to receive real-time updates."""
    await WebSocketManager.websocket_endpoint(websocket)


if __name__ == "__main__":
    import uvicorn
    # Start the FastAPI app using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
