import logging
import threading


class TagTracker:
    """
    Thread safe state machine tracking which room a single BLE tag is in.

    Three rooms (or however many are configured) each report a distance to this
    tag. Once the same "closest room" is seen `debounce_count` times in a row,
    the room transition is confirmed and logged.
    """

    def __init__(
        self,
        tag_name: str,
        room_names: list[str],
        debounce_count: int,
        logger: logging.Logger,
    ):
        self._tag_name = tag_name
        self._room_names = room_names
        self._debounce_count = debounce_count
        self._logger = logger
        self._lock = threading.Lock()

        # Distance per room, inf means "not yet seen"
        self._distances: dict[str, float] = {r: float("inf") for r in room_names}
        self._prev_room: str | None = None
        self._candidate_room: str | None = None
        self._candidate_count: int = 0

    def update(self, room_name: str, distance: float) -> str | None:
        """
        Record a distance reading from one room. Returns the confirmed new room
        name if a transition is committed, otherwise None.
        """
        with self._lock:
            self._distances[room_name] = distance

            # Don't make room decisions until every room has reported at least once
            if any(d == float("inf") for d in self._distances.values()):
                return None

            closest_room = min(self._distances, key=lambda r: self._distances[r])
            self._logger.debug(
                "%s distances=%s closest=%s",
                self._tag_name,
                self._distances,
                closest_room,
            )

            if closest_room == self._prev_room:
                # Still in the confirmed room, decay any partial candidate count
                if self._candidate_count > 0:
                    self._candidate_count -= 1
                return None

            # Closest room differs from confirmed room
            if closest_room != self._candidate_room:
                # New candidate, reset counter
                self._candidate_room = closest_room
                self._candidate_count = 1
            else:
                self._candidate_count += 1

            self._logger.debug(
                "%s candidate=%s count=%d/%d",
                self._tag_name,
                self._candidate_room,
                self._candidate_count,
                self._debounce_count,
            )

            if self._candidate_count >= self._debounce_count:
                confirmed = self._candidate_room
                self._prev_room = confirmed
                self._candidate_room = None
                self._candidate_count = 0
                return confirmed

            return None

    def current_room(self) -> str | None:
        with self._lock:
            return self._prev_room
