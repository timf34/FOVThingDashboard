import asyncio
import json
import os
import time
from collections import defaultdict
from datetime import timezone
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional

from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials
from database import init_db
from device import DeviceManager
from relay import RelayManager
from config import FOVDashboardConfig
from websockets_manager import WebSocketManager

app = FastAPI()
SessionFactory = init_db()
device_manager = DeviceManager(SessionFactory)
config = FOVDashboardConfig()
relay_manager  = RelayManager()

# store send-timestamp per ping-id
_pending_pings: dict[str, float] = {}
PING_INTERVAL_S = 60          # one RTT measurement per minute
PING_TIMEOUT_S   = 120        # throw away unanswered pings after 2 min

# from awscrt import io
# io.init_logging(io.LogLevel.Trace, 'stderr')     # <— full wire‑level trace


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fovdashboard.com",
        "https://www.fovdashboard.com",
        "http://fovdashboard.com",
        "https://aviva.fovdashboard.com",
        "https://marvel.fovdashboard.com",
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


def message_handler(topic, payload, *a, **kw):
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


def latency_echo_handler(topic, payload, *a, **kw):
    try:
        message_str = payload.decode("utf-8")
        print(f"Received echo from topic '{topic}': {message_str}")
        
        msg = json.loads(message_str)
        ping_id = msg["ID"]
        
        # Try to get device ID from the payload first (new firmware)
        # If not available, try to extract from topic (old firmware format might be: esp32/{device_id}/echo)
        if "device_id" in msg:
            dev = msg["device_id"]
        else:
            # Try to extract from topic - format might be "esp32/echo" or "esp32/{device_id}/echo"
            parts = topic.split('/')
            if len(parts) >= 3:
                dev = parts[1]  # Assuming format like "esp32/{device_id}/echo"
            else:
                dev = "unknown"  # Fallback
                
        print(f"Echo from device: {dev}, ping ID: {ping_id}")

        if ping_id not in _pending_pings:
            print(f"Unknown ping ID: {ping_id}, ignoring")
            return                       # stale/unknown echo ➜ ignore

        rtt_ms = (time.time() - _pending_pings.pop(ping_id)) * 1000
        print(f"RTT {dev}: {rtt_ms:.1f} ms")

        # store + stream to front-end
        state = device_manager.update_device(dev, "latency", f"{rtt_ms:.2f}")
        asyncio.run(WebSocketManager.notify_clients(dev, state))

    except Exception as exc:
        print(f"latency-echo handler failed: {exc}")
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
    iot_client.subscribe(topic=config.latency_echo_topic, handler=latency_echo_handler)
    iot_client.subscribe(topic=config.relay_topic, handler=relay_handler)

    # latency  –  publish one ping per connected device every minute
    def ping_loop() -> None:
        import uuid
        while True:
            now = time.time()
            ping_id = str(uuid.uuid4())

            payload = json.dumps({"ID": ping_id, "ts": now})
            try:
                iot_client.publish(topic=config.latency_ping_topic, payload=payload)
                _pending_pings[ping_id] = now         # remember when we sent it
            except Exception as exc:
                print("latency-ping publish failed:", exc)

            time.sleep(PING_INTERVAL_S)

    Thread(target=ping_loop, name="latency-ping", daemon=True).start()


def relay_handler(topic, payload, *a, **kw):
    rid  = topic.split('/')[2]              # fov/relay/<id>/heartbeat
    pkt  = json.loads(payload.decode())
    relay_manager.upsert(rid, pkt)
    asyncio.run(
        WebSocketManager.notify_clients(f"relay:{rid}", relay_manager.relays[rid])
    )


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
        "server_time": datetime.utcnow().isoformat(),
        "relays": relay_manager.relays,
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

        # Send current state of all relays
        for rid, state in relay_manager.relays.items():
            try:
                await websocket.send_json({
                    "topic": f"relay:{rid}",
                    "message": jsonable_encoder(state)  
                })
            except Exception as e:
                print(f"Error sending initial relay data: {e}")

        
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

@app.get("/api/relays")
async def get_relays():
    """
    Return the in-memory relay state so the UI can show it
    without waiting for the next heartbeat.
    """
    # JSON-encode datetimes so the client can parse them
    return {
        rid: {
            **st,
            "last_seen": st["last_seen"].isoformat() + "Z" if isinstance(st["last_seen"], datetime) else st["last_seen"]
        }
        for rid, st in relay_manager.relays.items()
    }


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

async def check_system_status():
    """Periodic task to update device WiFi status *and* relay liveness"""
    while True:
        # --- devices ---------------------------------------------------
        changed = device_manager.check_wifi_status()
        for name in changed:
            await WebSocketManager.notify_clients(name, device_manager.devices[name])

        # --- relays  ----------------------------------------------------
        relay_manager.refresh()
        for rid, st in relay_manager.relays.items():
            if not st.get("_sent") or st["_sent"] != st["alive"]:
                await WebSocketManager.notify_clients(f"relay:{rid}", st)
                st["_sent"] = st["alive"]

        await asyncio.sleep(30)


@app.on_event("startup")
async def startup_event():
    # Start the AWS IoT client in a background thread
    iot_thread = Thread(target=start_iot_client)
    iot_thread.daemon = False   # ✅ make it non-daemon so it keeps container alive
    iot_thread.start()

    # Start the device status checker
    asyncio.create_task(check_system_status())

    async def _latency_housekeeping():
        while True:
            cutoff = time.time() - PING_TIMEOUT_S
            old = [k for k, ts in _pending_pings.items() if ts < cutoff]
            for k in old:
                _pending_pings.pop(k, None)
            await asyncio.sleep(PING_TIMEOUT_S)

    asyncio.create_task(_latency_housekeeping())



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
