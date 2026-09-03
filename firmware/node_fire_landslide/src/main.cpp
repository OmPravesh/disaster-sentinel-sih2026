/**
 * ═══════════════════════════════════════════════════════════
 * DISASTER SENTINEL — Node 2: Fire + Landslide Monitoring
 * ═══════════════════════════════════════════════════════════
 * 
 * Combined ESP32 field node monitoring TWO hazard types:
 * 
 *   FIRE:
 *     Layer 1 (Primary):       Flame/IR Sensor (KY-026)
 *     Layer 2 (Corroborating): MQ-2 Gas/Smoke Sensor
 *     Layer 3 (Context):       BME280 (temp spike + humidity drop)
 * 
 *   LANDSLIDE:
 *     Layer 1 (Primary):       MPU6050 (tilt + vibration)
 *     Layer 2 (Corroborating): Soil Moisture Sensor
 *     Layer 3 (Context):       BME280 (shared — rain conditions)
 * 
 * Sends TWO LoRa packets per cycle: one for Fire, one for Landslide.
 * 
 * SIH 2026 | Problem Statement SIH26178 | Qualcomm
 * ═══════════════════════════════════════════════════════════
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>

#include "config.h"
#include "sensors/flame_sensor.h"
#include "sensors/gas_sensor.h"
#include "sensors/mpu6050_sensor.h"
#include "sensors/soil_moisture.h"
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

// Fire sensors
FlameSensor flameSensor;
GasSensor gasSensor;

// Landslide sensors
MPU6050Sensor mpuSensor;
SoilMoistureSensor soilSensor;

// Shared
BME280Sensor bmeSensor;

// Two separate baseline managers (fire vs landslide)
BaselineManager fireBaseline;
BaselineManager slideBaseline;

// Two anomaly engines
AnomalyEngine fireAnomalyEngine;
AnomalyEngine slideAnomalyEngine;

// Two 3-layer combiners (different weights possible)
ThreeLayerCombiner fireThreeLayer;
ThreeLayerCombiner slideThreeLayer;

LoRaTx lora;
SleepManager sleepMgr;

// Persisted in RTC memory across deep sleep
RTC_DATA_ATTR uint16_t seqCounter = 0;
RTC_DATA_ATTR uint32_t bootCount = 0;

// ============================================================
// SENSOR CHANNEL INDICES — FIRE
// ============================================================
#define FIRE_CH_FLAME        0   // Layer 1: Flame intensity
#define FIRE_CH_GAS          1   // Layer 2: Gas concentration
#define FIRE_CH_TEMPERATURE  2   // Layer 3a: Temperature
#define FIRE_CH_HUMIDITY     3   // Layer 3b: Humidity
#define FIRE_NUM_CHANNELS    4

// ============================================================
// SENSOR CHANNEL INDICES — LANDSLIDE
// ============================================================
#define SLIDE_CH_TILT        0   // Layer 1: Tilt angle
#define SLIDE_CH_VIBRATION   1   // Layer 1b: Vibration magnitude
#define SLIDE_CH_SOIL        2   // Layer 2: Soil moisture
#define SLIDE_CH_PRESSURE    3   // Layer 3a: Barometric pressure
#define SLIDE_CH_HUMIDITY    4   // Layer 3b: Humidity
#define SLIDE_NUM_CHANNELS   5

// ============================================================
// SETUP (runs on every boot — ESP32 resets from deep sleep)
// ============================================================

void setup() {
    Serial.begin(115200);
    delay(100);

    bootCount++;
    Serial.println("\n═══════════════════════════════════════════════");
    Serial.println("  DISASTER SENTINEL — Node 2: FIRE + LANDSLIDE");
    Serial.printf("  Node ID: %s\n", NODE_ID);
    Serial.printf("  Boot #%u | Seq #%u\n", bootCount, seqCounter);
    Serial.println("═══════════════════════════════════════════════\n");

    // --- I2C ---
    Wire.begin(BME_SDA, BME_SCL);

    // --- Initialize ALL sensors ---
    Serial.println("--- Initializing Sensors ---");

    // Fire L1: Flame
    flameSensor.begin(FLAME_ANALOG_PIN, FLAME_DIGITAL_PIN);

    // Fire L2: Gas (turn on heater)
    gasSensor.begin(GAS_ANALOG_PIN, GAS_DIGITAL_PIN, MQ2_HEATER_PIN);
    gasSensor.warmUp();  // 20 second warm-up

    // Landslide L1: MPU6050
    if (!mpuSensor.begin(MPU_ADDR)) {
        Serial.println("!!! MPU6050 FAILED — Landslide L1 unavailable !!!");
    }

    // Landslide L2: Soil Moisture
    soilSensor.begin(SOIL_ANALOG_PIN);

    // Shared L3: BME280
    if (!bmeSensor.begin(BME_ADDR)) {
        Serial.println("!!! BME280 FAILED — Layer 3 unavailable !!!");
    }

    // --- Initialize baselines ---
    fireBaseline.begin("fire_bl", BASELINE_MIN_SAMPLES);
    fireBaseline.setChannelCount(FIRE_NUM_CHANNELS);
    fireBaseline.load();

    slideBaseline.begin("slide_bl", BASELINE_MIN_SAMPLES);
    slideBaseline.setChannelCount(SLIDE_NUM_CHANNELS);
    slideBaseline.load();

    // --- Initialize anomaly engines ---
    fireAnomalyEngine.begin(&fireBaseline, ANOMALY_Z_THRESHOLD);
    slideAnomalyEngine.begin(&slideBaseline, ANOMALY_Z_THRESHOLD);

    // --- Initialize 3-layer combiners ---
    fireThreeLayer.begin(FIRE_LAYER1_WEIGHT, FIRE_LAYER2_WEIGHT, FIRE_LAYER3_WEIGHT);
    slideThreeLayer.begin(SLIDE_LAYER1_WEIGHT, SLIDE_LAYER2_WEIGHT, SLIDE_LAYER3_WEIGHT);

    // --- Initialize LoRa ---
    if (!lora.begin(LORA_CS, LORA_RST, LORA_DIO0,
                    LORA_FREQUENCY, LORA_TX_POWER,
                    LORA_SPREADING_FACTOR, LORA_BANDWIDTH)) {
        Serial.println("!!! LoRa FAILED — Cannot transmit !!!");
    }

    // --- Initialize sleep manager ---
    sleepMgr.begin(BATTERY_ADC_PIN);

    // ============================================================
    // READ ALL SENSORS
    // ============================================================

    Serial.println("\n--- Reading Sensors ---");

    // --- Fire sensors ---
    float flameIntensity = flameSensor.readIntensity();
    float gasConcentration = gasSensor.readConcentration();
    Serial.printf("  🔥 Flame: %.3f | Gas: %.3f\n", flameIntensity, gasConcentration);

    // --- Landslide sensors ---
    MPU6050Reading mpuReading = mpuSensor.read();
    float tiltAngle = mpuReading.valid ? mpuReading.tiltAngle : 0.0f;
    float vibration = mpuSensor.readVibration();
    float soilMoisture = soilSensor.readPercent();
    Serial.printf("  ⛰️  Tilt: %.1f° | Vibration: %.3f | Soil: %.1f%%\n",
                  tiltAngle, vibration, soilMoisture);

    // --- Shared BME280 ---
    BME280Reading bme = bmeSensor.read();
    float temperature = bme.valid ? bme.temperature : 0.0f;
    float humidity = bme.valid ? bme.humidity : 0.0f;
    float pressure = bme.valid ? bme.pressure : 0.0f;
    Serial.printf("  🌡️  Temp: %.1f°C | Humid: %.1f%% | Press: %.1f hPa\n",
                  temperature, humidity, pressure);

    // --- Battery ---
    uint8_t battery = sleepMgr.readBatteryPercent();
    Serial.printf("  🔋 Battery: %d%%\n", battery);

    // Turn off MQ-2 heater to save power
    gasSensor.heaterOff();

    // ============================================================
    // UPDATE BASELINES
    // ============================================================

    // Fire baseline
    fireBaseline.addReading(FIRE_CH_FLAME, flameIntensity);
    fireBaseline.addReading(FIRE_CH_GAS, gasConcentration);
    fireBaseline.addReading(FIRE_CH_TEMPERATURE, temperature);
    fireBaseline.addReading(FIRE_CH_HUMIDITY, humidity);

    // Landslide baseline
    slideBaseline.addReading(SLIDE_CH_TILT, tiltAngle);
    slideBaseline.addReading(SLIDE_CH_VIBRATION, vibration);
    slideBaseline.addReading(SLIDE_CH_SOIL, soilMoisture);
    slideBaseline.addReading(SLIDE_CH_PRESSURE, pressure);
    slideBaseline.addReading(SLIDE_CH_HUMIDITY, humidity);

    // ============================================================
    // ANOMALY DETECTION
    // ============================================================

    bool baselineMode = !fireBaseline.isCollectionComplete(BASELINE_DURATION_HOURS) ||
                        !slideBaseline.isCollectionComplete(BASELINE_DURATION_HOURS);

    ThreeLayerResult fireResult;
    ThreeLayerResult slideResult;

    if (baselineMode) {
        Serial.printf("\n--- BASELINE MODE ---\n");
        Serial.printf("  Fire hours: %.1f | Slide hours: %.1f\n",
                      fireBaseline.getHoursCollected(), slideBaseline.getHoursCollected());

        // Zero anomaly during baseline
        fireResult = {0, 0, 0, 0, 0, CONFIRM_NONE, 0};
        slideResult = {0, 0, 0, 0, 0, CONFIRM_NONE, 0};

        if (bootCount % 10 == 0) {
            fireBaseline.save();
            slideBaseline.save();
        }
    } else {
        Serial.println("\n--- MONITORING MODE ---");

        // ===== FIRE ANOMALY =====
        AnomalyResult firL1 = fireAnomalyEngine.computeAnomaly(FIRE_CH_FLAME, flameIntensity);
        AnomalyResult firL2 = fireAnomalyEngine.computeAnomaly(FIRE_CH_GAS, gasConcentration);

        // Fire L3: Temperature spike (high anomaly) AND humidity drop (inverted — low humidity is anomalous for fire)
        AnomalyResult firL3Temp = fireAnomalyEngine.computeAnomaly(FIRE_CH_TEMPERATURE, temperature);
        AnomalyResult firL3Humid = fireAnomalyEngine.computeAnomaly(FIRE_CH_HUMIDITY, humidity);

        AnomalyResult firL3;
        firL3.combinedAnomaly = max(firL3Temp.combinedAnomaly, firL3Humid.combinedAnomaly);
        firL3.valueAnomaly = firL3.combinedAnomaly;
        firL3.rateAnomaly = 0;
        firL3.zScore = max(firL3Temp.zScore, firL3Humid.zScore);
        firL3.rateZScore = 0;

        fireResult = fireThreeLayer.compute(firL1, firL2, firL3);

        Serial.println("  🔥 FIRE:");
        Serial.printf("    L1(flame): %.3f | L2(gas): %.3f | L3(env): %.3f\n",
                      fireResult.layer1Score, fireResult.layer2Score, fireResult.layer3Score);
        Serial.printf("    Combined: %.3f | Layers: %d/3 | Confirm: %d\n",
                      fireResult.combinedScore, fireResult.layersAnomalous, fireResult.confirmation);

        // ===== LANDSLIDE ANOMALY =====
        // L1: combine tilt and vibration anomalies
        AnomalyResult sldL1Tilt = slideAnomalyEngine.computeAnomaly(SLIDE_CH_TILT, tiltAngle);
        AnomalyResult sldL1Vib = slideAnomalyEngine.computeAnomaly(SLIDE_CH_VIBRATION, vibration);

        AnomalyResult sldL1;
        sldL1.combinedAnomaly = max(sldL1Tilt.combinedAnomaly, sldL1Vib.combinedAnomaly);
        sldL1.valueAnomaly = sldL1.combinedAnomaly;
        sldL1.rateAnomaly = 0;
        sldL1.zScore = max(sldL1Tilt.zScore, sldL1Vib.zScore);
        sldL1.rateZScore = 0;

        AnomalyResult sldL2 = slideAnomalyEngine.computeAnomaly(SLIDE_CH_SOIL, soilMoisture);

        AnomalyResult sldL3Press = slideAnomalyEngine.computeAnomaly(SLIDE_CH_PRESSURE, pressure);
        AnomalyResult sldL3Humid = slideAnomalyEngine.computeAnomaly(SLIDE_CH_HUMIDITY, humidity);

        AnomalyResult sldL3;
        sldL3.combinedAnomaly = max(sldL3Press.combinedAnomaly, sldL3Humid.combinedAnomaly);
        sldL3.valueAnomaly = sldL3.combinedAnomaly;
        sldL3.rateAnomaly = 0;
        sldL3.zScore = max(sldL3Press.zScore, sldL3Humid.zScore);
        sldL3.rateZScore = 0;

        slideResult = slideThreeLayer.compute(sldL1, sldL2, sldL3);

        Serial.println("  ⛰️  LANDSLIDE:");
        Serial.printf("    L1(motion): %.3f | L2(soil): %.3f | L3(env): %.3f\n",
                      slideResult.layer1Score, slideResult.layer2Score, slideResult.layer3Score);
        Serial.printf("    Combined: %.3f | Layers: %d/3 | Confirm: %d\n",
                      slideResult.combinedScore, slideResult.layersAnomalous, slideResult.confirmation);
    }

    // ============================================================
    // BUILD AND SEND TWO LoRa PACKETS
    // ============================================================

    Serial.println("\n--- Transmitting LoRa Packets ---");

    // --- Packet 1: FIRE ---
    bool firePriority = (fireResult.combinedScore >= PRIORITY_THRESHOLD);
    SentinelPacket firePkt = buildPacket(
        NODE_ID,
        HAZARD_FIRE,
        flameIntensity,       fireResult.layer1Score,
        gasConcentration,     fireResult.layer2Score,
        temperature,          fireResult.layer3Score,
        fireResult.combinedScore,
        fireResult.rateFlag,
        battery,
        seqCounter,
        firePriority
    );
    lora.sendPacket(firePkt);
    seqCounter++;

    delay(200);  // Small gap between transmissions

    // --- Packet 2: LANDSLIDE ---
    bool slidePriority = (slideResult.combinedScore >= PRIORITY_THRESHOLD);
    SentinelPacket slidePkt = buildPacket(
        "SLD2",              // Different node ID for landslide data from same physical node
        HAZARD_LANDSLIDE,
        tiltAngle,           slideResult.layer1Score,
        soilMoisture,        slideResult.layer2Score,
        pressure,            slideResult.layer3Score,
        slideResult.combinedScore,
        slideResult.rateFlag,
        battery,
        seqCounter,
        slidePriority
    );
    lora.sendPacket(slidePkt);
    seqCounter++;

    // ============================================================
    // SAVE & SLEEP
    // ============================================================

    float maxCombined = max(fireResult.combinedScore, slideResult.combinedScore);

    if (maxCombined > 0.5f) {
        fireBaseline.save();
        slideBaseline.save();
    }

    lora.sleep();

    Serial.println("\n--- Entering Deep Sleep ---");
    sleepMgr.adaptiveSleep(
        maxCombined,
        DEEP_SLEEP_NORMAL_US,
        (uint64_t)ELEVATED_INTERVAL_MS * 1000ULL,
        DEEP_SLEEP_ALERT_US
    );
}

void loop() {
    // Never called — deep sleep resets the ESP32
}
