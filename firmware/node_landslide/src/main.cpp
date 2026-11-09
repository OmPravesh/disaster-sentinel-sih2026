/**
 * Disaster Sentinel — Node 2 (Landslide) Dual-Bus Operations Firmware
 * 
 * ESP32 Node SLD2: Dual Independent Hardware I2C Architecture
 *   - Bus 0 (Wire):  MPU-6500 / MPU-6050 on SDA=GPIO21, SCL=GPIO22
 *   - Bus 1 (Wire1): BME280 / BMP280     on SDA=GPIO25, SCL=GPIO26
 *   - Layer 2: Capacitive Soil Moisture v1.2 on GPIO32 ADC
 *   - LoRa SX1278: 433 MHz, SF7, CR 4/5, Sync 0xF3
 * 
 * Complete physical electrical isolation between MPU and BME sensors.
 * Neither sensor can ever interfere with or clamp the other.
 * 
 * Zero Fake Data Policy: Offline sensors report 0.0f
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

// ============================================================
// PACKET STRUCTURE (27 Bytes Packed — Gateway Compatible)
// ============================================================
struct __attribute__((packed)) LoRaPacket {
    uint8_t  header;          // 0xAA (Normal) or 0xFF (Priority Alert)
    char     node_id[4];      // "SLD2"
    uint8_t  hazard_type;     // 0x03 (LANDSLIDE)
    float    l1_raw;          // Tilt angle (degrees)
    uint8_t  l1_anomaly;      // Anomaly score (0-100)
    float    l2_raw;          // Soil moisture (%)
    uint8_t  l2_anomaly;      // Anomaly score (0-100)
    float    l3_raw;          // Atmospheric pressure (hPa)
    uint8_t  l3_anomaly;      // Anomaly score (0-100)
    uint8_t  combined_score;  // Multi-layer risk (0-100)
    uint8_t  rate_flag;       // 0 = Normal, 3 = Rapid Acceleration
    uint8_t  battery_pct;     // Battery % (0-100)
    uint16_t sequence_num;    // Sequential packet counter
    uint16_t crc16;           // CRC16-CCITT integrity checksum
    uint8_t  end_marker;      // 0x0D
};

// ============================================================
// DUAL HARDWARE I2C OBJECTS & STATE
// ============================================================
static uint16_t g_sequence_num = 0;

// Bus 0 (Wire):  GPIO 21 / 22 for MPU-6500 / MPU-6050
// Bus 1 (Wire1): GPIO 25 / 26 for BME280 / BMP280 (Wire1 is pre-instantiated by ESP32 Wire library)

Adafruit_BME280 bme;
Adafruit_BMP280 bmp(&Wire1);

bool mpu_found = false;
uint8_t mpu_address = 0x68;
uint8_t mpu_chip_id = 0x00;

bool bme_found = false;
bool is_bmp = false;
uint8_t bme_address = 0x76;
uint8_t bme_chip_id = 0x00;

bool lora_initialized = false;

// ============================================================
// CRC16-CCITT CHECKSUM
// ============================================================
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

// ============================================================
// BUS 0 (WIRE: GPIO 21/22) HELPER FOR MPU-6500
// ============================================================
uint8_t read_mpu_register(uint8_t addr, uint8_t reg) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) {
        return 0xFF;
    }
    if (Wire.requestFrom((uint8_t)addr, (uint8_t)1, (uint8_t)true) == 1) {
        return Wire.read();
    }
    return 0xFF;
}

bool try_init_mpu() {
    for (uint8_t addr : {0x68, 0x69}) {
        uint8_t who = read_mpu_register(addr, 0x75);
        if (who != 0xFF && who != 0x00) {
            mpu_chip_id = who;

            // Wake up MPU
            Wire.beginTransmission(addr);
            Wire.write(0x6B);
            Wire.write(0x01);
            Wire.endTransmission(true);
            delay(10);

            // Configure Accelerometer to ±8G
            Wire.beginTransmission(addr);
            Wire.write(0x1C);
            Wire.write(0x10);
            Wire.endTransmission(true);
            delay(10);

            // Configure DLPF to 44Hz
            Wire.beginTransmission(addr);
            Wire.write(0x1A);
            Wire.write(0x03);
            Wire.endTransmission(true);
            delay(10);

            mpu_found = true;
            mpu_address = addr;

            const char* chip_name = "MPU-Clone";
            if (who == 0x68) chip_name = "MPU-6050";
            else if (who >= 0x70 && who <= 0x73) chip_name = "MPU-6500";
            else if (who == 0x98 || who == 0x75) chip_name = "MPU-9250";

            Serial.printf("  🎉 ✅ Bus 0 (GPIO 21/22): %s (ID=0x%02X) ACTIVE on 0x%02X!\n",
                          chip_name, who, addr);
            return true;
        }
    }
    return false;
}

float read_tilt_angle() {
    static float s_last_valid_tilt = 0.0f;
    static uint8_t s_fail_count = 0;

    if (!mpu_found) {
        return 0.0f;
    }

    float ax_sum = 0.0f, ay_sum = 0.0f, az_sum = 0.0f;
    int valid_samples = 0;

    for (int i = 0; i < 5; i++) {
        Wire.beginTransmission(mpu_address);
        Wire.write(0x3B);
        if (Wire.endTransmission(false) == 0) {
            if (Wire.requestFrom((int)mpu_address, 6, (int)true) == 6) {
                int16_t rawX = (Wire.read() << 8) | Wire.read();
                int16_t rawY = (Wire.read() << 8) | Wire.read();
                int16_t rawZ = (Wire.read() << 8) | Wire.read();

                ax_sum += (float)rawX / 4096.0f;
                ay_sum += (float)rawY / 4096.0f;
                az_sum += (float)rawZ / 4096.0f;
                valid_samples++;
            }
        }
        delayMicroseconds(500);
    }

    if (valid_samples == 0) {
        if (++s_fail_count >= 5) {
            Serial.println("  ⚠️ MPU consecutive read failures — marking offline.");
            s_last_valid_tilt = 0.0f;
            mpu_found = false;
            s_fail_count = 0;
        }
        return s_last_valid_tilt;
    }
    s_fail_count = 0;

    float ax = ax_sum / (float)valid_samples;
    float ay = ay_sum / (float)valid_samples;
    float az = az_sum / (float)valid_samples;

    float raw_tilt = atan2(sqrt(ax * ax + ay * ay), fabs(az)) * 180.0f / 3.14159265f;
    if (isnan(raw_tilt)) return s_last_valid_tilt;

    if (s_last_valid_tilt == 0.0f) {
        s_last_valid_tilt = raw_tilt;
    } else {
        s_last_valid_tilt = (0.3f * raw_tilt) + (0.7f * s_last_valid_tilt);
    }

    return s_last_valid_tilt;
}

// ============================================================
// BUS 1 (WIRE1: GPIO 25/26) HELPER FOR BME280 / BMP280
// ============================================================
uint8_t read_bme_register(uint8_t addr, uint8_t reg) {
    Wire1.beginTransmission(addr);
    Wire1.write(reg);
    if (Wire1.endTransmission(false) != 0) {
        return 0xFF;
    }
    if (Wire1.requestFrom((uint8_t)addr, (uint8_t)1, (uint8_t)true) == 1) {
        return Wire1.read();
    }
    return 0xFF;
}

bool try_init_bme() {
    uint8_t addrs[2] = {0x76, 0x77};
    for (uint8_t a : addrs) {
        uint8_t cid = read_bme_register(a, 0xD0);
        if (cid != 0xFF && cid != 0x00) {
            bme_chip_id = cid;

            // BME280 (Genuine Bosch = 0x60)
            if (cid == 0x60) {
                if (bme.begin(a, &Wire1)) {
                    bme_found = true;
                    is_bmp = false;
                    bme_address = a;
                    Serial.printf("  🎉 ✅ Bus 1 (GPIO 25/26): BME280 DETECTED on 0x%02X (ID=0x%02X)!\n", a, cid);
                    return true;
                }
            }

            // BMP280 (Genuine Bosch = 0x58, Clones = 0x56, 0x57)
            if (bmp.begin(a)) {
                bme_found = true;
                is_bmp = true;
                bme_address = a;
                Serial.printf("  🎉 ✅ Bus 1 (GPIO 25/26): BMP280 DETECTED on 0x%02X (ID=0x%02X)!\n", a, cid);
                return true;
            }
        }
    }
    return false;
}

// ============================================================
// SOIL MOISTURE (TRUE PHYSICAL ANALOG ADC)
// ============================================================
float read_soil_moisture() {
    int raw = analogRead(SOIL_ANALOG_PIN);
    const int DRY_AIR_VAL = 2800;
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

// ============================================================
// SETUP
// ============================================================
void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println("\n═══════════════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 2: LANDSLIDE HARDWARE SUITE ");
    Serial.println("  Dual-Bus: Wire (MPU: 21/22) + Wire1 (BME: 25/26)    ");
    Serial.println("═══════════════════════════════════════════════════════");

    analogSetAttenuation(ADC_11db);
    pinMode(SOIL_ANALOG_PIN, INPUT);

    // --- BUS 0 INITIALIZATION (MPU: GPIO 21 / 22) ---
    Serial.println("\n--- Initializing Bus 0 (Wire: SDA=GPIO21, SCL=GPIO22) ---");
    Wire.begin(MPU_SDA, MPU_SCL);
    Wire.setClock(100000);
    Wire.setTimeOut(100);
    delay(50);

    for (uint8_t a = 1; a < 127; a++) {
        Wire.beginTransmission(a);
        if (Wire.endTransmission(true) == 0) {
            Serial.printf("  ⭐ Bus 0 Device at 0x%02X\n", a);
        }
    }
    try_init_mpu();

    // --- BUS 1 INITIALIZATION (BME: GPIO 25 / 26) ---
    Serial.println("\n--- Initializing Bus 1 (Wire1: SDA=GPIO25, SCL=GPIO26) ---");
    Wire1.begin(BME_SDA, BME_SCL);
    Wire1.setClock(100000);
    Wire1.setTimeOut(100);
    delay(50);

    for (uint8_t a = 1; a < 127; a++) {
        Wire1.beginTransmission(a);
        if (Wire1.endTransmission(true) == 0) {
            Serial.printf("  ⭐ Bus 1 Device at 0x%02X\n", a);
        }
    }
    try_init_bme();

    // --- LoRa SX1278 SPI INITIALIZATION ---
    Serial.println("\n--- Initializing LoRa SX1278 (SPI) ---");
    pinMode(LORA_RST, OUTPUT);
    digitalWrite(LORA_RST, LOW);
    delay(10);
    digitalWrite(LORA_RST, HIGH);
    delay(15);

    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
    LoRa.setSPI(SPI);
    LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);

    if (LoRa.begin(LORA_FREQUENCY)) {
        lora_initialized = true;
        LoRa.setTxPower(LORA_TX_POWER);
        LoRa.setSpreadingFactor(LORA_SPREADING_FACTOR);
        LoRa.setSignalBandwidth(LORA_BANDWIDTH);
        LoRa.setCodingRate4(5);
        LoRa.setSyncWord(0xF3);
        LoRa.enableCrc();
        Serial.println("  ✅ LoRa SX1278 initialized successfully (433 MHz, SF7, CR 4/5)!");
    } else {
        Serial.println("  ❌ LoRa initialization failed! Check SPI wiring.");
    }

    Serial.println("═══════════════════════════════════════════════════════\n");
}

// ============================================================
// MAIN LOOP
// ============================================================
void loop() {
    // Non-blocking hot-plug re-probe every 3s
    static unsigned long s_last_retry = 0;
    unsigned long now = millis();
    if ((!mpu_found || !bme_found) && (now - s_last_retry > 3000)) {
        s_last_retry = now;

        if (!mpu_found) {
            try_init_mpu();
        }
        if (!bme_found) {
            uint8_t b76 = read_bme_register(0x76, 0xD0);
            uint8_t b77 = read_bme_register(0x77, 0xD0);
            Serial.printf("  [PROBE Bus 1 (25/26)] BME ID: 0x76=0x%02X, 0x77=0x%02X\n", b76, b77);
            try_init_bme();
        }
    }

    // 1. Read physical sensors
    float tilt = read_tilt_angle();
    float soil = read_soil_moisture();
    int rawSoil = analogRead(SOIL_ANALOG_PIN);

    // Read real pressure and temp if BME is active on Wire1
    float pressure = 0.0f;
    float temp = 0.0f;
    if (bme_found) {
        static uint8_t s_bme_fail_count = 0;
        float rawPress = (is_bmp ? bmp.readPressure() : bme.readPressure()) / 100.0f;
        float rawTemp  = is_bmp ? bmp.readTemperature() : bme.readTemperature();

        bool press_ok = !isnan(rawPress) && rawPress >= 300.0f && rawPress <= 1200.0f;
        bool temp_ok  = !isnan(rawTemp)  && rawTemp  >= -40.0f && rawTemp  <= 85.0f;

        if (press_ok && temp_ok) {
            pressure = rawPress;
            temp = rawTemp;
            s_bme_fail_count = 0;
        } else {
            if (++s_bme_fail_count >= 5) {
                Serial.println("  ⚠️ BME280 consecutive read failures — marking offline.");
                bme_found = false;
                is_bmp = false;
                s_bme_fail_count = 0;
            }
        }
    }

    // 2. Multi-layer risk fusion
    float l1_anomaly_f = (tilt > 0.0f) ? min(1.0f, max(0.0f, (tilt - 2.0f) / 15.0f)) : 0.0f;
    float l2_anomaly_f = min(1.0f, max(0.0f, (soil - 40.0f) / 50.0f));
    float l3_anomaly_f = (pressure > 0.0f) ? min(1.0f, max(0.0f, (1013.0f - pressure) / 20.0f)) : 0.0f;

    float combined_f = SLIDE_LAYER1_WEIGHT * l1_anomaly_f + SLIDE_LAYER2_WEIGHT * l2_anomaly_f + SLIDE_LAYER3_WEIGHT * l3_anomaly_f;
    bool is_priority = combined_f >= PRIORITY_THRESHOLD;

    // 3. Construct LoRa binary telemetry packet
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

    // 4. Transmit packet over 433 MHz LoRa
    if (lora_initialized) {
        LoRa.beginPacket();
        LoRa.write((const uint8_t*)&packet, sizeof(packet));
        LoRa.endPacket();

        Serial.printf("📡 SLD2 Sent: Tilt=%.1f°, Soil=%.1f%%, Press=%.1fhPa | Combined=%.2f | Seq=%d\n",
                      tilt, soil, pressure, combined_f, packet.sequence_num);
    }

    // 5. Output diagnostics
    Serial.printf("  [DIAG] Tilt=%.1f deg (%s, ID=0x%02X) | RawSoil(GPIO%d)=%d (Soil=%.1f%%) | BME=%s (ID=0x%02X, Temp=%.1fC Press=%.1fhPa)\n",
                  tilt, mpu_found ? "MPU OK" : "DISCONNECTED", mpu_chip_id,
                  SOIL_ANALOG_PIN, rawSoil, soil,
                  bme_found ? (is_bmp ? "BMP280 OK" : "BME280 OK") : "DISCONNECTED", bme_chip_id,
                  temp, pressure);

    // 6. Output JSON formatted line for local serial bridge
    Serial.printf("{\"node\":\"SLD2\",\"tilt\":%.1f,\"soil\":%.1f,\"press\":%.1f,\"anomaly\":%.2f,\"batt\":%d,\"seq\":%d}\n",
                  tilt, soil, pressure, combined_f, packet.battery_pct, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
