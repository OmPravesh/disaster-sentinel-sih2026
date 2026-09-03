/**
 * Disaster Sentinel — Shared LoRa Packet Format
 * 
 * Defines the binary packet structure used for communication
 * between ESP32 field nodes and the Jetson LoRa receiver.
 * 
 * This header is shared between all firmware projects.
 * 
 * Packet Structure (29 bytes total):
 * ───────────────────────────────────────────
 * Byte 0:        Header (0xAA=normal, 0xFF=priority)
 * Bytes 1-4:     Node ID (4 ASCII chars, e.g., "FLD1")
 * Byte 5:        Hazard type (0x01=FLOOD, 0x02=FIRE, 0x03=LANDSLIDE)
 * Bytes 6-9:     L1 raw value (float, 4 bytes)
 * Byte 10:       L1 anomaly score (uint8, 0-100 → 0.0-1.0)
 * Bytes 11-14:   L2 raw value (float, 4 bytes)
 * Byte 15:       L2 anomaly score (uint8, 0-100)
 * Bytes 16-19:   L3 raw value (float, 4 bytes)
 * Byte 20:       L3 anomaly score (uint8, 0-100)
 * Byte 21:       Combined 3-layer score (uint8, 0-100)
 * Byte 22:       Rate flag (0=stable, 1=rising, 2=falling, 3=rapid)
 * Byte 23:       Battery percentage (uint8, 0-100)
 * Bytes 24-25:   Sequence number (uint16, little-endian)
 * Bytes 26-27:   CRC-16 (CCITT)
 * Byte 28:       End marker (0x0D)
 * ───────────────────────────────────────────
 */

#ifndef PACKET_FORMAT_H
#define PACKET_FORMAT_H

#include <Arduino.h>

// Packet constants
#define PACKET_SIZE           29
#define PACKET_HEADER_NORMAL  0xAA
#define PACKET_HEADER_PRIORITY 0xFF
#define PACKET_END_MARKER     0x0D

// Hazard type codes
#define HAZARD_FLOOD     0x01
#define HAZARD_FIRE      0x02
#define HAZARD_LANDSLIDE 0x03

// Packet structure (packed to ensure exact byte layout)
#pragma pack(push, 1)
typedef struct {
    uint8_t  header;          // 0xAA or 0xFF
    char     nodeId[4];       // e.g., "FLD1"
    uint8_t  hazardType;      // HAZARD_FLOOD, HAZARD_FIRE, HAZARD_LANDSLIDE
    float    l1Raw;           // Layer 1 raw sensor value
    uint8_t  l1Anomaly;       // Layer 1 anomaly (0-100)
    float    l2Raw;           // Layer 2 raw sensor value
    uint8_t  l2Anomaly;       // Layer 2 anomaly (0-100)
    float    l3Raw;           // Layer 3 raw sensor value (e.g., pressure)
    uint8_t  l3Anomaly;       // Layer 3 anomaly (0-100)
    uint8_t  combinedScore;   // 3-layer combined (0-100)
    uint8_t  rateFlag;        // 0=stable, 1=rising, 2=falling, 3=rapid
    uint8_t  battery;         // Battery percentage (0-100)
    uint16_t seqNum;          // Sequence number (little-endian)
    uint16_t crc;             // CRC-16 CCITT
    uint8_t  endMarker;       // 0x0D
} SentinelPacket;
#pragma pack(pop)

/**
 * Utility: Convert float anomaly score (0.0-1.0) to uint8 (0-100)
 */
inline uint8_t anomalyToUint8(float score) {
    int val = (int)(score * 100.0f + 0.5f);
    if (val < 0) val = 0;
    if (val > 100) val = 100;
    return (uint8_t)val;
}

/**
 * Utility: Convert uint8 (0-100) back to float anomaly score (0.0-1.0)
 */
inline float uint8ToAnomaly(uint8_t val) {
    return val / 100.0f;
}

/**
 * Calculate CRC-16 CCITT for a buffer.
 * @param data  Pointer to data
 * @param len   Length in bytes
 * @return CRC-16 value
 */
inline uint16_t calculateCRC16(const uint8_t* data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

/**
 * Build a SentinelPacket from field values.
 */
inline SentinelPacket buildPacket(
    const char* nodeId,
    uint8_t hazardType,
    float l1Raw, float l1Anom,
    float l2Raw, float l2Anom,
    float l3Raw, float l3Anom,
    float combinedScore,
    uint8_t rateFlag,
    uint8_t battery,
    uint16_t seqNum,
    bool isPriority
) {
    SentinelPacket pkt;
    
    pkt.header = isPriority ? PACKET_HEADER_PRIORITY : PACKET_HEADER_NORMAL;
    memcpy(pkt.nodeId, nodeId, 4);
    pkt.hazardType = hazardType;
    pkt.l1Raw = l1Raw;
    pkt.l1Anomaly = anomalyToUint8(l1Anom);
    pkt.l2Raw = l2Raw;
    pkt.l2Anomaly = anomalyToUint8(l2Anom);
    pkt.l3Raw = l3Raw;
    pkt.l3Anomaly = anomalyToUint8(l3Anom);
    pkt.combinedScore = anomalyToUint8(combinedScore);
    pkt.rateFlag = rateFlag;
    pkt.battery = battery;
    pkt.seqNum = seqNum;
    
    // Calculate CRC over everything except CRC field and end marker
    pkt.crc = calculateCRC16((const uint8_t*)&pkt, offsetof(SentinelPacket, crc));
    pkt.endMarker = PACKET_END_MARKER;
    
    return pkt;
}

/**
 * Validate a received packet's CRC.
 */
inline bool validatePacketCRC(const SentinelPacket& pkt) {
    uint16_t expected = calculateCRC16((const uint8_t*)&pkt, offsetof(SentinelPacket, crc));
    return (pkt.crc == expected) && (pkt.endMarker == PACKET_END_MARKER);
}

#endif // PACKET_FORMAT_H
