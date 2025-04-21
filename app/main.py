# app/main.py
from __future__ import annotations

import asyncio
import logging
import os
import signal
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional, Tuple

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials
from config import FOVDashboardConfig
from database import init_db
from device import DeviceManager
from websockets_manager import WebSocketManager  # unchanged

# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s",
)
log = logging.getLogger("fov.main")

# --------------------------------------------------------------------------- #
# globals (kept minimal)
# --------------------------------------------------------------------------- #
app = FastAPI()
config = FOVDashboardConfig()
SessionFactory = init_db()
device_manager = DeviceManager(SessionFactory)

# an asyncio queue for the IoT background thread to push messages into
_iot_queue: asyncio.Queue[Tuple[str, str]] | None = None
_iot_thread: Thread | None = None
_iot_client: IOTClient | None = None

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
ALLOWED_ORIGINS = [
    "https://fovdashboard.com",
    "https://www.fovdashboard.com",
    "http://fovdashboard.com",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _client_id() -> str:
    """Separate ID for local dev vs deployed."""
    return "FOVDashboardClientLocal" if os.name == "nt" else "FOVDashboardClient"


def _parse_topic(topic: str) -> Tuple[str, str]:
    """
    eu-west-1/aviva/<device>/<metric>
    ->  (<device>, <metric>)
    """
    parts = topic.split("/")
    if len(parts) < 4:
        raise ValueError(f"Unexpected topic structure: {topic!r}")
    return parts[2], parts[-1]


# --------------------------------------------------------------------------- #
# IoT client bootstrap (runs in a real thread, blocks on MQTT loop)
# --------------------------------------------------------------------------- #


def _iot_thread_fn(queue: asyncio.Queue) -> None:
    """Run inside a native thread; blocks on the AWS CRT event‑loop."""
    global _iot_client

    log.info("IoT thread starting")
    context = IOTContext()
    creds = IOTCredentials(
        cert_path=config.cert_path,
        priv_key_path=config.private_key_path,
        ca_path=config.root_ca_path,
        endpoint=config.endpoint,
        client_id=_client_id(),
    )
    _iot_client = IOTClient(context, creds)
    _iot_client.connect()

    for topic in (
        config.version_topic,
        config.battery_topic,
        config.temperature_topic,
        config.ota_topic,
    ):
        _iot_client.subscribe(topic=topic, handler=lambda t, p: queue.put_nowait((t, p)))

    # block the thread for ever; the AWS‑CRT SDK keeps its own event‑loop alive
    signal.pause()


async def _consume_iot_queue(queue: asyncio.Queue) -> None:
    """Coroutine running in the FastAPI loop that processes IoT messages."""
    while True:
        topic, payload_bytes = await queue.get()
        try:
            payload_str = payload_bytes.decode()
            device, metric = _parse_topic(topic)
            log.debug("IoT %s %s %s", device, metric, payload_str)

            # update DB + in‑mem cache
            new_state = device_manager.update_device(device, metric, payload_str)

            # push to websocket clients
            await WebSocketManager.notify_clients(device, new_state)
        except Exception as exc:
            log.exception("Failed to handle IoT message: %s", exc, stack_info=False)


# --------------------------------------------------------------------------- #
# LIFESPAN – startup / shutdown
# --------------------------------------------------------------------------- #
@app.on_event("startup")
async def _startup() -> None:
    global _iot_queue, _iot_thread

    _iot_queue = asyncio.Queue()
    # kick off queue consumer
    asyncio.create_task(_consume_iot_queue(_iot_queue))

    # kick off the blocking mqtt thread
    _iot_thread = Thread(target=_iot_thread_fn, args=(_iot_queue,), name="IoT‑MQTT")
    _iot_thread.start()

    # periodic Wi‑Fi‑status checker
    asyncio.create_task(_wifi_status_task())
    log.info("Application startup complete")


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _iot_client:
        try:
            _iot_client.disconnect()
        except Exception:
            pass
    if _iot_thread and _iot_thread.is_alive():
        _iot_thread.join(timeout=2)
    log.info("Application shutdown complete")


async def _wifi_status_task() -> None:
    """Mark devices disconnected if we haven't seen them for > 60 s."""
    while True:
        device_manager.check_wifi_status()
        await asyncio.sleep(30)

# --------------------------------------------------------------------------- #
# REST endpoints
# --------------------------------------------------------------------------- #


@app.get("/api/devices")
async def get_devices():
    return device_manager.devices


@app.get("/api/device/{device_name}/history")
async def get_device_history(
    device_name: str,
    metric_type: Optional[str] = None,
    hours: int = 24,
    last_id: Optional[int] = None,
    page_size: int = 50,
):
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        logs, has_more = device_manager.get_device_history(
            device_name,
            metric_type,
            start_time=start_time,
            page_size=page_size,
            last_id=last_id,
        )
        return {
            "logs": logs,
            "hasMore": has_more,
            "lastId": logs[-1]["id"] if logs else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/status")
async def status():
    mem = psutil.virtual_memory()
    return {
        "status": "online",
        "device_count": len(device_manager.devices),
        "websocket_connections": len(WebSocketManager.clients),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_used_percent": mem.percent,
        },
        "server_time": datetime.utcnow().isoformat(),
    }


# --------------------------------------------------------------------------- #
# WEBSOCKET
# --------------------------------------------------------------------------- #
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await WebSocketManager.websocket_endpoint(ws)  # the manager now handles ping/pong


# --------------------------------------------------------------------------- #
# main (only when launched directly – uvicorn in Docker bypasses this)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
