/**
 * Disaster Sentinel — Node 4 (Pollution) Main Firmware
 * 
 * ESP32 node operating in 2-Layer Mode (MQ-135 + PM2.5 Dust).
 * Features:
 *   - 1.8" ST7735 Color TFT SPI Display (128x160) with live telemetry dashboard
 *   - SX1278 433 MHz LoRa Radio Transceiver (Binary Protocol with CRC16)
 *   - USB Serial Telemetry for Central Hub Auto-Bridge
 * 
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include "config.h"

// 1.8" ST7735 TFT Instance
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// Color Palette (RGB565 format)
#define COLOR_BG        0x0841  // Very dark slate navy
#define COLOR_CARD      0x1082  // Dark slate card background
#define COLOR_WHITE     0xFFFF  // Pure white
#define COLOR_GRAY      0x9CF3  // Light slate gray
#define COLOR_CYAN      0x07FF  // Vibrant cyan / air
#define COLOR_GREEN     0x2667  // Emerald safe green
#define COLOR_AMBER     0xFD20  // Warning amber
#define COLOR_RED       0xF800  // Critical alert red
#define COLOR_BLUE      0x345F  // Header blue
#define COLOR_LINE      0x2965  // Subtle border line

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
bool lora_initialized = false;
bool tft_initialized = false;

// CRC16-CCITT Checksum Calculation
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

// Read MQ-135 Air Quality Sensor
float read_mq135_aqi() {
    int raw = analogRead(MQ135_ANALOG_PIN);
    float voltage = (raw / 4095.0f) * 3.3f;
    float aqi = (voltage / 3.3f) * 500.0f; // Scaled 0-500 AQI
    return aqi;
}

// Read Optical Dust Sensor (GP2Y1010AU0F)
float read_pm25_dust() {
    digitalWrite(PM25_LED_PIN, LOW); // Turn ON internal IR LED
    delayMicroseconds(280);
    int raw = analogRead(PM25_ANALOG_PIN);
    delayMicroseconds(40);
    digitalWrite(PM25_LED_PIN, HIGH); // Turn OFF internal IR LED

    float voltage = (raw / 4095.0f) * 3.3f;
    float dust_density = (voltage - 0.9f) * 0.2f * 1000.0f; // ug/m3
    return max(0.0f, dust_density);
}

// Battery Voltage Monitoring
uint8_t compute_battery_pct() {
    int raw = analogRead(BATTERY_ADC_PIN);
    float mv = (raw / 4095.0f) * 3300.0f * 2.0f; // 1/2 voltage divider
    if (mv >= BATTERY_FULL_MV) return 100;
    if (mv <= BATTERY_EMPTY_MV) return 0;
    return (uint8_t)(((mv - BATTERY_EMPTY_MV) / (BATTERY_FULL_MV - BATTERY_EMPTY_MV)) * 100.0f);
}

// ============================================================
// 1.8" ST7735 TFT DISPLAY ENGINE
// ============================================================

void draw_static_ui() {
    if (!tft_initialized) return;

    // Deselect LoRa on SPI bus
    digitalWrite(LORA_CS, HIGH);
    digitalWrite(TFT_CS, LOW);

    tft.fillScreen(COLOR_BG);

    // 1. Top Header Bar
    tft.fillRect(0, 0, 128, 22, COLOR_BLUE);
    tft.setTextSize(1);
    tft.setTextColor(COLOR_WHITE);
    tft.setCursor(6, 4);
    tft.print("DISASTER SENTINEL");
    tft.setTextColor(COLOR_CYAN);
    tft.setCursor(6, 13);
    tft.print("NODE 4 - AIR BASIN");

    // 2. Card 1 Outline: MQ-135 Gas / AQI
    tft.fillRoundRect(4, 26, 120, 38, 4, COLOR_CARD);
    tft.drawRoundRect(4, 26, 120, 38, 4, COLOR_LINE);
    tft.setTextSize(1);
    tft.setTextColor(COLOR_GRAY);
    tft.setCursor(10, 30);
    tft.print("AIR QUALITY (MQ135)");

    // 3. Card 2 Outline: PM2.5 Dust
    tft.fillRoundRect(4, 68, 120, 38, 4, COLOR_CARD);
    tft.drawRoundRect(4, 68, 120, 38, 4, COLOR_LINE);
    tft.setTextSize(1);
    tft.setTextColor(COLOR_GRAY);
    tft.setCursor(10, 72);
    tft.print("PM2.5 DUST SENSOR");

    // 4. Card 3 Outline: Threat Level & Bar
    tft.fillRoundRect(4, 110, 120, 32, 4, COLOR_CARD);
    tft.drawRoundRect(4, 110, 120, 32, 4, COLOR_LINE);
    tft.setTextSize(1);
    tft.setTextColor(COLOR_GRAY);
    tft.setCursor(10, 114);
    tft.print("THREAT LEVEL:");

    // 5. Bottom Status Strip
    tft.drawFastHLine(0, 146, 128, COLOR_LINE);
    tft.fillRect(0, 147, 128, 13, COLOR_BG);

    digitalWrite(TFT_CS, HIGH);
}

void update_display_metrics(float aqi, float pm25, float combined, bool is_priority, uint8_t batt, uint16_t seq) {
    if (!tft_initialized) return;

    // Deselect LoRa on SPI bus
    digitalWrite(LORA_CS, HIGH);
    digitalWrite(TFT_CS, LOW);

    // --- 1. Update AQI Value & Status ---
    tft.fillRect(10, 42, 108, 18, COLOR_CARD); // Clear old value
    tft.setTextSize(2);
    uint16_t aqi_color = (aqi < 100.0f) ? COLOR_GREEN : ((aqi < 200.0f) ? COLOR_AMBER : COLOR_RED);
    tft.setTextColor(aqi_color);
    tft.setCursor(10, 44);
    tft.printf("%.0f", aqi);
    
    tft.setTextSize(1);
    tft.setCursor(55, 45);
    tft.setTextColor(COLOR_GRAY);
    tft.print("AQI");
    tft.setCursor(55, 53);
    tft.setTextColor(aqi_color);
    if (aqi < 100.0f) tft.print("GOOD");
    else if (aqi < 200.0f) tft.print("MODERATE");
    else tft.print("ALERT!");

    // --- 2. Update PM2.5 Value & Status ---
    tft.fillRect(10, 84, 108, 18, COLOR_CARD); // Clear old value
    tft.setTextSize(2);
    uint16_t pm_color = (pm25 < 35.0f) ? COLOR_GREEN : ((pm25 < 75.0f) ? COLOR_AMBER : COLOR_RED);
    tft.setTextColor(pm_color);
    tft.setCursor(10, 86);
    tft.printf("%.1f", pm25);

    tft.setTextSize(1);
    tft.setCursor(68, 87);
    tft.setTextColor(COLOR_GRAY);
    tft.print("ug/m3");
    tft.setCursor(68, 95);
    tft.setTextColor(pm_color);
    if (pm25 < 35.0f) tft.print("OPTIMAL");
    else if (pm25 < 75.0f) tft.print("ELEVATED");
    else tft.print("CRITICAL");

    // --- 3. Update Threat Gauge Bar ---
    tft.fillRect(80, 114, 40, 10, COLOR_CARD);
    tft.setTextSize(1);
    uint16_t threat_color = (combined < 0.50f) ? COLOR_GREEN : ((combined < 0.70f) ? COLOR_AMBER : COLOR_RED);
    tft.setTextColor(threat_color);
    tft.setCursor(82, 114);
    tft.printf("%.0f%%", combined * 100.0f);

    // Threat progress bar (width = 108 px)
    tft.fillRect(10, 126, 108, 10, COLOR_BG);
    tft.drawRect(10, 126, 108, 10, COLOR_LINE);
    int bar_width = (int)(combined * 104.0f);
    if (bar_width > 104) bar_width = 104;
    if (bar_width > 0) {
        tft.fillRect(12, 128, bar_width, 6, threat_color);
    }

    // --- 4. Update Bottom Footer ---
    tft.fillRect(0, 148, 128, 12, COLOR_BG);
    tft.setTextSize(1);
    tft.setTextColor(lora_initialized ? COLOR_GREEN : COLOR_AMBER);
    tft.setCursor(4, 150);
    tft.printf("LoRa:%s#%d", lora_initialized ? "TX " : "OFF ", seq % 1000);

    tft.setTextColor(COLOR_CYAN);
    tft.setCursor(80, 150);
    tft.printf("BAT:%d%%", batt);

    digitalWrite(TFT_CS, HIGH);
}

// ============================================================
// ARDUINO SETUP & LOOP
// ============================================================

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("\n═══════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 4: POLLUTION (POL4)");
    Serial.println("  1.8\" ST7735 TFT + SX1278 LoRa Integrated");
    Serial.println("═══════════════════════════════════════════════");

    // Initialize Sensor GPIOs
    pinMode(MQ135_ANALOG_PIN, INPUT);
    pinMode(PM25_ANALOG_PIN, INPUT);
    pinMode(PM25_LED_PIN, OUTPUT);
    digitalWrite(PM25_LED_PIN, HIGH);

    // Initialize SPI Chip Selects (Keep DESELECTED by default)
    pinMode(LORA_CS, OUTPUT);
    digitalWrite(LORA_CS, HIGH);

    pinMode(TFT_CS, OUTPUT);
    digitalWrite(TFT_CS, HIGH);

    // Hardware reset pulse for SX1278
    pinMode(LORA_RST, OUTPUT);
    digitalWrite(LORA_RST, LOW);
    delay(10);
    digitalWrite(LORA_RST, HIGH);
    delay(15);

    // Shared Hardware SPI Bus
    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);

    // 1. Initialize 1.8" ST7735 TFT Screen
    Serial.print("  [TFT] Initializing 1.8\" ST7735 SPI Display...");
    tft.initR(INITR_BLACKTAB); // Standard 1.8" 128x160 BlackTab
    tft.setRotation(0);        // Portrait Mode (128 width x 160 height)
    tft_initialized = true;
    Serial.println(" OK!");

    // Draw static GUI frames
    draw_static_ui();

    // 2. Direct SPI diagnostic probe for SX1278
    digitalWrite(LORA_CS, LOW);
    SPI.transfer(0x42 & 0x7F);
    uint8_t probeVersion = SPI.transfer(0x00);
    digitalWrite(LORA_CS, HIGH);

    Serial.printf("  [LoRa SPI Probe] SX1278 Chip ID: 0x%02X (Expected 0x12)\n", probeVersion);

    // 3. Initialize LoRa Radio
    LoRa.setSPI(SPI);
    LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);

    if (LoRa.begin(LORA_FREQUENCY)) {
        lora_initialized = true;
        LoRa.setTxPower(LORA_TX_POWER);
        LoRa.setSpreadingFactor(LORA_SPREADING_FACTOR);
        LoRa.setSignalBandwidth(LORA_BANDWIDTH);
        LoRa.setSyncWord(0xF3);
        LoRa.enableCrc();
        Serial.println("  [LoRa] SX1278 initialized successfully (433 MHz, SF7)!");
    } else {
        Serial.println("  [LoRa] SX1278 init failed. Node will continue via USB Serial!");
    }

    Serial.println("✅ Node POL4 initialization complete. Starting sensor acquisition...\n");
}

void loop() {
    float aqi = read_mq135_aqi();
    float pm25 = read_pm25_dust();
    uint8_t batt = compute_battery_pct();

    // 2-Layer Anomaly Scoring
    float l1_anomaly_f = min(1.0f, max(0.0f, (aqi - 50.0f) / 250.0f));
    float l2_anomaly_f = min(1.0f, max(0.0f, (pm25 - 25.0f) / 150.0f));
    float combined_f = POL_LAYER1_WEIGHT * l1_anomaly_f + POL_LAYER2_WEIGHT * l2_anomaly_f;

    bool is_priority = combined_f >= PRIORITY_THRESHOLD;

    // Prepare Binary LoRa Packet
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
    packet.battery_pct = batt;
    packet.sequence_num = ++g_sequence_num;
    packet.end_marker = 0x0D;

    // Calculate CRC16 checksum
    size_t payload_len = sizeof(LoRaPacket) - 3;
    packet.crc16 = calculate_crc16((const uint8_t*)&packet, payload_len);

    // --- 1. Wireless LoRa Transmission ---
    if (lora_initialized) {
        digitalWrite(TFT_CS, HIGH); // Ensure TFT is unselected
        digitalWrite(LORA_CS, LOW);
        LoRa.beginPacket();
        LoRa.write((const uint8_t*)&packet, sizeof(packet));
        LoRa.endPacket();
        digitalWrite(LORA_CS, HIGH);
    }

    // --- 2. Live TFT Display Update ---
    update_display_metrics(aqi, pm25, combined_f, is_priority, batt, packet.sequence_num);

    // --- 3. USB Serial Telemetry (Matches Jetson serial_bridge.py regex) ---
    Serial.printf("📡 POL4 Sent: AQI=%.1f (L1=%.2f), PM2.5=%.1f (L2=%.2f) | Combined=%.2f | Seq=%d\n",
                  aqi, l1_anomaly_f, pm25, l2_anomaly_f, combined_f, packet.sequence_num);

    // JSON line for external serial loggers
    Serial.printf("{\"node\":\"POL4\",\"aqi\":%.1f,\"pm25\":%.1f,\"anomaly\":%.2f,\"batt\":%d,\"seq\":%d}\n",
                  aqi, pm25, combined_f, batt, packet.sequence_num);

    uint32_t interval = is_priority ? ALERT_INTERVAL_MS : (combined_f >= ELEVATED_THRESHOLD ? ELEVATED_INTERVAL_MS : NORMAL_INTERVAL_MS);
    delay(interval);
}
