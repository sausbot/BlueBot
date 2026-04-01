class KalmanFilter:
    """
    One dimensional Kalman filter for smoothing distance measurements.

    Each BLE tag gets its own KalmanFilter instance so state (_pos, _var)
    is independent per tag.

    Usage:
        kf = KalmanFilter(process_variance=3.0, sensor_variance=10.0, initial_variance=400.0)
        smoothed = kf.update(raw_distance)
    """

    def __init__(
        self, process_variance: float, sensor_variance: float, initial_variance: float
    ):
        self._process_var = process_variance
        self._sensor_var = sensor_variance
        self._var = initial_variance
        self._pos = 0.0

    def update(self, measurement: float) -> float:
        """Apply one predict→correct cycle and return the filtered estimate."""
        # Predict: grow uncertainty by process noise
        self._var += self._process_var

        # Correct: blend prior estimate with new measurement weighted by uncertainty
        self._pos = (self._var * measurement + self._sensor_var * self._pos) / (
            self._var + self._sensor_var
        )
        self._var = (self._var * self._sensor_var) / (self._var + self._sensor_var)

        return self._pos
