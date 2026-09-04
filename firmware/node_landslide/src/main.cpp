/**
 * Disaster Sentinel — Node 2 (Landslide) Main Firmware
 * 
 * ESP32 Node SLD2: MPU6050 Tilt + Soil Moisture + BME280.
 * Transmits binary LoRa packets to Jetson Orin Nano gateway.
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "config.h"

struct __attribute__((packed)) LoRaPacket {
    uint8_t  header;
    char     node_id[4];      // "SLD2"
    uint8_t  hazard_type;     // 0x03 (LANDSLIDE)
    float    l1_raw;          // Tilt angle (degrees)
    uint8_t  l1_anomaly;
    float    l2_raw;          // Soil moisture (%)
    uint8_t  l2_anomaly;
    float    l3_raw;          // Pressure (hPa)
    uint8_t  l3_anomaly;
    uint8_t  combined_score;
    uint8_t  rate_flag;
    uint8_t  battery_pct;
    uint16_t sequence_num;
    uint16_t crc16;
    uint8_t  end_marker;
};

static uint16_t g_sequence_num = 0;
Adafruit_MPU6050 mpu;
Adafruit_BME280 bme;
bool mpu_found = false;
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

float read_tilt_angle() {
    if (!mpu_found) return 1.5f;
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    float tilt = atan2(sqrt(a.acceleration.x * a.acceleration.x + a.acceleration.y * a.acceleration.y), a.acceleration.z) * 180.0 / 3.14159265;
    return abs(tilt);
}

float read_soil_moisture() {
    int raw = analogRead(SOIL_ANALOG_PIN);
    float pct = (4095.0f - raw) / 4095.0f * 100.0f;
    return max(0.0f, min(100.0f, pct));
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
    pinMode(SOIL_ANALOG_PIN, INPUT);

    Wire.begin(BME_SDA, BME_SCL);
    if (mpu.begin(MPU_ADDR, &Wire)) {
        mpu_found = true;
        mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    }
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

    Serial.println("✅ Node SLD2 (Landslide - 3-Layer Mode) initialized.");
}

void loop() {
    float tilt = read_tilt_angle();
    float soil = read_soil_moisture();
    float pressure = bme_found ? bme.readPressure() / 100.0F : 1013.25f;

    float l1_anomaly_f = min(1.0f, max(0.0f, (tilt - 2.0f) / 15.0f));
    float l2_anomaly_f = min(1.0f, max(0.0f, (soil - 40.0f) / 50.0f));
    float l3_anomaly_f = min(1.0f, max(0.0f, (1013.0f - pressure) / 20.0f));

    float combined_f = SLIDE_LAYER1_WEIGHT * l1_anomaly_f + SLIDE_LAYER2_WEIGHT * l2_anomaly_f + SLIDE_LAYER3_WEIGHT * l3_anomaly_f;
    bool is_priority = combined_f >= PRIORITY_THRESHOLD;

    LoRaPacket packet;
    memset(&packet, 0, sizeof(packet));
    packet.header = is_priority ? PACKET_HEADER_PRIORITY : PACKET_HEADER_NORMAL;
    memcpy(packet.node_id, NODE_ID, 4);
    packet.hazard_type = NODE_TYPE;

    packet.l1_raw = tilt;
    packet.l1_anomaly = (uint8_t)(l1_anomaly_f * 100.0f);
    packet.l2_raw = soil;
    packet.l2_anomaly = (uint8_t)(l2_anomaly_f * 100.0f);
    packet.l3_raw = pressure;
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

    Serial.printf("📡 SLD2 Sent: Tilt=%.1f°, Soil=%.1f%%, Press=%.1fhPa | Combined=%.2f | Seq=%d\n",
                  tilt, soil, pressure, combined_f, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
