from dataclasses import dataclass


@dataclass
class ScanMessage:
    """
    A single BLE scan result published by a scanner node.

    Wire format (preserved from original):
        "ROOM1 NUT1 RSSI -60 DISTANCE 1.58 TIME 14:32:45"
    """

    room: str
    tag: str
    rssi: int
    distance: float
    timestamp: str

    def serialize(self) -> str:
        return "ROOM{} {} RSSI {} DISTANCE {:3.2f} TIME {}".format(
            self.room, self.tag, self.rssi, self.distance, self.timestamp
        )

    @classmethod
    def parse(cls, raw: str) -> "ScanMessage":
        """Parse a wire format string into a ScanMessage"""
        try:
            parts = raw.strip().split()
            # parts: [room, tag, "RSSI", rssi_val, "DISTANCE", dist_val, "TIME", time_val]
            if len(parts) != 8:
                raise ValueError(f"Expected 8 tokens, got {len(parts)}")
            return cls(
                room=parts[0],
                tag=parts[1],
                rssi=int(parts[3]),
                distance=float(parts[5]),
                timestamp=parts[7],
            )
        except (IndexError, ValueError) as e:
            raise ValueError(f"Cannot parse ScanMessage from {raw!r}: {e}") from e
