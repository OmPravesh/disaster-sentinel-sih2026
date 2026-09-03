/**
 * ═══════════════════════════════════════════════════════════
 * DISASTER SENTINEL — Node 1: Flood Monitoring
 * ═══════════════════════════════════════════════════════════
 * 
 * ESP32 field node for flood detection using 3-layer sensor
 * prediction system:
 * 
 *   Layer 1 (Primary):       Water Level Sensor
 *   Layer 2 (Corroborating): Rain Sensor (YL-83)
 *   Layer 3 (Context):       BME280 (Pressure/Humidity)
 * 
 * Flow:
 *   1. Read all 3 sensor layers
 *   2. Compute per-layer anomaly scores (z-score based)
 *   3. Combine into 3-layer confidence score
 *   4. Format LoRa packet with all layer data
 *   5. Transmit via SX1278 LoRa
 *   6. Enter adaptive deep sleep
 * 
 * On first boot (or if baseline invalid):
 *   - Enters baseline collection mode for 48 hours
 *   - Collects normal environmental statistics
 *   - Stores baseline in NVS flash
 *   - After baseline period, switches to monitoring mode
 * 
 * SIH 2026 | Problem Statement SIH26178 | Qualcomm
 * ═══════════════════════════════════════════════════════════
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>

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

// Sequence counter (persisted in RTC memory to survive deep sleep)
RTC_DATA_ATTR uint16_t seqCounter = 0;

// Boot counter (for debugging)
RTC_DATA_ATTR uint32_t bootCount = 0;

// Previous water level reading (for rate calculation)
RTC_DATA_ATTR float prevWaterLevel = 0.0f;
RTC_DATA_ATTR unsigned long prevWaterTime = 0;
RTC_DATA_ATTR bool hasPrevWater = false;

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

    // --- I2C ---
    Wire.begin(BME_SDA, BME_SCL);

    // --- Initialize sensors ---
    Serial.println("--- Initializing Sensors ---");

    // Layer 1: Water Level
    waterSensor.begin(WATER_TRIG_PIN, WATER_ECHO_PIN, WATER_ANALOG_PIN, true);

    // Layer 2: Rain
    rainSensor.begin(RAIN_ANALOG_PIN, RAIN_DIGITAL_PIN);

    // Layer 3: BME280
    if (!bmeSensor.begin(BME_ADDR)) {
        Serial.println("!!! BME280 FAILED — Layer 3 will be unavailable !!!");
    }

    // --- Initialize baseline manager ---
    baseline.begin("flood_bl", BASELINE_MIN_SAMPLES);
    baseline.setChannelCount(NUM_CHANNELS);
    baseline.load();  // Try to load from NVS

    // --- Initialize anomaly engine ---
    anomalyEngine.begin(&baseline, ANOMALY_Z_THRESHOLD);

    // --- Initialize 3-layer combiner ---
    threeLayer.begin(LAYER1_WEIGHT, LAYER2_WEIGHT, LAYER3_WEIGHT);

    // --- Initialize LoRa ---
    if (!lora.begin(LORA_CS, LORA_RST, LORA_DIO0,
                    LORA_FREQUENCY, LORA_TX_POWER,
                    LORA_SPREADING_FACTOR, LORA_BANDWIDTH)) {
        Serial.println("!!! LoRa FAILED — Cannot transmit !!!");
        // Still continue to collect baseline data
    }

    // --- Initialize sleep manager ---
    sleepMgr.begin(BATTERY_ADC_PIN);

    // --- Sensor warm-up ---
    delay(SENSOR_WARMUP_MS);

    // ============================================================
    // MAIN MEASUREMENT CYCLE
    // ============================================================

    Serial.println("\n--- Reading Sensors ---");

    // === Layer 1: Water Level ===
    float waterLevel = waterSensor.readCm();
    Serial.printf("  L1 Water Level: %.1f cm\n", waterLevel);

    // Calculate rate of change
    float waterRate = 0.0f;
    unsigned long now = millis();
    if (hasPrevWater && prevWaterTime > 0) {
        // Rate in cm/minute (approximate using boot intervals)
        float timeDeltaMin = 2.0f;  // Approximate — assumes ~2 min between boots
        waterRate = (waterLevel - prevWaterLevel) / timeDeltaMin;
        Serial.printf("  L1 Rate: %.2f cm/min\n", waterRate);
    }

    // === Layer 2: Rain ===
    float rainIntensity = rainSensor.readIntensity();
    float rainRaw = rainSensor.getRawValue();
    Serial.printf("  L2 Rain Intensity: %.2f (raw: %.0f)\n", rainIntensity, rainRaw);

    // === Layer 3: BME280 ===
    BME280Reading bme = bmeSensor.read();
    float pressure = bme.valid ? bme.pressure : 0.0f;
    float humidity = bme.valid ? bme.humidity : 0.0f;
    float temperature = bme.valid ? bme.temperature : 0.0f;
    Serial.printf("  L3 Pressure: %.1f hPa | Humidity: %.1f%% | Temp: %.1f°C\n",
                  pressure, humidity, temperature);

    // === Battery ===
    uint8_t battery = sleepMgr.readBatteryPercent();
    Serial.printf("  Battery: %d%%\n", battery);

    // ============================================================
    // BASELINE / ANOMALY PROCESSING
    // ============================================================

    // Always add readings to baseline (continuously refines)
    baseline.addReading(CH_WATER_LEVEL, waterLevel);
    baseline.addReading(CH_RAIN, rainIntensity);
    baseline.addReading(CH_PRESSURE, pressure);
    baseline.addReading(CH_HUMIDITY, humidity);
    baseline.addReading(CH_TEMPERATURE, temperature);

    // Check if still in baseline collection mode
    bool baselineMode = !baseline.isCollectionComplete(BASELINE_DURATION_HOURS);

    ThreeLayerResult result;

    if (baselineMode) {
        // === BASELINE COLLECTION MODE ===
        float hours = baseline.getHoursCollected();
        uint32_t samples = baseline.getStats(CH_WATER_LEVEL).sampleCount;
        Serial.printf("\n--- BASELINE MODE ---\n");
        Serial.printf("  Hours collected: %.1f / %d\n", hours, BASELINE_DURATION_HOURS);
        Serial.printf("  Samples: %u / %u\n", samples, BASELINE_MIN_SAMPLES);
        Serial.println("  Anomaly detection not yet active\n");

        // Send a baseline-mode packet (all anomaly scores = 0)
        result.layer1Score = 0.0f;
        result.layer2Score = 0.0f;
        result.layer3Score = 0.0f;
        result.combinedScore = 0.0f;
        result.rateFlag = 0;
        result.confirmation = CONFIRM_NONE;

        // Save baseline periodically (every ~10 boots)
        if (bootCount % 10 == 0) {
            baseline.save();
            Serial.println("  Baseline saved to NVS");
        }
    } else {
        // === MONITORING MODE ===
        Serial.println("\n--- MONITORING MODE ---");

        // Compute per-layer anomaly scores
        AnomalyResult l1Anomaly = anomalyEngine.computeAnomalyWithRate(
            CH_WATER_LEVEL, waterLevel, waterRate);

        AnomalyResult l2Anomaly = anomalyEngine.computeAnomaly(
            CH_RAIN, rainIntensity);

        // For Layer 3, combine pressure and humidity anomalies
        AnomalyResult l3Pressure = anomalyEngine.computeAnomaly(
            CH_PRESSURE, pressure);
        AnomalyResult l3Humidity = anomalyEngine.computeAnomaly(
            CH_HUMIDITY, humidity);

        // Layer 3 anomaly = max of pressure and humidity anomalies
        // (storm conditions: low pressure OR high humidity)
        AnomalyResult l3Combined;
        l3Combined.combinedAnomaly = max(l3Pressure.combinedAnomaly,
                                          l3Humidity.combinedAnomaly);
        l3Combined.valueAnomaly = max(l3Pressure.valueAnomaly,
                                       l3Humidity.valueAnomaly);
        l3Combined.rateAnomaly = 0;
        l3Combined.zScore = max(l3Pressure.zScore, l3Humidity.zScore);
        l3Combined.rateZScore = 0;

        // Compute 3-layer combined result
        result = threeLayer.compute(l1Anomaly, l2Anomaly, l3Combined, waterRate);

        // Debug output
        Serial.printf("  L1 anomaly: %.3f (z=%.2f)\n",
                      result.layer1Score, l1Anomaly.zScore);
        Serial.printf("  L2 anomaly: %.3f (z=%.2f)\n",
                      result.layer2Score, l2Anomaly.zScore);
        Serial.printf("  L3 anomaly: %.3f (z=%.2f)\n",
                      result.layer3Score, l3Combined.zScore);
        Serial.printf("  Combined:   %.3f\n", result.combinedScore);
        Serial.printf("  Layers anomalous: %d/3\n", result.layersAnomalous);
        Serial.printf("  Confirmation: %s\n",
                      result.confirmation == CONFIRM_HIGH   ? "HIGH ✅" :
                      result.confirmation == CONFIRM_MEDIUM ? "MEDIUM ⚠️" :
                      result.confirmation == CONFIRM_LOW    ? "LOW" : "NONE");
        Serial.printf("  Rate flag: %d\n", result.rateFlag);
    }

    // ============================================================
    // BUILD AND SEND LoRa PACKET
    // ============================================================

    Serial.println("\n--- Transmitting LoRa Packet ---");

    bool isPriority = (result.combinedScore >= PRIORITY_THRESHOLD);

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
    seqCounter++;

    // ============================================================
    // UPDATE STATE FOR NEXT WAKE
    // ============================================================

    prevWaterLevel = waterLevel;
    prevWaterTime = now;
    hasPrevWater = true;

    // ============================================================
    // ADAPTIVE DEEP SLEEP
    // ============================================================

    // Save baseline before sleep if anomaly detected
    if (result.combinedScore > 0.5f) {
        baseline.save();
    }

    // Put LoRa to sleep
    lora.sleep();

    Serial.println("\n--- Entering Deep Sleep ---");
    sleepMgr.adaptiveSleep(
        result.combinedScore,
        DEEP_SLEEP_NORMAL_US,                            // Normal: 2 min
        (uint64_t)ELEVATED_INTERVAL_MS * 1000ULL,        // Elevated: 30 sec
        DEEP_SLEEP_ALERT_US                              // Alert: 15 sec
    );

    // Never reaches here — ESP32 resets on wake
}

void loop() {
    // Never called — deep sleep resets the ESP32
    // All logic is in setup()
}
