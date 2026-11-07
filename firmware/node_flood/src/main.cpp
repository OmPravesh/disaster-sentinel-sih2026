/**
 * ═══════════════════════════════════════════════════════════
 * DISASTER SENTINEL — Node 1: Flood Monitoring
 * ═══════════════════════════════════════════════════════════
 * 
 * ESP32 field node for flood detection using 3-layer sensor
 * prediction system + 0.96" I2C OLED Display:
 * 
 *   Layer 1 (Primary):       Water Level Sensor (Ultrasonic / Analog)
 *   Layer 2 (Corroborating): Rain Sensor (YL-83)
 *   Layer 3 (Context):       BME280 / BMP280 (Pressure/Temp/Humidity)
 *   Display:                 0.96" 128x64 White OLED (I2C SSD1306)
 *   Wireless:                SX1278 LoRa 433 MHz
 * 
 * SIH 2026 | Problem Statement SIH26178 | Qualcomm
 * ═══════════════════════════════════════════════════════════
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "config.h"
#include "sensors/water_level.h"
#include "sensors/rain_sensor.h"
#include "sensors/bme280_sensor.h"
#include "anomaly/baseline.h"
#include "anomaly/anomaly_engine.h"
#include "anomaly/three_layer.h"
#include "lora/lora_tx.h"
#include "lora/packet_format.h"
#include "power/sleep_manager.h"

// ============================================================
// GLOBAL OBJECTS
// ============================================================

WaterLevelSensor waterSensor;
RainSensor rainSensor;
BME280Sensor bmeSensor;

BaselineManager baseline;
AnomalyEngine anomalyEngine;
ThreeLayerCombiner threeLayer;

LoRaTx lora;
SleepManager sleepMgr;

// 0.96" SSD1306 I2C OLED
Adafruit_SSD1306 oled(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
bool oledReady = false;

// Sequence counter
uint16_t seqCounter = 0;
uint32_t bootCount = 0;

// Previous water level reading (for rate calculation)
float prevWaterLevel = 0.0f;
unsigned long prevWaterTime = 0;
bool hasPrevWater = false;

// ============================================================
// SENSOR CHANNEL INDICES
// ============================================================
#define CH_WATER_LEVEL  0  // Layer 1
#define CH_RAIN         1  // Layer 2
#define CH_PRESSURE     2  // Layer 3 (primary context)
#define CH_HUMIDITY     3  // Layer 3 (secondary context)
#define CH_TEMPERATURE  4  // Additional context
#define NUM_CHANNELS    5

// ============================================================
// OLED DISPLAY HELPER
// ============================================================

void drawOledSplash() {
    if (!oledReady) return;
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);

    oled.drawRect(0, 0, 128, 64, SSD1306_WHITE);
    oled.setTextSize(1);
    oled.setCursor(14, 8);
    oled.print(F("DISASTER SENTINEL"));
    oled.setCursor(20, 24);
    oled.print(F("NODE 1: FLOOD"));
    oled.setCursor(12, 40);
    oled.print(F("SX1278 LoRa 433MHz"));
    oled.setCursor(22, 50);
    oled.print(F("System Online..."));
    oled.display();
}

void updateOledDisplay(float waterLevel, float rainIntensity, float pressure, float humidity, float temp, float combinedScore, bool isPriority, uint8_t batt, uint16_t seq) {
    if (!oledReady) return;

    oled.clearDisplay();

    // 1. Top Inverted Header Bar
    oled.fillRect(0, 0, 128, 12, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    oled.setTextSize(1);
    oled.setCursor(4, 2);
    oled.print(F("FLD1  FLOOD MONITOR"));

    oled.setCursor(104, 2);
    oled.printf("%d%%", batt);

    // 2. Body Metrics
    oled.setTextColor(SSD1306_WHITE);

    // Line 1: Water Level (cm and m)
    oled.setCursor(2, 16);
    oled.printf("Water: %.1fcm (%.2fm)", waterLevel, waterLevel / 100.0f);

    // Line 2: Rain Intensity
    oled.setCursor(2, 28);
    oled.printf("Rain:  %.1f mm/h", rainIntensity);

    // Line 3: Pressure & Temp
    oled.setCursor(2, 40);
    oled.printf("Baro:  %.0f hPa %.0fC", pressure > 0 ? pressure : 1013.2f, temp);

    // 3. Footer Separator Line
    oled.drawFastHLine(0, 51, 128, SSD1306_WHITE);

    // 4. Status Bar
    oled.setCursor(2, 54);
    oled.printf("TX#%u", seq);

    oled.setCursor(46, 54);
    oled.printf("Risk:%.2f", combinedScore);

    if (isPriority) {
        oled.fillRect(94, 53, 34, 11, SSD1306_WHITE);
        oled.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        oled.setCursor(96, 55);
        oled.print(F("WARN!"));
    } else {
        oled.setTextColor(SSD1306_WHITE);
        oled.setCursor(98, 54);
        oled.print(F("[SAFE]"));
    }

    oled.display();
}

// ============================================================
// SETUP
// ============================================================

void setup() {
    // --- Serial ---
    Serial.begin(115200);
    delay(100);

    bootCount++;
    Serial.println("\n═══════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 1: FLOOD");
    Serial.printf("  Node ID: %s\n", NODE_ID);
    Serial.printf("  Boot #%u | Seq #%u\n", bootCount, seqCounter);
    Serial.println("═══════════════════════════════════════════════\n");

    // --- I2C Initialization (Shared Bus: BME280 + OLED) ---
    Wire.begin(BME_SDA, BME_SCL);

    // --- Initialize 0.96" I2C OLED (Auto-probe 0x3C and 0x3D) ---
    if (oled.begin(SSD1306_SWITCHCAPVCC, 0x3C) || oled.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
        oledReady = true;
        Serial.println("✅ 0.96\" I2C OLED (SSD1306) Initialized Successfully");
        drawOledSplash();
        delay(1000);
    } else {
        Serial.println("⚠️ OLED display not found on 0x3C or 0x3D (check GND, VCC->3.3V, SCL->GPIO22, SDA->GPIO21)");
    }

    // --- Initialize sensors ---
    Serial.println("--- Initializing Sensors ---");

    // Layer 1: Water Level
    waterSensor.begin(WATER_TRIG_PIN, WATER_ECHO_PIN, WATER_ANALOG_PIN, true);

    // Layer 2: Rain
    rainSensor.begin(RAIN_ANALOG_PIN, RAIN_DIGITAL_PIN);

    // Layer 3: BME280
    if (!bmeSensor.begin(BME_ADDR)) {
        Serial.println("⚠️ BME280 not responding on 0x76, fallback to nominal baro");
    }

    // --- Initialize baseline manager ---
    baseline.begin("flood_bl", BASELINE_MIN_SAMPLES);
    baseline.setChannelCount(NUM_CHANNELS);
    baseline.load();  // Try to load from NVS

    // --- Initialize anomaly engine ---
    anomalyEngine.begin(&baseline, ANOMALY_Z_THRESHOLD);

    // --- Initialize 3-layer combiner ---
    threeLayer.begin(LAYER1_WEIGHT, LAYER2_WEIGHT, LAYER3_WEIGHT);

    // --- Initialize LoRa SX1278 ---
    if (!lora.begin(LORA_CS, LORA_RST, LORA_DIO0,
                    LORA_FREQUENCY, LORA_TX_POWER,
                    LORA_SPREADING_FACTOR, LORA_BANDWIDTH)) {
        Serial.println("⚠️ LoRa initialization failed or SX1278 not responding!");
    } else {
        Serial.println("✅ SX1278 LoRa Initialized @ 433 MHz");
    }

    // --- Initialize sleep manager (for battery reading) ---
    sleepMgr.begin(BATTERY_ADC_PIN);

    // Sensor warm-up
    delay(SENSOR_WARMUP_MS);
}

// ============================================================
// MAIN LOOP (Live Continuous Telemetry & Display)
// ============================================================

void loop() {
    unsigned long loopStart = millis();

    // === Layer 1: Water Level ===
    float waterLevel = waterSensor.readCm();

    // Calculate rate of change
    float waterRate = 0.0f;
    unsigned long now = millis();
    if (hasPrevWater && prevWaterTime > 0) {
        float timeDeltaMin = (float)(now - prevWaterTime) / 60000.0f;
        if (timeDeltaMin > 0.01f) {
            waterRate = (waterLevel - prevWaterLevel) / timeDeltaMin;
        }
    }

    // === Layer 2: Rain ===
    float rainIntensity = rainSensor.readIntensity();
    float rainRaw = rainSensor.getRawValue();

    // === Layer 3: BME280 ===
    BME280Reading bme = bmeSensor.read();
    float pressure = bme.valid ? bme.pressure : 1013.2f;
    float humidity = bme.valid ? bme.humidity : 55.0f;
    float temperature = bme.valid ? bme.temperature : 25.0f;

    // === Battery ===
    uint8_t battery = sleepMgr.readBatteryPercent();
    if (battery == 0) battery = 96;  // Fallback nominal when running on USB 5V

    // === Baseline / Anomaly Processing ===
    baseline.addReading(CH_WATER_LEVEL, waterLevel);
    baseline.addReading(CH_RAIN, rainIntensity);
    baseline.addReading(CH_PRESSURE, pressure);
    baseline.addReading(CH_HUMIDITY, humidity);
    baseline.addReading(CH_TEMPERATURE, temperature);

    bool baselineMode = !baseline.isCollectionComplete(BASELINE_DURATION_HOURS);
    ThreeLayerResult result;

    if (baselineMode) {
        result.layer1Score = 0.0f;
        result.layer2Score = 0.0f;
        result.layer3Score = 0.0f;
        result.combinedScore = 0.0f;
        result.rateFlag = 0;
        result.confirmation = CONFIRM_NONE;
    } else {
        AnomalyResult l1Anomaly = anomalyEngine.computeAnomalyWithRate(
            CH_WATER_LEVEL, waterLevel, waterRate);
        AnomalyResult l2Anomaly = anomalyEngine.computeAnomaly(
            CH_RAIN, rainIntensity);
        AnomalyResult l3Pressure = anomalyEngine.computeAnomaly(
            CH_PRESSURE, pressure);
        AnomalyResult l3Humidity = anomalyEngine.computeAnomaly(
            CH_HUMIDITY, humidity);

        AnomalyResult l3Combined;
        l3Combined.combinedAnomaly = max(l3Pressure.combinedAnomaly, l3Humidity.combinedAnomaly);
        l3Combined.valueAnomaly = max(l3Pressure.valueAnomaly, l3Humidity.valueAnomaly);
        l3Combined.rateAnomaly = 0;
        l3Combined.zScore = max(l3Pressure.zScore, l3Humidity.zScore);
        l3Combined.rateZScore = 0;

        result = threeLayer.compute(l1Anomaly, l2Anomaly, l3Combined, waterRate);
    }

    bool isPriority = (result.combinedScore >= PRIORITY_THRESHOLD);
    seqCounter++;

    // === 1. Transmit via LoRa ===
    SentinelPacket pkt = buildPacket(
        NODE_ID,
        HAZARD_FLOOD,
        waterLevel,       result.layer1Score,
        rainIntensity,    result.layer2Score,
        pressure,         result.layer3Score,
        result.combinedScore,
        result.rateFlag,
        battery,
        seqCounter,
        isPriority
    );

    lora.sendPacket(pkt);

    // === 2. Update Live 0.96" OLED Display ===
    updateOledDisplay(waterLevel, rainIntensity, pressure, humidity, temperature,
                      result.combinedScore, isPriority, battery, seqCounter);

    // === 3. Standardized USB Serial Telemetry for serial_bridge.py ===
    Serial.printf("📡 FLD1 Sent: Water=%.1fcm, Rain=%.1f, Press=%.1f | Combined=%.2f | Seq=%u\n",
                  waterLevel, rainIntensity, pressure, result.combinedScore, seqCounter);

    // JSON formatted packet for web loggers
    Serial.printf("{\"node\":\"FLD1\",\"water_level\":%.1f,\"rain\":%.1f,\"pressure\":%.1f,\"anomaly\":%.2f,\"batt\":%d,\"seq\":%u}\n",
                  waterLevel, rainIntensity, pressure, result.combinedScore, battery, seqCounter);

    // Update state tracking
    prevWaterLevel = waterLevel;
    prevWaterTime = now;
    hasPrevWater = true;

    // Cadence: 3.5 seconds normal, 1.5 seconds if priority
    uint32_t loopDelay = isPriority ? 1500 : 3500;
    unsigned long elapsed = millis() - loopStart;
    if (elapsed < loopDelay) {
        delay(loopDelay - elapsed);
    }
}
