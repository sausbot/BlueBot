import logging

import paho.mqtt.client as mqtt


class MQTTPublisher:
    """
    Persistent MQTT publisher for a scanner node.

    This class maintains one persistent connection and reconnects only when needed.
    """

    def __init__(self, broker_host: str, broker_port: int, client_id: str, logger: logging.Logger):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._logger = logger
        self._client = mqtt.Client(client_id=client_id)
        self._client.on_disconnect = self._on_disconnect
        self._connected = False

    def connect(self) -> None:
        self._client.connect(self._broker_host, self._broker_port, keepalive=60)
        self._client.loop_start()
        self._connected = True
        self._logger.info("Connected to MQTT broker %s:%d", self._broker_host, self._broker_port)

    def publish(self, topic: str, message: str) -> None:
        if not self._connected:
            self._logger.warning("Not connected, attempting reconnect before publish")
            self._reconnect()
        self._client.publish(topic, message)

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected = False
        if rc != 0:
            self._logger.warning("Unexpected MQTT disconnect (rc=%d)", rc)

    def _reconnect(self) -> None:
        try:
            self._client.reconnect()
            self._connected = True
            self._logger.info("Reconnected to MQTT broker")
        except Exception as e:
            self._logger.error("Reconnect failed: %s", e)
