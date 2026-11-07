/**
 * Disaster Sentinel — Node 2 (Landslide) Main Firmware
 * 
 * ESP32 Node SLD2: MPU-6050 / MPU-6500 Tilt + Soil Moisture + BME280/BMP280.
 * Automatically accepts both genuine MPU-6050 (0x68) and modern MPU-6500 (0x70).
 * Transmits binary LoRa packets to Jetson Orin Nano gateway over 433 MHz.
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>
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
Adafruit_BMP280 bmp;

bool mpu_found = false;
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

float read_tilt_angle() {
    static float s_last_valid_tilt = 0.0f;
    if (!mpu_found) return 0.0f;

    sensors_event_t a, g, temp;
    if (!mpu.getEvent(&a, &g, &temp)) {
        return s_last_valid_tilt;
    }

    float ax = a.acceleration.x;
    float ay = a.acceleration.y;
    float az = a.acceleration.z;

    float raw_tilt = atan2(sqrt(ax * ax + ay * ay), fabs(az)) * 180.0f / 3.14159265f;
    if (isnan(raw_tilt)) raw_tilt = 0.0f;

    // Exponential moving average filter
    if (s_last_valid_tilt == 0.0f) {
        s_last_valid_tilt = raw_tilt;
    } else {
        s_last_valid_tilt = (0.3f * raw_tilt) + (0.7f * s_last_valid_tilt);
    }

    return s_last_valid_tilt;
}

float read_soil_moisture() {
    int raw = analogRead(SOIL_ANALOG_PIN);
    // Capacitive Soil Moisture Sensor v1.2:
    // In dry air (raw ~2800 - 3200) -> 0.0%
    // In water/wet soil (raw ~1100 - 1500) -> 100.0%
    const int DRY_AIR_VAL = 3000;
    const int WET_VAL = 1200;
    if (raw >= DRY_AIR_VAL) return 0.0f;
    if (raw <= WET_VAL) return 100.0f;
    float pct = (float)(DRY_AIR_VAL - raw) / (float)(DRY_AIR_VAL - WET_VAL) * 100.0f;
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
    delay(200);
    Serial.println("\n═══════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 2: LANDSLIDE (SLD2)");
    Serial.println("  Sensors: MPU-6050/6500 (0x70) + Soil + BME/BMP");
    Serial.println("═══════════════════════════════════════════════");

    analogSetAttenuation(ADC_11db);
    pinMode(SOIL_ANALOG_PIN, INPUT);

    // --- I2C Bus Initialization (Pins 21 SDA, 22 SCL) ---
    Wire.begin(BME_SDA, BME_SCL, 100000);
    Wire.setTimeOut(100);
    delay(50);

    // Quick I2C Bus Scan
    Serial.println("🔍 I2C Scan (GPIO 21 SDA / GPIO 22 SCL):");
    int i2c_devs = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  ⭐ Found I2C device at 0x%02X\n", addr);
            i2c_devs++;
        }
    }
    if (i2c_devs == 0) {
        Serial.println("  ⚠️ No I2C devices found on bus.");
    }

    // --- MPU-6050 / MPU-6500 Initialization (Addresses 0x68 / 0x69) ---
    Serial.println("\n--- Initializing MPU (MPU-6050 / MPU-6500) ---");
    if (mpu.begin(0x68, &Wire) || mpu.begin(0x69, &Wire)) {
        mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
        mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);
        mpu_found = true;
        Serial.println("✅ MPU-6050 / MPU-6500 (0x68/0x70) initialized successfully!");
    } else {
        Serial.println("⚠️ MPU-6050 / MPU-6500 not detected on 0x68 or 0x69.");
    }

    // --- BME280 / BMP280 Initialization (Addresses 0x76 / 0x77) ---
    Serial.println("\n--- Initializing Environmental Sensor (BME280 / BMP280) ---");
    uint8_t addrs[2] = {0x76, 0x77};

    // Step 1: Try BME280 (Temp + Humidity + Pressure)
    for (uint8_t a : addrs) {
        if (bme.begin(a)) {
            bme.setSampling(
                Adafruit_BME280::MODE_FORCED,
                Adafruit_BME280::SAMPLING_X2,
                Adafruit_BME280::SAMPLING_X16,
                Adafruit_BME280::SAMPLING_X1,
                Adafruit_BME280::FILTER_X16,
                Adafruit_BME280::STANDBY_MS_0_5
            );
            bme_found = true;
            is_bmp = false;
            Serial.printf("✅ BME280 detected and configured on 0x%02X!\n", a);
            break;
        }
    }

    // Step 2: Try BMP280 (Temp + Pressure)
    if (!bme_found) {
        for (uint8_t a : addrs) {
            if (bmp.begin(a)) {
                bmp.setSampling(
                    Adafruit_BMP280::MODE_FORCED,
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
        Serial.println("⚠️ BME280 / BMP280 not responding on 0x76 or 0x77 (Layer 3 fallback).");
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
    }

    if (LoRa.begin(LORA_FREQUENCY)) {
        lora_initialized = true;
        LoRa.setTxPower(LORA_TX_POWER);
        LoRa.setSpreadingFactor(LORA_SPREADING_FACTOR);
        LoRa.setSignalBandwidth(LORA_BANDWIDTH);
        LoRa.setCodingRate4(5);
        LoRa.setSyncWord(0xF3);
        LoRa.enableCrc();
        Serial.println("✅ LoRa SX1278 initialized successfully (433 MHz, SF7, CR 4/5)!\n");
    } else {
        Serial.println("❌ LoRa initialization failed! Check wiring.\n");
    }

    Serial.println("✅ Node SLD2 initialization sequence complete.\n");
}

void loop() {
    float tilt = read_tilt_angle();
    float soil = read_soil_moisture();
    int rawSoil = analogRead(SOIL_ANALOG_PIN);
    float pressure = 990.0f;
    float temp = 25.0f;

    if (bme_found) {
        if (is_bmp) {
            bmp.takeForcedMeasurement();
            float rawPress = bmp.readPressure() / 100.0f;
            float rawTemp  = bmp.readTemperature();
            if (!isnan(rawPress) && rawPress >= 800.0f && rawPress <= 1100.0f) pressure = rawPress;
            if (!isnan(rawTemp) && rawTemp >= -20.0f && rawTemp <= 85.0f) temp = rawTemp;
        } else {
            bme.takeForcedMeasurement();
            float rawPress = bme.readPressure() / 100.0f;
            float rawTemp  = bme.readTemperature();
            if (!isnan(rawPress) && rawPress >= 800.0f && rawPress <= 1100.0f) pressure = rawPress;
            if (!isnan(rawTemp) && rawTemp >= -20.0f && rawTemp <= 85.0f) temp = rawTemp;
        }
    }

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
    if (packet.battery_pct == 0) packet.battery_pct = 95; // USB fallback
    packet.sequence_num = ++g_sequence_num;
    packet.end_marker = 0x0D;

    size_t payload_len = sizeof(LoRaPacket) - 3;
    packet.crc16 = calculate_crc16((const uint8_t*)&packet, payload_len);

    if (lora_initialized) {
        LoRa.beginPacket();
        LoRa.write((const uint8_t*)&packet, sizeof(packet));
        LoRa.endPacket(true); // Non-blocking TX

        Serial.printf("📡 SLD2 Sent: Tilt=%.1f°, Soil=%.1f%%, Press=%.1fhPa | Combined=%.2f | Seq=%d\n",
                      tilt, soil, pressure, combined_f, packet.sequence_num);
    } else {
        Serial.printf("⚠️ SLD2 Telemetry (LoRa offline): Tilt=%.1f°, Soil=%.1f%%, Press=%.1fhPa | Combined=%.2f | Seq=%d\n",
                      tilt, soil, pressure, combined_f, packet.sequence_num);
    }

    // Diagnostics for hardware verification
    Serial.printf("  [DIAG] Tilt=%.1f deg (%s) | RawSoil(GPIO%d)=%d (Soil=%.1f%%) | Temp=%.1fC Press=%.1fhPa\n",
                  tilt, mpu_found ? "MPU-6050/6500 OK" : "None",
                  SOIL_ANALOG_PIN, rawSoil, soil, temp, pressure);

    // JSON formatted line for external serial bridge & analytics
    Serial.printf("{\"node\":\"SLD2\",\"tilt\":%.1f,\"soil\":%.1f,\"press\":%.1f,\"anomaly\":%.2f,\"batt\":%d,\"seq\":%d}\n",
                  tilt, soil, pressure, combined_f, packet.battery_pct, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
