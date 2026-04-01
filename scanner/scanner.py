import logging
import socket
import sys
from datetime import datetime, timedelta

from scanner.ble_scanner import BLEScanner, ScanResult
from scanner.config import ScannerConfig, TagConfig, load_config
from scanner.kalman import KalmanFilter
from scanner.mqtt_publisher import MQTTPublisher
from shared.message import ScanMessage


def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("bluebot.scanner")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger


class ScannerNode:
    """Orchestrates BLE scanning, Kalman filtering, and MQTT publishing for one room."""

    def __init__(self, config: ScannerConfig, logger: logging.Logger):
        self._config = config
        self._logger = logger

        # One KalmanFilter instance per tag (keyed by MAC address)
        self._filters: dict[str, KalmanFilter] = {
            tag.mac: KalmanFilter(
                process_variance=config.kalman.process_variance,
                sensor_variance=config.kalman.sensor_variance,
                initial_variance=config.kalman.initial_variance,
            )
            for tag in config.tags
        }

        # MAC -> TagConfig lookup
        self._tags_by_mac: dict[str, TagConfig] = {tag.mac: tag for tag in config.tags}

        self._ble = BLEScanner(
            scan_duration=config.scan_duration_seconds,
            logger=logger,
        )
        self._publisher = MQTTPublisher(
            broker_host=config.broker_host,
            broker_port=config.mqtt_port,
            client_id=config.mqtt_client_id,
            logger=logger,
        )

    def run(self) -> None:
        self._logger.info(
            "Starting scanner node: room=%s broker=%s:%d",
            self._config.room_name,
            self._config.broker_host,
            self._config.mqtt_port,
        )
        self._publisher.connect()
        self._ble.run(self._on_scan_results)

    def _on_scan_results(self, results: list[ScanResult]) -> None:
        for result in results:
            mac = result.mac.lower()
            if mac not in self._tags_by_mac:
                continue

            tag = self._tags_by_mac[mac]
            kf = self._filters[mac]

            raw_distance = self._calculate_distance(result.rssi)
            filtered_distance = kf.update(raw_distance)

            timestamp = (
                datetime.now() + timedelta(hours=self._config.utc_offset_hours)
            ).strftime("%H:%M:%S")

            msg = ScanMessage(
                room=self._config.room_name,
                tag=tag.name,
                rssi=result.rssi,
                distance=filtered_distance,
                timestamp=timestamp,
            )

            payload = msg.serialize()
            self._logger.debug(payload)
            self._publisher.publish(self._config.mqtt_topic, payload)

    def _calculate_distance(self, rssi: int) -> float:
        """Convert RSSI to metres using the log distance path loss model."""
        ref = self._config.distance.reference_rssi
        n = self._config.distance.path_loss_exponent
        return round(10 ** ((ref - rssi) / (10 * n)), 2)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: sudo python {sys.argv[0]} <path/to/nodes.yaml>")
        sys.exit(1)

    nodes_yaml = sys.argv[1]
    hostname = socket.gethostname()
    logger = _setup_logging()

    try:
        config = load_config(nodes_yaml, hostname)
    except KeyError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    ScannerNode(config, logger).run()


if __name__ == "__main__":
    main()
