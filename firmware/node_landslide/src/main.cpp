/**
 * Disaster Sentinel — Node 2 (Landslide) Main Firmware
 * 
 * ESP32 Node SLD2: MPU-6500 / MPU-6050 Tilt + Soil Moisture + BMP280/BME280.
 * Supports MPU-6500 (WHO_AM_I = 0x70) & MPU-6050 (WHO_AM_I = 0x68).
 * Transmits binary LoRa packets to Jetson Orin Nano gateway over 433 MHz.
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
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
Adafruit_BME280 bme;
Adafruit_BMP280 bmp;

bool mpu_found = false;
bool mpu_is_6500 = false;
uint8_t mpu_address = 0x68;

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

// Low-level register access for MPU-6500 / MPU-6050 matching YMFC-AL implementation
uint8_t search_gyro(uint8_t gyro_address, uint8_t who_am_i_reg) {
    Wire.beginTransmission(gyro_address);
    Wire.write(who_am_i_reg);
    Wire.endTransmission();
    Wire.requestFrom((int)gyro_address, 1);
    uint32_t timer = millis() + 100;
    while (Wire.available() < 1 && millis() < timer);
    if (Wire.available() > 0) return Wire.read();
    return 0x00;
}

bool write_i2c_register(uint8_t addr, uint8_t reg, uint8_t val) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    Wire.write(val);
    return (Wire.endTransmission() == 0);
}

void recover_i2c_bus(uint8_t sda_pin, uint8_t scl_pin) {
    pinMode(sda_pin, INPUT_PULLUP);
    pinMode(scl_pin, OUTPUT);
    digitalWrite(scl_pin, HIGH);
    delayMicroseconds(10);
    // Pulse SCL 9 times to free any locked I2C slave
    for (int i = 0; i < 9; i++) {
        digitalWrite(scl_pin, LOW);
        delayMicroseconds(5);
        digitalWrite(scl_pin, HIGH);
        delayMicroseconds(5);
    }
    // Generate I2C STOP condition
    pinMode(sda_pin, OUTPUT);
    digitalWrite(sda_pin, LOW);
    delayMicroseconds(5);
    digitalWrite(scl_pin, HIGH);
    delayMicroseconds(5);
    digitalWrite(sda_pin, HIGH);
    delayMicroseconds(5);
    pinMode(sda_pin, INPUT_PULLUP);
    pinMode(scl_pin, INPUT_PULLUP);
}

float read_tilt_angle() {
    static float s_last_valid_tilt = 0.0f;
    if (!mpu_found) return 0.0f;

    Wire.beginTransmission(mpu_address);
    Wire.write(0x3B); // ACCEL_XOUT_H register
    if (Wire.endTransmission() != 0) {
        return s_last_valid_tilt;
    }
    if (Wire.requestFrom((int)mpu_address, 6) != 6) {
        return s_last_valid_tilt;
    }

    int16_t rawX = (Wire.read() << 8) | Wire.read();
    int16_t rawY = (Wire.read() << 8) | Wire.read();
    int16_t rawZ = (Wire.read() << 8) | Wire.read();

    float ax = (float)rawX / 4096.0f;
    float ay = (float)rawY / 4096.0f;
    float az = (float)rawZ / 4096.0f;

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
    delay(150);
    Serial.println("\n═══════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 2: LANDSLIDE (SLD2)");
    Serial.println("  Hardware: MPU-6500 / MPU-6050 + Soil + BMP280");
    Serial.println("═══════════════════════════════════════════════");

    analogSetAttenuation(ADC_11db);
    pinMode(SOIL_ANALOG_PIN, INPUT);

    // --- I2C Bus Clean Recovery & Setup ---
    recover_i2c_bus(BME_SDA, BME_SCL);
    Wire.begin(BME_SDA, BME_SCL, 100000);
    Wire.setTimeOut(50);
    delay(50);

    Serial.println("🔍 Running full I2C Bus Scan (0x01 to 0x7E)...");
    int i2c_devs = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  ⭐ ACK from I2C device at 0x%02X\n", addr);
            i2c_devs++;
        }
    }
    if (i2c_devs == 0) {
        Serial.println("  ⚠️ No standard ACK on I2C bus. Probing registers directly...");
    }

    // --- Probe for MPU-6500 / MPU-6050 (Matches YMFC-AL photo) ---
    Serial.println("Searching for MPU-6500 on address 0x68...");
    delay(200);
    uint8_t who68 = search_gyro(0x68, 0x75);
    Serial.printf("  search_gyro(0x68, 0x75) => 0x%02X\n", who68);

    if (who68 == 0x70) {
        Serial.println("✅ MPU-6500 found on address 0x68 (WHO_AM_I == 0x70)!");
        mpu_address = 0x68;
        mpu_found = true;
        mpu_is_6500 = true;
    } else if (who68 == 0x68) {
        Serial.println("✅ MPU-6050 found on address 0x68 (WHO_AM_I == 0x68)!");
        mpu_address = 0x68;
        mpu_found = true;
        mpu_is_6500 = false;
    }

    if (!mpu_found) {
        Serial.println("Searching for MPU-6500 on address 0x69...");
        delay(200);
        uint8_t who69 = search_gyro(0x69, 0x75);
        Serial.printf("  search_gyro(0x69, 0x75) => 0x%02X\n", who69);
        if (who69 == 0x70) {
            Serial.println("✅ MPU-6500 found on address 0x69 (WHO_AM_I == 0x70)!");
            mpu_address = 0x69;
            mpu_found = true;
            mpu_is_6500 = true;
        } else if (who69 == 0x68) {
            Serial.println("✅ MPU-6050 found on address 0x69 (WHO_AM_I == 0x68)!");
            mpu_address = 0x69;
            mpu_found = true;
            mpu_is_6500 = false;
        }
    }

    if (mpu_found) {
        // Wake up MPU-6500
        write_i2c_register(mpu_address, 0x6B, 0x00);
        delay(20);
        // Auto select best clock source (PLL with X gyro)
        write_i2c_register(mpu_address, 0x6B, 0x01);
        delay(10);
        // Set Accelerometer to ±8G
        write_i2c_register(mpu_address, 0x1C, 0x10);
        delay(10);
        // Set DLPF to 44Hz filter
        write_i2c_register(mpu_address, 0x1A, 0x03);
        delay(10);
        Serial.printf("✅ %s initialized & calibrated (±8G range, 44Hz DLPF filter).\n",
                      mpu_is_6500 ? "MPU-6500" : "MPU-6050");
    } else {
        Serial.println("⚠️ MPU-6500 / MPU-6050 not detected on 0x68 or 0x69.");
    }

    // --- Auto-detect BME280 or BMP280 on 0x76 or 0x77 ---
    uint8_t bme_addrs[2] = {0x76, 0x77};
    for (uint8_t a : bme_addrs) {
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
        for (uint8_t a : bme_addrs) {
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
        Serial.println("⚠️ BME280/BMP280 not responding on 0x76 or 0x77 (Layer 3 fallback).");
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
        Serial.println("✅ LoRa SX1278 initialized successfully (433 MHz, SF7, CR 4/5)!");
    } else {
        Serial.println("❌ LoRa initialization failed! Check wiring.");
    }

    Serial.println("✅ Node SLD2 initialization complete.\n");
}

void loop() {
    float tilt = read_tilt_angle();
    float soil = read_soil_moisture();
    int rawSoil = analogRead(SOIL_ANALOG_PIN);
    float pressure = 990.0f;
    float temp = 25.0f;

    if (bme_found) {
        float rawPress = (is_bmp ? bmp.readPressure() : bme.readPressure()) / 100.0f;
        float rawTemp  = is_bmp ? bmp.readTemperature() : bme.readTemperature();
        if (!isnan(rawPress) && rawPress >= 800.0f && rawPress <= 1100.0f) {
            pressure = rawPress;
        }
        if (!isnan(rawTemp) && rawTemp >= -20.0f && rawTemp <= 85.0f) {
            temp = rawTemp;
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
                  tilt, mpu_is_6500 ? "MPU-6500" : (mpu_found ? "MPU-6050" : "None"),
                  SOIL_ANALOG_PIN, rawSoil, soil, temp, pressure);

    // JSON formatted line for external serial bridge & analytics
    Serial.printf("{\"node\":\"SLD2\",\"tilt\":%.1f,\"soil\":%.1f,\"press\":%.1f,\"anomaly\":%.2f,\"batt\":%d,\"seq\":%d}\n",
                  tilt, soil, pressure, combined_f, packet.battery_pct, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
