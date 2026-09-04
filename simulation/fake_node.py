"""
Disaster Sentinel — Fake Node Simulator

Generates realistic LoRa packets for testing without hardware.
Used by SimulatedReceiver and standalone scenario testing.
"""

import struct
import random
import math
import time
from typing import Optional


# Must match packet_format.h
PACKET_HEADER_NORMAL = 0xAA
PACKET_HEADER_PRIORITY = 0xFF
PACKET_END_MARKER = 0x0D
HAZARD_FLOOD = 0x01
HAZARD_FIRE = 0x02
HAZARD_LANDSLIDE = 0x03
HAZARD_POLLUTION = 0x04


def calculate_crc16(data: bytes) -> int:
    """CRC-16 CCITT — must match firmware."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def _build_raw_packet(
    node_id: str,
    hazard_type: int,
    l1_raw: float, l1_anomaly: float,
    l2_raw: float, l2_anomaly: float,
    l3_raw: float, l3_anomaly: float,
    combined: float,
    rate_flag: int,
    battery: int,
    seq: int,
    priority: bool = False,
) -> bytes:
    """Build a raw binary packet matching the ESP32 format."""
    header = PACKET_HEADER_PRIORITY if priority else PACKET_HEADER_NORMAL
    l1_a = max(0, min(100, int(l1_anomaly * 100)))
    l2_a = max(0, min(100, int(l2_anomaly * 100)))
    l3_a = max(0, min(100, int(l3_anomaly * 100)))
    comb = max(0, min(100, int(combined * 100)))

    # Pack everything except CRC and end marker
    payload = struct.pack(
        '<B4sBfBfBfBBBBH',
        header,
        node_id.encode('ascii')[:4].ljust(4, b'\x00'),
        hazard_type,
        l1_raw, l1_a,
        l2_raw, l2_a,
        l3_raw, l3_a,
        comb, rate_flag,
        battery,
        seq & 0xFFFF,
    )

    crc = calculate_crc16(payload)
    packet = payload + struct.pack('<HB', crc, PACKET_END_MARKER)
    return packet


def create_normal_flood_packet(seq: int = 0) -> bytes:
    """Generate a normal (no anomaly) flood node packet."""
    water = 50.0 + random.gauss(0, 3)        # Normal ~50cm
    rain = 0.05 + random.gauss(0, 0.02)      # Light rain
    pressure = 1013.0 + random.gauss(0, 1)    # Normal pressure

    return _build_raw_packet(
        "FLD1", HAZARD_FLOOD,
        water, random.uniform(0.02, 0.12),
        rain, random.uniform(0.01, 0.08),
        pressure, random.uniform(0.01, 0.06),
        random.uniform(0.02, 0.10),
        0,  # stable
        random.randint(85, 98),
        seq,
    )


def create_normal_fire_packet(seq: int = 0) -> bytes:
    """Generate a normal fire node packet."""
    flame = 0.02 + random.gauss(0, 0.01)    # No flame
    gas = 0.08 + random.gauss(0, 0.03)      # Clean air
    temp = 28.0 + random.gauss(0, 2)        # Normal temp

    return _build_raw_packet(
        "FIR3", HAZARD_FIRE,
        max(0, flame), random.uniform(0.01, 0.08),
        max(0, gas), random.uniform(0.01, 0.06),
        temp, random.uniform(0.01, 0.05),
        random.uniform(0.01, 0.08),
        0,
        random.randint(82, 95),
        seq,
    )


def create_normal_landslide_packet(seq: int = 0) -> bytes:
    """Generate a normal landslide node packet."""
    tilt = 1.5 + random.gauss(0, 0.5)       # Normal slight tilt
    soil = 35.0 + random.gauss(0, 5)         # Normal moisture
    pressure = 1013.0 + random.gauss(0, 1)   # Normal pressure

    return _build_raw_packet(
        "SLD2", HAZARD_LANDSLIDE,
        max(0, tilt), random.uniform(0.02, 0.10),
        max(0, soil), random.uniform(0.01, 0.08),
        pressure, random.uniform(0.01, 0.05),
        random.uniform(0.02, 0.08),
        0,
        random.randint(82, 95),
        seq,
    )


def create_normal_pollution_packet(seq: int = 0) -> bytes:
    """Generate a normal pollution node packet (2-layer)."""
    aqi = 45.0 + random.gauss(0, 5)          # Clean AQI (~45)
    pm25 = 12.0 + random.gauss(0, 2)         # Normal PM2.5 (~12 ug/m3)

    l1_a = random.uniform(0.02, 0.12)
    l2_a = random.uniform(0.01, 0.10)
    combined = 0.55 * l1_a + 0.45 * l2_a

    return _build_raw_packet(
        "POL4", HAZARD_POLLUTION,
        max(0, aqi), l1_a,
        max(0, pm25), l2_a,
        0.0, 0.0,  # L3 not used for 2-layer node
        combined,
        0,
        random.randint(85, 98),
        seq,
    )


def create_flood_event_packet(seq: int, severity: float = 0.8) -> bytes:
    """Generate a flood-event packet with configurable severity."""
    water = 150 + severity * 150 + random.gauss(0, 5)   # Rising water
    rain = 0.6 + severity * 0.3 + random.gauss(0, 0.05)  # Heavy rain
    pressure = 1003 - severity * 8 + random.gauss(0, 1)   # Storm pressure

    l1_a = 0.5 + severity * 0.45 + random.gauss(0, 0.03)
    l2_a = 0.4 + severity * 0.50 + random.gauss(0, 0.04)
    l3_a = 0.3 + severity * 0.50 + random.gauss(0, 0.05)

    combined = 0.50 * l1_a + 0.30 * l2_a + 0.20 * l3_a

    return _build_raw_packet(
        "FLD1", HAZARD_FLOOD,
        water, min(1.0, max(0, l1_a)),
        rain, min(1.0, max(0, l2_a)),
        pressure, min(1.0, max(0, l3_a)),
        min(1.0, max(0, combined)),
        3 if severity > 0.6 else 1,  # rapid or rising
        random.randint(70, 90),
        seq,
        priority=(combined > 0.7),
    )


def create_fire_event_packet(seq: int, severity: float = 0.8) -> bytes:
    """Generate a fire-event packet."""
    flame = 0.5 + severity * 0.45 + random.gauss(0, 0.03)
    gas = 0.4 + severity * 0.50 + random.gauss(0, 0.04)
    temp = 35 + severity * 25 + random.gauss(0, 2)

    l1_a = 0.5 + severity * 0.45
    l2_a = 0.4 + severity * 0.50
    l3_a = 0.3 + severity * 0.50

    combined = 0.50 * l1_a + 0.30 * l2_a + 0.20 * l3_a

    return _build_raw_packet(
        "FIR3", HAZARD_FIRE,
        min(1.0, flame), min(1.0, max(0, l1_a)),
        min(1.0, gas), min(1.0, max(0, l2_a)),
        temp, min(1.0, max(0, l3_a)),
        min(1.0, max(0, combined)),
        3 if severity > 0.6 else 1,
        random.randint(70, 90),
        seq,
        priority=(combined > 0.7),
    )


def create_landslide_event_packet(seq: int, severity: float = 0.8) -> bytes:
    """Generate a landslide-event packet."""
    tilt = 5 + severity * 15 + random.gauss(0, 1)
    soil = 70 + severity * 25 + random.gauss(0, 3)
    pressure = 1005 - severity * 10 + random.gauss(0, 1)

    l1_a = 0.5 + severity * 0.45
    l2_a = 0.4 + severity * 0.45
    l3_a = 0.3 + severity * 0.45

    combined = 0.50 * l1_a + 0.30 * l2_a + 0.20 * l3_a

    return _build_raw_packet(
        "SLD2", HAZARD_LANDSLIDE,
        max(0, tilt), min(1.0, max(0, l1_a)),
        min(100, max(0, soil)), min(1.0, max(0, l2_a)),
        pressure, min(1.0, max(0, l3_a)),
        min(1.0, max(0, combined)),
        3 if severity > 0.6 else 1,
        random.randint(70, 90),
        seq,
        priority=(combined > 0.7),
    )


def create_pollution_event_packet(seq: int, severity: float = 0.8) -> bytes:
    """Generate a pollution-event packet (2-layer)."""
    aqi = 150 + severity * 250 + random.gauss(0, 10)     # Severe AQI (150-400+)
    pm25 = 80 + severity * 180 + random.gauss(0, 8)      # Severe PM2.5 (80-260+)

    l1_a = 0.5 + severity * 0.45
    l2_a = 0.4 + severity * 0.50
    combined = 0.55 * l1_a + 0.45 * l2_a

    return _build_raw_packet(
        "POL4", HAZARD_POLLUTION,
        max(0, aqi), min(1.0, max(0, l1_a)),
        max(0, pm25), min(1.0, max(0, l2_a)),
        0.0, 0.0,
        min(1.0, max(0, combined)),
        3 if severity > 0.6 else 1,
        random.randint(70, 90),
        seq,
        priority=(combined > 0.7),
    )
