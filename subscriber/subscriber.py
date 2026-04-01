#!/usr/bin/env python3
"""
BlueBot central subscriber, runs on the collecting computer.
Connects to all Raspberry Pi MQTT brokers defined in nodes yaml,
listens for scan messages, and logs confirmed rooms to a text file.

Usage:
    python subscriber/subscriber.py config/subscriber.yaml
"""

import logging
import signal
import sys
import threading
from datetime import datetime

from shared.message import ScanMessage
from subscriber.config import SubscriberConfig, load_config
from subscriber.mqtt_client import ManagedMQTTClient
from subscriber.tag_tracker import TagTracker


def _setup_logging(log_file: str, debug_log_file: str) -> logging.Logger:
    logger = logging.getLogger("bluebot.subscriber")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # Console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # Main log — INFO and above (room transition events)
    main_fh = logging.FileHandler(log_file, mode="a")
    main_fh.setLevel(logging.INFO)
    main_fh.setFormatter(fmt)
    logger.addHandler(main_fh)

    # Debug log — everything
    debug_fh = logging.FileHandler(debug_log_file, mode="a")
    debug_fh.setLevel(logging.DEBUG)
    debug_fh.setFormatter(fmt)
    logger.addHandler(debug_fh)

    return logger


class Subscriber:
    """Connects to all Pi brokers and tracks room occupancy for each BLE tag."""

    def __init__(self, config: SubscriberConfig, logger: logging.Logger):
        self._config = config
        self._logger = logger
        self._stop_event = threading.Event()

        room_names = [b.room_name for b in config.brokers]

        # One TagTracker per tag
        self._trackers: dict[str, TagTracker] = {
            tag.name: TagTracker(
                tag_name=tag.name,
                room_names=room_names,
                debounce_count=config.debounce_count,
                logger=logger,
            )
            for tag in config.tags
        }

        # One ManagedMQTTClient per broker (one per Pi)
        self._clients: list[ManagedMQTTClient] = [
            ManagedMQTTClient(
                broker_host=broker.host,
                broker_port=broker.port,
                topic=config.topic,
                on_message_cb=self._on_message,
                logger=logger,
            )
            for broker in config.brokers
        ]

    def run(self) -> None:
        session_start = datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")
        self._logger.info("=== Session started %s ===", session_start)
        self._logger.info(
            "Listening on %d broker(s), tracking %d tag(s)",
            len(self._clients),
            len(self._trackers),
        )

        for client in self._clients:
            client.start()

        # Handle Ctrl-C gracefully
        signal.signal(signal.SIGINT, lambda *_: self.stop())
        signal.signal(signal.SIGTERM, lambda *_: self.stop())

        self._stop_event.wait()
        self._logger.info("Shutting down...")
        for client in self._clients:
            client.stop()

    def stop(self) -> None:
        self._stop_event.set()

    def _on_message(self, msg: ScanMessage) -> None:
        tracker = self._trackers.get(msg.tag)
        if tracker is None:
            self._logger.debug("Unknown tag %s ignoring", msg.tag)
            return

        self._logger.debug(
            "%s reports %s distance=%.2f", msg.room, msg.tag, msg.distance
        )

        confirmed_room = tracker.update(room_name=msg.room, distance=msg.distance)

        if confirmed_room is not None:
            self._logger.info(
                "%s confirmed in %s at %s", msg.tag, confirmed_room, msg.timestamp
            )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <path/to/subscriber.yaml>")
        sys.exit(1)

    subscriber_yaml = sys.argv[1]

    # Bootstrap a minimal logger before config is loaded
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    bootstrap_logger = logging.getLogger("bluebot.bootstrap")

    try:
        config = load_config(subscriber_yaml)
    except (FileNotFoundError, KeyError) as e:
        bootstrap_logger.error("Failed to load config: %s", e)
        sys.exit(1)

    logger = _setup_logging(config.log_file, config.debug_log_file)
    Subscriber(config, logger).run()


if __name__ == "__main__":
    main()
