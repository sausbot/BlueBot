import os
from dataclasses import dataclass, field

import yaml


@dataclass
class BrokerConfig:
    host: str
    port: int
    room_name: str
    client_id: str


@dataclass
class TagDef:
    name: str


@dataclass
class SubscriberConfig:
    topic: str
    debounce_count: int
    log_file: str
    debug_log_file: str
    brokers: list[BrokerConfig] = field(default_factory=list)
    tags: list[TagDef] = field(default_factory=list)


def load_config(subscriber_yaml: str) -> SubscriberConfig:
    """
    Load subscriber config, deriving the broker list from nodes yaml"""
    with open(subscriber_yaml) as f:
        data = yaml.safe_load(f)

    # Resolve nodes_config path relative to subscriber.yaml's directory
    nodes_yaml_path = data["nodes_config"]
    if not os.path.isabs(nodes_yaml_path):
        base_dir = os.path.dirname(os.path.abspath(subscriber_yaml))
        nodes_yaml_path = os.path.normpath(os.path.join(base_dir, "..", nodes_yaml_path))

    with open(nodes_yaml_path) as f:
        nodes_data = yaml.safe_load(f)

    defaults = nodes_data.get("defaults", {})
    nodes = nodes_data.get("nodes", {})
    default_port = defaults.get("mqtt_port", 1883)

    brokers = [
        BrokerConfig(
            host=node_cfg["broker_host"],
            port=node_cfg.get("mqtt_port", default_port),
            room_name=node_cfg["room_name"],
            client_id=f"sub_{hostname}",
        )
        for hostname, node_cfg in nodes.items()
    ]

    tags = [TagDef(name=t["name"]) for t in data.get("tags", [])]

    return SubscriberConfig(
        topic=data.get("topic", "testTopic"),
        debounce_count=data.get("debounce_count", 12),
        log_file=data.get("log_file", "Logging.txt"),
        debug_log_file=data.get("debug_log_file", "SubLog.txt"),
        brokers=brokers,
        tags=tags,
    )
