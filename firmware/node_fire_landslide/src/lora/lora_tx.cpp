/**
 * Disaster Sentinel — LoRa Transmitter Implementation
 * 
 * SX1278 LoRa module driver for field node packet transmission.
 */

#include "lora_tx.h"

bool LoRaTx::begin(int csPin, int rstPin, int dio0Pin,
                    long frequency, int txPower, int sf, long bandwidth) {
    _packetsSent = 0;
    _initialized = false;

    // Configure LoRa pins
    LoRa.setPins(csPin, rstPin, dio0Pin);

    Serial.println("[LoRa TX] Initializing...");
    Serial.printf("  Frequency: %.1f MHz\n", frequency / 1e6);
    Serial.printf("  TX Power: %d dBm\n", txPower);
    Serial.printf("  SF: %d\n", sf);

    // Initialize LoRa module
    if (!LoRa.begin(frequency)) {
        Serial.println("[LoRa TX] ERROR: Init failed! Check wiring.");
        return false;
    }

    // Configure parameters
    LoRa.setTxPower(txPower);
    LoRa.setSpreadingFactor(sf);
    LoRa.setSignalBandwidth(bandwidth);
    LoRa.setCodingRate4(5);           // Coding rate 4/5
    LoRa.enableCrc();                  // Enable CRC at LoRa level too
    LoRa.setSyncWord(0xF3);           // Custom sync word for our network

    _initialized = true;
    Serial.println("[LoRa TX] Initialized successfully");

    return true;
}

bool LoRaTx::sendPacket(const SentinelPacket& pkt) {
    if (!_initialized) {
        Serial.println("[LoRa TX] ERROR: Not initialized");
        return false;
    }

    // Send packet as raw bytes
    LoRa.beginPacket();
    LoRa.write((const uint8_t*)&pkt, sizeof(SentinelPacket));
    LoRa.endPacket(true);  // true = async (non-blocking)

    _packetsSent++;

    // Debug output
    Serial.printf("[LoRa TX] Packet #%u sent | Node: %.4s | Hazard: 0x%02X | "
                  "L1=%.1f(a%d) L2=%.1f(a%d) L3=%.1f(a%d) | "
                  "Combined: %d | Rate: %d | Bat: %d%%\n",
                  _packetsSent,
                  pkt.nodeId,
                  pkt.hazardType,
                  pkt.l1Raw, pkt.l1Anomaly,
                  pkt.l2Raw, pkt.l2Anomaly,
                  pkt.l3Raw, pkt.l3Anomaly,
                  pkt.combinedScore,
                  pkt.rateFlag,
                  pkt.battery);

    return true;
}

bool LoRaTx::sendRaw(const uint8_t* data, size_t len) {
    if (!_initialized) return false;

    LoRa.beginPacket();
    LoRa.write(data, len);
    LoRa.endPacket(true);

    return true;
}

int LoRaTx::getLastRSSI() {
    return LoRa.packetRssi();
}

void LoRaTx::sleep() {
    if (_initialized) {
        LoRa.sleep();
        Serial.println("[LoRa TX] Entering sleep mode");
    }
}

void LoRaTx::wake() {
    if (_initialized) {
        LoRa.idle();
        Serial.println("[LoRa TX] Woke up from sleep");
    }
}

uint32_t LoRaTx::getPacketsSent() {
    return _packetsSent;
}
