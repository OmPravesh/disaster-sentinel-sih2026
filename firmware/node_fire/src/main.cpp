/**
 * Disaster Sentinel — Node 3 (Fire) Main Firmware
 * 
 * ESP32 Node FIR3: Flame IR (KY-026) + Smoke/Gas (MQ-2) + BME280/BMP280.
 * Transmits binary LoRa packets to Jetson Orin Nano gateway over 433 MHz.
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>
#include "config.h"

struct __attribute__((packed)) LoRaPacket {
    uint8_t  header;
    char     node_id[4];      // "FIR3"
    uint8_t  hazard_type;     // 0x02 (FIRE)
    float    l1_raw;          // Flame IR intensity (0.0 - 1.0)
    uint8_t  l1_anomaly;
    float    l2_raw;          // Smoke/Gas concentration (0.0 - 1.0)
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
Adafruit_BMP280 bmp;
bool bme_found = false;
bool is_bmp = false;
bool lora_initialized = false;

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
    bool digitalTriggered = (digitalRead(FLAME_DIGITAL_PIN) == LOW);

    // Inverted KY-026 Flame Sensor:
    // Dark / Clean / No Flame: raw is high (~3800 - 4095)
    // Flame present: raw drops towards 0 (~200 - 1500)
    float intensity = 0.0f;
    if (raw < 3700) {
        intensity = (3700.0f - (float)raw) / 3200.0f;
    }

    // Cross-validate digital pin: only allow DO to bump intensity if raw analog shows some IR drop (< 3700)
    if (digitalTriggered && raw < 3700 && intensity < 0.5f) {
        intensity = 0.5f;
    }

    if (intensity < 0.0f) intensity = 0.0f;
    if (intensity > 1.0f) intensity = 1.0f;
    return intensity;
}

float read_gas_sensor() {
    int raw = analogRead(GAS_ANALOG_PIN);
    bool digitalTriggered = (digitalRead(GAS_DIGITAL_PIN) == LOW);

    // MQ-2 Gas / Smoke Sensor:
    // Clean air: raw is low (~200 - 700)
    // Smoke / Combustible Gas: raw jumps towards 3000+
    float intensity = 0.0f;
    if (raw > 500) {
        intensity = ((float)raw - 500.0f) / 3000.0f;
    }
    if (digitalTriggered && intensity < 0.4f) {
        intensity = 0.4f; // Digital DO comparator confirms gas threshold
    }
    if (intensity < 0.0f) intensity = 0.0f;
    if (intensity > 1.0f) intensity = 1.0f;
    return intensity;
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
    delay(100);
    Serial.println("\n═══════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 3: FIRE (FIR3)");
    Serial.println("═══════════════════════════════════════════════");

    // Configure ADC & Digital pins
    analogSetAttenuation(ADC_11db);
    pinMode(FLAME_ANALOG_PIN, INPUT);
    pinMode(FLAME_DIGITAL_PIN, INPUT_PULLUP);
    pinMode(GAS_ANALOG_PIN, INPUT);
    pinMode(GAS_DIGITAL_PIN, INPUT_PULLUP);

    // --- I2C Environmental Sensor (BME280 / BMP280) ---
    Wire.begin(BME_SDA, BME_SCL, 100000);
    Wire.setTimeOut(30);

    uint8_t addrs[2] = {0x76, 0x77};
    for (uint8_t a : addrs) {
        if (bme.begin(a, &Wire)) {
            bme.setSampling(
                Adafruit_BME280::MODE_NORMAL,
                Adafruit_BME280::SAMPLING_X2,
                Adafruit_BME280::SAMPLING_X16,
                Adafruit_BME280::SAMPLING_X1,
                Adafruit_BME280::FILTER_X16,
                Adafruit_BME280::STANDBY_MS_500
            );
            bme_found = true;
            is_bmp = false;
            Serial.printf("✅ BME280 detected and configured on 0x%02X!\n", a);
            break;
        }
    }
    if (!bme_found) {
        for (uint8_t a : addrs) {
            if (bmp.begin(a)) {
                bmp.setSampling(
                    Adafruit_BMP280::MODE_NORMAL,
                    Adafruit_BMP280::SAMPLING_X2,
                    Adafruit_BMP280::SAMPLING_X16,
                    Adafruit_BMP280::FILTER_X16,
                    Adafruit_BMP280::STANDBY_MS_500
                );
                bme_found = true;
                is_bmp = true;
                Serial.printf("✅ BMP280 detected and configured on 0x%02X!\n", a);
                break;
            }
        }
    }
    if (!bme_found) {
        Serial.println("⚠️ BME280/BMP280 not responding on 0x76 or 0x77 (Layer 3 nominal).");
    }

    // --- LoRa SX1278 SPI Initialization ---
    pinMode(LORA_RST, OUTPUT);
    digitalWrite(LORA_RST, LOW);
    delay(10);
    digitalWrite(LORA_RST, HIGH);
    delay(15);

    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
    LoRa.setSPI(SPI);
    LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);

    // Direct SPI diagnostic probe
    pinMode(LORA_CS, OUTPUT);
    digitalWrite(LORA_CS, LOW);
    SPI.transfer(0x42 & 0x7F);
    uint8_t probeVersion = SPI.transfer(0x00);
    digitalWrite(LORA_CS, HIGH);

    Serial.printf("  [SPI Probe] SX1278 Chip ID: 0x%02X (Expected 0x12)\n", probeVersion);
    if (probeVersion == 0x12) {
        Serial.println("  ==> SPI hardware communication verified OK!");
    } else if (probeVersion == 0x00) {
        Serial.println("  ==> Cause: LoRa has NO 3.3V POWER, or MISO/MOSI wire is loose!");
    } else {
        Serial.println("  ==> Cause: NSS (D5) or SCK (D18) wire is loose!");
    }

    if (LoRa.begin(LORA_FREQUENCY)) {
        lora_initialized = true;
        LoRa.setTxPower(LORA_TX_POWER);
        LoRa.setSpreadingFactor(LORA_SPREADING_FACTOR);
        LoRa.setSignalBandwidth(LORA_BANDWIDTH);
        LoRa.setCodingRate4(5);
        LoRa.setSyncWord(0xF3);
        LoRa.enableCrc();
        Serial.println("✅ LoRa SX1278 initialized successfully (433 MHz, SF7, CR 4/5)!");
    } else {
        Serial.println("❌ LoRa initialization failed! Check wiring.");
    }

    Serial.println("✅ Node FIR3 initialization complete.\n");
}

void loop() {
    float flame = read_flame_sensor();
    float gas   = read_gas_sensor();
    float temp  = 26.5f;
    float press = 990.0f;

    if (bme_found) {
        float rawTemp  = is_bmp ? bmp.readTemperature() : bme.readTemperature();
        float rawPress = (is_bmp ? bmp.readPressure() : bme.readPressure()) / 100.0f;

        // Sanity filter on I2C readings
        if (!isnan(rawTemp) && rawTemp >= -20.0f && rawTemp <= 85.0f) {
            temp = rawTemp;
        }
        if (!isnan(rawPress) && rawPress >= 800.0f && rawPress <= 1100.0f) {
            press = rawPress;
        }
    }

    // Anomaly normalization
    float l1_anomaly_f = min(1.0f, max(0.0f, flame));
    float l2_anomaly_f = min(1.0f, max(0.0f, gas));
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
    if (packet.battery_pct == 0) packet.battery_pct = 96; // USB power fallback
    packet.sequence_num = ++g_sequence_num;
    packet.end_marker = 0x0D;

    size_t payload_len = sizeof(LoRaPacket) - 3;
    packet.crc16 = calculate_crc16((const uint8_t*)&packet, payload_len);

    if (lora_initialized) {
        LoRa.beginPacket();
        LoRa.write((const uint8_t*)&packet, sizeof(packet));
        LoRa.endPacket(true); // Non-blocking TX

        Serial.printf("📡 FIR3 Sent: Flame=%.2f, Gas=%.2f, Temp=%.1f°C | Combined=%.2f | Seq=%d\n",
                      flame, gas, temp, combined_f, packet.sequence_num);
    } else {
        Serial.printf("⚠️ FIR3 Telemetry (LoRa offline): Flame=%.2f, Gas=%.2f, Temp=%.1f°C | Combined=%.2f | Seq=%d\n",
                      flame, gas, temp, combined_f, packet.sequence_num);
    }

    int rawFlame = analogRead(FLAME_ANALOG_PIN);
    int rawGas   = analogRead(GAS_ANALOG_PIN);
    int flameDO  = digitalRead(FLAME_DIGITAL_PIN);
    int gasDO    = digitalRead(GAS_DIGITAL_PIN);

    // Diagnostics print for hardware verification
    Serial.printf("  [DIAG] RawFlame(GPIO%d)=%d [DO(GPIO%d)=%d] | RawGas(GPIO%d)=%d [DO(GPIO%d)=%d] | Temp=%.1fC Press=%.1fhPa\n",
                  FLAME_ANALOG_PIN, rawFlame, FLAME_DIGITAL_PIN, flameDO,
                  GAS_ANALOG_PIN, rawGas, GAS_DIGITAL_PIN, gasDO,
                  temp, press);

    // JSON formatted line for external serial bridge & analytics
    Serial.printf("{\"node\":\"FIR3\",\"flame\":%.2f,\"gas\":%.2f,\"temp\":%.1f,\"anomaly\":%.2f,\"batt\":%d,\"seq\":%d}\n",
                  flame, gas, temp, combined_f, packet.battery_pct, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
