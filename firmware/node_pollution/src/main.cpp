/**
 * Disaster Sentinel — Node 4 (Pollution) Main Firmware
 * 
 * ESP32 node operating in 2-Layer Mode (MQ-135 + PM2.5).
 * Transmits binary LoRa packets to Jetson Orin Nano gateway.
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include "config.h"

// Binary packet structure (matches packet_format.h & python decoder)
struct __attribute__((packed)) LoRaPacket {
    uint8_t  header;          // 0xAA (normal) or 0xFF (priority)
    char     node_id[4];      // "POL4"
    uint8_t  hazard_type;     // 0x04 (POLLUTION)
    float    l1_raw;          // MQ-135 AQI value
    uint8_t  l1_anomaly;      // Anomaly score (0-100%)
    float    l2_raw;          // PM2.5 concentration (ug/m3)
    uint8_t  l2_anomaly;      // Anomaly score (0-100%)
    float    l3_raw;          // 0.0 (Unused for 2-layer mode)
    uint8_t  l3_anomaly;      // 0 (Unused for 2-layer mode)
    uint8_t  combined_score;  // 0.55*L1 + 0.45*L2 (0-100%)
    uint8_t  rate_flag;       // 0=stable, 1=rising, 2=falling, 3=rapid
    uint8_t  battery_pct;     // Battery percentage
    uint16_t sequence_num;    // Packet sequence counter
    uint16_t crc16;           // CRC16-CCITT checksum
    uint8_t  end_marker;      // 0x0D
};

static uint16_t g_sequence_num = 0;

uint16_t calculate_crc16(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int b = 0; b < 8; b++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

float read_mq135_aqi() {
    int raw = analogRead(MQ135_ANALOG_PIN);
    float voltage = (raw / 4095.0f) * 3.3f;
    float aqi = (voltage / 3.3f) * 500.0f; // Scaled 0-500 AQI
    return aqi;
}

float read_pm25_dust() {
    digitalWrite(PM25_LED_PIN, LOW); // Turn on IR LED
    delayMicroseconds(280);
    int raw = analogRead(PM25_ANALOG_PIN);
    delayMicroseconds(40);
    digitalWrite(PM25_LED_PIN, HIGH); // Turn off IR LED

    float voltage = (raw / 4095.0f) * 3.3f;
    float dust_density = (voltage - 0.9f) * 0.2f * 1000.0f; // ug/m3
    return max(0.0f, dust_density);
}

uint8_t compute_battery_pct() {
    int raw = analogRead(BATTERY_ADC_PIN);
    float mv = (raw / 4095.0f) * 3300.0f * 2.0f; // 1/2 voltage divider
    if (mv >= BATTERY_FULL_MV) return 100;
    if (mv <= BATTERY_EMPTY_MV) return 0;
    return (uint8_t)(((mv - BATTERY_EMPTY_MV) / (BATTERY_FULL_MV - BATTERY_EMPTY_MV)) * 100.0f);
}

void setup() {
    Serial.begin(115200);
    pinMode(MQ135_ANALOG_PIN, INPUT);
    pinMode(PM25_ANALOG_PIN, INPUT);
    pinMode(PM25_LED_PIN, OUTPUT);
    digitalWrite(PM25_LED_PIN, HIGH);

    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
    LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);

    if (!LoRa.begin(LORA_FREQUENCY)) {
        Serial.println("❌ LoRa initialization failed!");
        while (1) { delay(1000); }
    }

    LoRa.setTxPower(LORA_TX_POWER);
    LoRa.setSpreadingFactor(LORA_SPREADING_FACTOR);
    LoRa.setSignalBandwidth(LORA_BANDWIDTH);

    Serial.println("✅ Node POL4 (Pollution - 2-Layer Mode) initialized.");
}

void loop() {
    float aqi = read_mq135_aqi();
    float pm25 = read_pm25_dust();

    // 2-Layer anomaly scoring
    float l1_anomaly_f = min(1.0f, max(0.0f, (aqi - 50.0f) / 250.0f));
    float l2_anomaly_f = min(1.0f, max(0.0f, (pm25 - 25.0f) / 150.0f));
    float combined_f = POL_LAYER1_WEIGHT * l1_anomaly_f + POL_LAYER2_WEIGHT * l2_anomaly_f;

    bool is_priority = combined_f >= PRIORITY_THRESHOLD;

    LoRaPacket packet;
    memset(&packet, 0, sizeof(packet));
    packet.header = is_priority ? PACKET_HEADER_PRIORITY : PACKET_HEADER_NORMAL;
    memcpy(packet.node_id, NODE_ID, 4);
    packet.hazard_type = NODE_TYPE;

    packet.l1_raw = aqi;
    packet.l1_anomaly = (uint8_t)(l1_anomaly_f * 100.0f);

    packet.l2_raw = pm25;
    packet.l2_anomaly = (uint8_t)(l2_anomaly_f * 100.0f);

    packet.l3_raw = 0.0f;     // Unused in 2-layer mode
    packet.l3_anomaly = 0;    // Unused in 2-layer mode

    packet.combined_score = (uint8_t)(combined_f * 100.0f);
    packet.rate_flag = (combined_f > 0.6f) ? 3 : 0;
    packet.battery_pct = compute_battery_pct();
    packet.sequence_num = ++g_sequence_num;
    packet.end_marker = 0x0D;

    // Calculate CRC over payload
    size_t payload_len = sizeof(LoRaPacket) - 3; // Excluding crc16 and end_marker
    packet.crc16 = calculate_crc16((const uint8_t*)&packet, payload_len);

    // Send via LoRa
    LoRa.beginPacket();
    LoRa.write((const uint8_t*)&packet, sizeof(packet));
    LoRa.endPacket();

    Serial.printf("📡 POL4 Sent: AQI=%.1f (L1=%.2f), PM2.5=%.1f (L2=%.2f) | Combined=%.2f | Seq=%d\n",
                  aqi, l1_anomaly_f, pm25, l2_anomaly_f, combined_f, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
