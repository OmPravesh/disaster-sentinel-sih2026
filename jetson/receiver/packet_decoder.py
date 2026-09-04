"""
Disaster Sentinel — LoRa Packet Decoder

Parses binary SentinelPacket data from LoRa receiver into
structured Python objects. Validates CRC and packet integrity.

Mirrors the packet_format.h struct from ESP32 firmware.
"""

import struct
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


# Hazard type constants (must match firmware)
HAZARD_FLOOD = 0x01
HAZARD_FIRE = 0x02
HAZARD_LANDSLIDE = 0x03
HAZARD_POLLUTION = 0x04

HAZARD_NAMES = {
    HAZARD_FLOOD: "FLOOD",
    HAZARD_FIRE: "FIRE",
    HAZARD_LANDSLIDE: "LANDSLIDE",
    HAZARD_POLLUTION: "POLLUTION",
}

# Packet constants
PACKET_SIZE = 29
PACKET_HEADER_NORMAL = 0xAA
PACKET_HEADER_PRIORITY = 0xFF
PACKET_END_MARKER = 0x0D

# Rate flag meanings
RATE_FLAGS = {
    0: "stable",
    1: "rising",
    2: "falling",
    3: "rapid",
}


@dataclass
class DecodedPacket:
    """Decoded LoRa packet from an ESP32 field node."""
    # Header
    is_priority: bool
    
    # Node identification
    node_id: str
    hazard_type: int
    hazard_name: str
    
    # Layer 1 — Primary sensor
    l1_raw: float
    l1_anomaly: float  # 0.0 - 1.0
    
    # Layer 2 — Corroborating sensor
    l2_raw: float
    l2_anomaly: float  # 0.0 - 1.0
    
    # Layer 3 — Environmental context
    l3_raw: float
    l3_anomaly: float  # 0.0 - 1.0
    
    # Combined 3-layer analysis
    combined_score: float  # 0.0 - 1.0
    rate_flag: int
    rate_name: str
    
    # Metadata
    battery: int  # 0-100%
    seq_num: int
    
    # Validation
    crc_valid: bool
    
    # Timestamp (added at receive time)
    received_at: datetime = None
    rssi: int = 0  # Signal strength
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "is_priority": self.is_priority,
            "node_id": self.node_id,
            "hazard_type": self.hazard_type,
            "hazard_name": self.hazard_name,
            "l1_raw": round(self.l1_raw, 3),
            "l1_anomaly": round(self.l1_anomaly, 3),
            "l2_raw": round(self.l2_raw, 3),
            "l2_anomaly": round(self.l2_anomaly, 3),
            "l3_raw": round(self.l3_raw, 3),
            "l3_anomaly": round(self.l3_anomaly, 3),
            "combined_score": round(self.combined_score, 3),
            "rate_flag": self.rate_flag,
            "rate_name": self.rate_name,
            "battery": self.battery,
            "seq_num": self.seq_num,
            "crc_valid": self.crc_valid,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "rssi": self.rssi,
        }


def calculate_crc16(data: bytes) -> int:
    """
    Calculate CRC-16 CCITT.
    Must match the firmware's calculateCRC16() function.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF  # Keep as 16-bit
    return crc


def decode_packet(raw_bytes: bytes, rssi: int = 0) -> Optional[DecodedPacket]:
    """
    Decode a raw LoRa packet into a DecodedPacket.
    
    Args:
        raw_bytes: Raw bytes received from LoRa (should be PACKET_SIZE bytes)
        rssi: RSSI of the received packet
        
    Returns:
        DecodedPacket if valid, None if packet is malformed
    """
    if len(raw_bytes) < PACKET_SIZE:
        print(f"[Decoder] Packet too short: {len(raw_bytes)} bytes (expected {PACKET_SIZE})")
        return None
    
    # Use only first PACKET_SIZE bytes
    data = raw_bytes[:PACKET_SIZE]
    
    # Check end marker
    if data[-1] != PACKET_END_MARKER:
        print(f"[Decoder] Invalid end marker: 0x{data[-1]:02X}")
        return None
    
    # Check header
    header = data[0]
    if header not in (PACKET_HEADER_NORMAL, PACKET_HEADER_PRIORITY):
        print(f"[Decoder] Invalid header: 0x{header:02X}")
        return None
    
    # Unpack the binary structure
    # Format: B 4s B f B f B f B B B B H H B
    # (matches the C struct with pack(1))
    try:
        unpacked = struct.unpack('<B4sBfBfBfBBBBHHB', data)
    except struct.error as e:
        print(f"[Decoder] Struct unpack error: {e}")
        return None
    
    (header, node_id_bytes, hazard_type,
     l1_raw, l1_anom, l2_raw, l2_anom, l3_raw, l3_anom,
     combined, rate_flag, battery, seq_num,
     received_crc, end_marker) = unpacked
    
    # Validate CRC (computed over everything before the CRC field)
    crc_data = data[:26]  # Everything up to but not including CRC (2 bytes) and end marker (1 byte)
    expected_crc = calculate_crc16(crc_data)
    crc_valid = (received_crc == expected_crc)
    
    if not crc_valid:
        print(f"[Decoder] CRC mismatch: received=0x{received_crc:04X}, "
              f"expected=0x{expected_crc:04X}")
    
    # Decode node ID
    node_id = node_id_bytes.decode('ascii', errors='replace').strip('\x00')
    
    # Convert uint8 anomaly scores to float (0-100 → 0.0-1.0)
    hazard_name = HAZARD_NAMES.get(hazard_type, f"UNKNOWN(0x{hazard_type:02X})")
    rate_name = RATE_FLAGS.get(rate_flag, f"unknown({rate_flag})")
    
    return DecodedPacket(
        is_priority=(header == PACKET_HEADER_PRIORITY),
        node_id=node_id,
        hazard_type=hazard_type,
        hazard_name=hazard_name,
        l1_raw=l1_raw,
        l1_anomaly=l1_anom / 100.0,
        l2_raw=l2_raw,
        l2_anomaly=l2_anom / 100.0,
        l3_raw=l3_raw,
        l3_anomaly=l3_anom / 100.0,
        combined_score=combined / 100.0,
        rate_flag=rate_flag,
        rate_name=rate_name,
        battery=battery,
        seq_num=seq_num,
        crc_valid=crc_valid,
        received_at=datetime.now(),
        rssi=rssi,
    )


def format_packet_log(pkt: DecodedPacket) -> str:
    """Format a decoded packet for console logging."""
    priority_tag = "🔴 PRIORITY" if pkt.is_priority else "🟢 NORMAL"
    return (
        f"[{priority_tag}] {pkt.node_id} | {pkt.hazard_name} | "
        f"L1={pkt.l1_raw:.1f}(a{pkt.l1_anomaly:.2f}) "
        f"L2={pkt.l2_raw:.1f}(a{pkt.l2_anomaly:.2f}) "
        f"L3={pkt.l3_raw:.1f}(a{pkt.l3_anomaly:.2f}) | "
        f"Combined={pkt.combined_score:.2f} | Rate={pkt.rate_name} | "
        f"Bat={pkt.battery}% | Seq={pkt.seq_num} | "
        f"RSSI={pkt.rssi}dBm | CRC={'✅' if pkt.crc_valid else '❌'}"
    )
