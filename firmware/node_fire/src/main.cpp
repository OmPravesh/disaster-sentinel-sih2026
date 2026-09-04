/**
 * Disaster Sentinel — Node 3 (Fire) Main Firmware
 * 
 * ESP32 Node FIR3: Flame IR + Smoke/Gas + BME280.
 * Transmits binary LoRa packets to Jetson Orin Nano gateway.
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include "config.h"

struct __attribute__((packed)) LoRaPacket {
    uint8_t  header;
    char     node_id[4];      // "FIR3"
    uint8_t  hazard_type;     // 0x02 (FIRE)
    float    l1_raw;          // Flame IR intensity
    uint8_t  l1_anomaly;
    float    l2_raw;          // Smoke/Gas concentration
    uint8_t  l2_anomaly;
    float    l3_raw;          // Temperature (°C)
    uint8_t  l3_anomaly;
    uint8_t  combined_score;
    uint8_t  rate_flag;
    uint8_t  battery_pct;
    uint16_t sequence_num;
    uint16_t crc16;
    uint8_t  end_marker;
};

static uint16_t g_sequence_num = 0;
Adafruit_BME280 bme;
bool bme_found = false;

uint16_t calculate_crc16(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int b = 0; b < 8; b++) {
            if (crc & 0x8000) crc = (crc << 1) ^ 0x1021;
            else crc <<= 1;
        }
    }
    return crc;
}

float read_flame_sensor() {
    int raw = analogRead(FLAME_ANALOG_PIN);
    return (4095.0f - raw) / 4095.0f; // Scaled 0.0 (no flame) to 1.0 (strong flame)
}

float read_gas_sensor() {
    int raw = analogRead(GAS_ANALOG_PIN);
    return raw / 4095.0f;
}

uint8_t compute_battery_pct() {
    int raw = analogRead(BATTERY_ADC_PIN);
    float mv = (raw / 4095.0f) * 3300.0f * 2.0f;
    if (mv >= BATTERY_FULL_MV) return 100;
    if (mv <= BATTERY_EMPTY_MV) return 0;
    return (uint8_t)(((mv - BATTERY_EMPTY_MV) / (BATTERY_FULL_MV - BATTERY_EMPTY_MV)) * 100.0f);
}

void setup() {
    Serial.begin(115200);
    pinMode(FLAME_ANALOG_PIN, INPUT);
    pinMode(GAS_ANALOG_PIN, INPUT);

    Wire.begin(BME_SDA, BME_SCL);
    if (bme.begin(BME_ADDR, &Wire)) {
        bme_found = true;
    }

    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
    LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);

    if (!LoRa.begin(LORA_FREQUENCY)) {
        Serial.println("❌ LoRa initialization failed!");
        while (1) { delay(1000); }
    }

    LoRa.setTxPower(LORA_TX_POWER);
    LoRa.setSpreadingFactor(LORA_SPREADING_FACTOR);
    LoRa.setSignalBandwidth(LORA_BANDWIDTH);

    Serial.println("✅ Node FIR3 (Fire - 3-Layer Mode) initialized.");
}

void loop() {
    float flame = read_flame_sensor();
    float gas = read_gas_sensor();
    float temp = bme_found ? bme.readTemperature() : 28.0f;

    float l1_anomaly_f = min(1.0f, max(0.0f, flame));
    float l2_anomaly_f = min(1.0f, max(0.0f, (gas - 0.1f) / 0.8f));
    float l3_anomaly_f = min(1.0f, max(0.0f, (temp - 30.0f) / 40.0f));

    float combined_f = FIRE_LAYER1_WEIGHT * l1_anomaly_f + FIRE_LAYER2_WEIGHT * l2_anomaly_f + FIRE_LAYER3_WEIGHT * l3_anomaly_f;
    bool is_priority = combined_f >= PRIORITY_THRESHOLD;

    LoRaPacket packet;
    memset(&packet, 0, sizeof(packet));
    packet.header = is_priority ? PACKET_HEADER_PRIORITY : PACKET_HEADER_NORMAL;
    memcpy(packet.node_id, NODE_ID, 4);
    packet.hazard_type = NODE_TYPE;

    packet.l1_raw = flame;
    packet.l1_anomaly = (uint8_t)(l1_anomaly_f * 100.0f);
    packet.l2_raw = gas;
    packet.l2_anomaly = (uint8_t)(l2_anomaly_f * 100.0f);
    packet.l3_raw = temp;
    packet.l3_anomaly = (uint8_t)(l3_anomaly_f * 100.0f);

    packet.combined_score = (uint8_t)(combined_f * 100.0f);
    packet.rate_flag = (combined_f > 0.6f) ? 3 : 0;
    packet.battery_pct = compute_battery_pct();
    packet.sequence_num = ++g_sequence_num;
    packet.end_marker = 0x0D;

    size_t payload_len = sizeof(LoRaPacket) - 3;
    packet.crc16 = calculate_crc16((const uint8_t*)&packet, payload_len);

    LoRa.beginPacket();
    LoRa.write((const uint8_t*)&packet, sizeof(packet));
    LoRa.endPacket();

    Serial.printf("📡 FIR3 Sent: Flame=%.2f, Gas=%.2f, Temp=%.1f°C | Combined=%.2f | Seq=%d\n",
                  flame, gas, temp, combined_f, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
