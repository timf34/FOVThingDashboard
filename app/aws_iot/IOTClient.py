from __future__ import annotations

import threading
import time
from concurrent import futures
from typing import Optional, Callable

from awscrt import mqtt, exceptions as awscrt_exceptions          # 🆕  exceptions alias
from awsiot import mqtt_connection_builder

from aws_iot.IOTContext import IOTContext, IOTCredentials


class IOTClient:
    """
    Thin wrapper around the AWS‑CRT MQTT connection that

    * keeps one reconnect loop alive at a time
    * remembers the last subscribe handler so we can re‑subscribe after a reconnect
    * surfaces a simple `publish/subscribe` API
    """

    # instance attributes just for the type checker
    _mqtt_connection: mqtt.Connection
    context: IOTContext
    credentials: IOTCredentials

    # --- ctor --------------------------------------------------------------- #

    def __init__(
        self,
        context: IOTContext,
        credentials: IOTCredentials,
        subscribe_topic: str | None = None,
        publish_topic: str | None = None,
        ca_bytes: Optional[bytes] = None,
    ):
        self.context = context
        self.credentials = credentials

        self.subscribe_topic = subscribe_topic
        self.publish_topic = publish_topic

        self.connected: bool = False
        self._handler: Optional[Callable] = None
        self._reconnect_lock = threading.Lock()
        self._reconnect_thread: Optional[threading.Thread] = None

        print(
            f"Creating IOTClient with subscribe topic: {self.subscribe_topic} "
            f"and publish topic: {self.publish_topic}"
        )

        self._mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.credentials.endpoint,
            port=self.credentials.port,
            cert_filepath=self.credentials.cert_path,
            pri_key_filepath=self.credentials.priv_key_path,
            ca_filepath=self.credentials.ca_path,
            ca_bytes=ca_bytes,
            client_bootstrap=self.context.client_bootstrap,
            on_connection_interrupted=self._on_conn_interrupted,
            on_connection_resumed=self._on_conn_resumed,
            client_id=self.credentials.client_id,
            clean_session=False,
            keep_alive_secs=30,
        )

    # --- public helpers ----------------------------------------------------- #

    def connect(self) -> futures.Future:
        print(
            f"Connecting to endpoint '{self.credentials.endpoint}' "
            f"with client ID '{self.credentials.client_id}'"
        )
        fut = self._mqtt_connection.connect()
        fut.result()  # block
        self.connected = True
        print("Successfully connected")
        return fut

    def disconnect(self) -> futures.Future:
        print("Disconnecting")
        fut = self._mqtt_connection.disconnect()
        fut.result()
        self.connected = False
        return fut

    # ----------------------------------------------------------------------- #

    def publish(self, topic: str | None = None, payload: str | None = None) -> Optional[futures.Future]:
        if not self.connected:
            print("Not connected – publish skipped")
            return None

        topic = topic or self.publish_topic
        if topic is None:
            raise ValueError("No publish topic provided")

        if payload is None:
            print("Empty payload – publish skipped")

        fut, packet_id = self._mqtt_connection.publish(
            topic=topic, payload=payload, qos=mqtt.QoS.AT_MOST_ONCE
        )
        print(f"Published to '{topic}' (id={packet_id})")
        return fut

    def subscribe(self, topic: str | None = None, handler: Callable | None = None) -> futures.Future:
        topic = topic or self.subscribe_topic
        if topic is None:
            raise ValueError("No subscribe topic provided")

        if handler is None:
            print("⚠  Subscribing without a handler – incoming messages will be dropped")
        else:
            self._handler = handler    # 🆕 remember for re‑subscribe

        fut, packet_id = self._mqtt_connection.subscribe(
            topic=topic, qos=mqtt.QoS.AT_MOST_ONCE, callback=handler
        )
        qos = fut.result()["qos"]
        print(f"Subscribed to '{topic}' (id={packet_id}, qos={qos})")
        return fut

    # --- internal callbacks ------------------------------------------------- #

    def _on_conn_interrupted(self, connection, error, **kwargs):
        print("MQTT connection interrupted:", error)
        self.connected = False

        # ensure only ONE reconnect loop is running
        with self._reconnect_lock:
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                return  # already trying
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop, daemon=True
            )
            self._reconnect_thread.start()

    def _on_conn_resumed(self, connection, return_code, session_present, **kwargs):
        """Called by CRT after it automatically reconnects."""
        print("MQTT connection resumed – session_present =", session_present)
        self.connected = True

        # If the broker did NOT persist our session we must re‑subscribe
        if not session_present and self.subscribe_topic and self._handler:
            try:
                self.subscribe(self.subscribe_topic, handler=self._handler)
            except Exception as exc:
                print("Re‑subscribe failed:", exc)

    # --- reconnect loop ----------------------------------------------------- #

    def _reconnect_loop(self):
        """Background task started after an interruption."""
        while not self.connected:
            try:
                print("Trying to reconnect …")
                self._mqtt_connection.reconnect().result()
                print("Re‑connected; resubscribing")
                if self.subscribe_topic and self._handler:
                    self.subscribe(self.subscribe_topic, handler=self._handler)
                self.connected = True
            except awscrt_exceptions.AwsCrtError as e:
                print("Reconnect failed:", e)
                time.sleep(5)
