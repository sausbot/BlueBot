import logging
import time
from dataclasses import dataclass

from bluepy.btle import Scanner, BTLEException


@dataclass
class ScanResult:
    mac: str
    rssi: int


class BLEScanner:
    """
    Wraps bluepy Scanner with restart on failure logic.

    BLE adapters on Raspberry Pi can enter a bad state and raise BTLEException.
    This class catches those errors, logs them, and re-initializes the scanner
    so the scan loop keeps running without manual intervention.
    """

    _RESTART_DELAY_SECONDS = 5.0

    def __init__(self, scan_duration: float, logger: logging.Logger):
        self._scan_duration = scan_duration
        self._logger = logger
        self._scanner = Scanner()

    def scan_once(self) -> list[ScanResult]:
        """
        Run a single BLE scan and return results for all visible devices.

        Returns an empty list if the scan produces no results.
        Raises BTLEException on hardware failure (caller should handle restart).
        """
        devices = self._scanner.scan(self._scan_duration)
        return [ScanResult(mac=dev.addr, rssi=dev.rssi) for dev in devices]

    def run(self, callback) -> None:
        """
        Run the scan loop indefinitely, calling callback(list[ScanResult]) each cycle.

        Restarts the bluepy Scanner on BTLEException so transient hardware
        errors do not terminate the program.
        """
        while True:
            try:
                results = self.scan_once()
                callback(results)
            except BTLEException as e:
                self._logger.warning(
                    "BLE scan failed: %s restarting scanner in %ds",
                    e,
                    self._RESTART_DELAY_SECONDS,
                )
                time.sleep(self._RESTART_DELAY_SECONDS)
                self._scanner = Scanner()
            except Exception as e:
                self._logger.error(
                    "Unexpected error in scan loop: %s", e, exc_info=True
                )
                time.sleep(self._RESTART_DELAY_SECONDS)
