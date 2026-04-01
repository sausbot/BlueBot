import logging
from typing import Callable

import paho.mqtt.client as mqtt

from shared.message import ScanMessage


class ManagedMQTTClient:
    """
    MQTT client for one broker (one Raspberry Pi) with auto reconnect.

    Paho handles TCP reconnect internally via reconnect_delay_set.
    The on_connect callback re-subscribes to the topic after every connection
    so messages resume automatically after a broker restart.
    """

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topic: str,
        on_message_cb: Callable[[ScanMessage], None],
        logger: logging.Logger,
    ):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._topic = topic
        self._on_message_cb = on_message_cb
        self._logger = logger

        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # Reconnect with exponential back-off: 1s min, 30s max
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def start(self) -> None:
        self._logger.info(
            "Connecting to broker %s:%d", self._broker_host, self._broker_port
        )
        self._client.connect(self._broker_host, self._broker_port, keepalive=60)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._logger.info(
                "Connected to %s:%d, subscribing to %s",
                self._broker_host,
                self._broker_port,
                self._topic,
            )
            client.subscribe(self._topic)
        else:
            self._logger.warning(
                "Connection to %s:%d failed (rc=%d)",
                self._broker_host,
                self._broker_port,
                rc,
            )

    def _on_disconnect(self, client, userdata, rc) -> None:
        if rc != 0:
            self._logger.warning(
                "Disconnected from %s:%d (rc=%d), paho will reconnect",
                self._broker_host,
                self._broker_port,
                rc,
            )

    def _on_message(self, client, userdata, msg) -> None:
        raw = msg.payload.decode(errors="replace")
        try:
            scan_msg = ScanMessage.parse(raw)
        except ValueError as e:
            self._logger.warning(
                "Unparseable message from %s: %s", self._broker_host, e
            )
            return
        self._on_message_cb(scan_msg)
