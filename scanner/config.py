"""
Configuration loading for Raspberry Pi scanner nodes.

Reads nodes yaml and resolves the configuration for a specific node by
merging shared defaults with per node overrides.
"""

import copy
from dataclasses import dataclass, field

import yaml


@dataclass
class TagConfig:
    name: str
    mac: str


@dataclass
class KalmanConfig:
    process_variance: float = 3.0
    sensor_variance: float = 10.0
    initial_variance: float = 400.0


@dataclass
class DistanceConfig:
    reference_rssi: int = -54
    path_loss_exponent: float = 2.5


@dataclass
class ScannerConfig:
    room_name: str
    broker_host: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_client_id: str
    scan_duration_seconds: float
    utc_offset_hours: int
    kalman: KalmanConfig
    distance: DistanceConfig
    tags: list[TagConfig] = field(default_factory=list)


def load_config(path: str, hostname: str) -> ScannerConfig:
    """
    Load scanner config from nodes.yaml, resolving defaults for the given hostname.

    Merges the top level `defaults` section with the node specific overrides.
    Node values take precedence over defaults.

    Raises KeyError if the hostname is not listed under `nodes`.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    nodes = data.get("nodes", {})
    if hostname not in nodes:
        available = ", ".join(nodes.keys())
        raise KeyError(
            f"Hostname {hostname!r} not found in {path}. "
            f"Available nodes: {available}"
        )

    defaults = copy.deepcopy(data.get("defaults", {}))
    overrides = copy.deepcopy(nodes[hostname])

    # Deep-merge: node overrides win over defaults
    merged = _deep_merge(defaults, overrides)

    kalman_data = merged.get("kalman", {})
    distance_data = merged.get("distance", {})
    tags_data = merged.get("tags", [])

    return ScannerConfig(
        room_name=merged["room_name"],
        broker_host=merged["broker_host"],
        mqtt_port=merged.get("mqtt_port", 1883),
        mqtt_topic=merged.get("mqtt_topic", "testTopic"),
        mqtt_client_id=f"scanner_{hostname}",
        scan_duration_seconds=merged.get("scan_duration_seconds", 1.0),
        utc_offset_hours=merged.get("utc_offset_hours", 0),
        kalman=KalmanConfig(
            process_variance=kalman_data.get("process_variance", 3.0),
            sensor_variance=kalman_data.get("sensor_variance", 10.0),
            initial_variance=kalman_data.get("initial_variance", 400.0),
        ),
        distance=DistanceConfig(
            reference_rssi=distance_data.get("reference_rssi", -54),
            path_loss_exponent=distance_data.get("path_loss_exponent", 2.5),
        ),
        tags=[TagConfig(name=t["name"], mac=t["mac"].lower()) for t in tags_data],
    )


def _deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge overrides into base. Returns a new dict."""
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
