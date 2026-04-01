# BlueBot

## Overview

Indoor room level location tracking for BLE bracelet tags using a network of Raspberry Pi nodes. Each Pi is placed in a room and continuously scans for BLE tags worn on mobile objects. Distance is estimated from RSSI and smoothed with a Kalman filter. A central subscriber collects readings from all Pis over MQTT and determines which room each bracelet is in, logging confirmed transitions when the same room is detected consistently.

## System Architecture

```mermaid
flowchart LR
    subgraph Tags["Bracelet Tags"]
        T1["NUT1"] 
        T2["NUT2"] 
        T3["NUT3"]
    end

    subgraph Nodes["Raspberry Pi Nodes"]
        RPI1["ROOM1<br/><i>scanner.py</i>"]
        RPI2["ROOM2<br/><i>scanner.py</i>"]
        RPI3["ROOM3<br/><i>scanner.py</i>"]
    end

    subgraph PC["Central PC"]
        SUB["<i>subscriber.py</i>"]
        LOG["Logging.txt"]
        SUB -->|room confirmed| LOG
    end

    Tags -. "BLE" .-> Nodes
    Nodes -->|"MQTT"| SUB
```
