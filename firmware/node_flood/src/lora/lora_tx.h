/**
 * Disaster Sentinel — LoRa Transmitter Driver
 * 
 * Handles SX1278 LoRa module initialization, packet transmission,
 * and adaptive transmission interval based on anomaly state.
 */

#ifndef LORA_TX_H
#define LORA_TX_H

#include <Arduino.h>
#include <LoRa.h>
#include "packet_format.h"

class LoRaTx {
public:
    /**
     * Initialize LoRa SX1278 module.
     * @return true if initialization successful
     */
    bool begin(int csPin, int rstPin, int dio0Pin,
               long frequency, int txPower, int sf, long bandwidth);

    /**
     * Send a SentinelPacket over LoRa.
     * @param pkt  The packet to send
     * @return true if transmission successful
     */
    bool sendPacket(const SentinelPacket& pkt);

    /**
     * Send raw bytes over LoRa (for debugging).
     */
    bool sendRaw(const uint8_t* data, size_t len);

    /**
     * Get RSSI of last transmission confirmation (if available).
     */
    int getLastRSSI();

    /**
     * Put LoRa module into sleep mode (power saving).
     */
    void sleep();

    /**
     * Wake LoRa module from sleep.
     */
    void wake();

    /**
     * Get total packets sent counter.
     */
    uint32_t getPacketsSent();

private:
    uint32_t _packetsSent;
    bool _initialized;
};

#endif // LORA_TX_H
