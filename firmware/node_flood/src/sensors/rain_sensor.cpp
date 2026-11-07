/**
 * Disaster Sentinel — Rain Sensor Implementation
 * 
 * YL-83 / FC-37 Rain Sensor Module Driver.
 * Layer 2 — Corroborating sensor for flood detection.
 * 
 * Electrical characteristics of YL-83:
 *   - Dry plate: Resistance is very high (~MΩ), AO outputs near VCC (ADC ~3800-4095)
 *   - Moisture/Rain: Surface tracks conduct, AO drops down to ~500-2500 (lower = heavier rain)
 *   - Disconnected / Floating / Unpowered: ADC reads near 0 (treated as disconnected, NOT 100% rain!)
 *   - Digital DO pin: Active LOW (LM393 comparator triggers LOW when rain crosses potentiometer threshold)
 */

#include "rain_sensor.h"

// Calibration thresholds for YL-83 on ESP32 12-bit ADC (0-4095)
static const int DRY_ADC_THRESHOLD = 3900;     // Completely dry
static const int SOAKED_ADC_THRESHOLD = 600;   // Maximum heavy rain saturation
static const int DISCONNECTED_ADC_MIN = 30;    // Readings below 30 indicate disconnected pin

void RainSensor::begin(int analogPin, int digitalPin) {
    _analogPin = analogPin;
    _digitalPin = digitalPin;
    _lastRaw = 0.0f;

    if (_digitalPin >= 0) {
        pinMode(_digitalPin, INPUT_PULLUP);
    }

    analogSetAttenuation(ADC_11db);  // Full 0-3.3V ADC range

    Serial.println("[RainSensor] Initialized YL-83 Driver");
    Serial.printf("  AO (Analog): GPIO%d | DO (Digital): GPIO%d\n", _analogPin, _digitalPin);
}

float RainSensor::readIntensity() {
    long sum = 0;
    const int samples = 12;

    for (int i = 0; i < samples; i++) {
        sum += analogRead(_analogPin);
        delay(4);
    }

    int avgRaw = sum / samples;
    _lastRaw = (float)avgRaw;

    // Check for disconnected or unpowered analog wire
    bool digitalWet = (_digitalPin >= 0 && digitalRead(_digitalPin) == LOW);

    if (avgRaw < DISCONNECTED_ADC_MIN && !digitalWet) {
        // Pin is reading 0 with no digital rain trigger -> wire is disconnected/unpowered
        // Do NOT falsely trigger a 100% rain alarm!
        return 0.0f;
    }

    // Active range scaling:
    // avgRaw >= DRY_ADC_THRESHOLD -> 0.0 (Dry)
    // avgRaw <= SOAKED_ADC_THRESHOLD -> 1.0 (Heavy rain)
    float intensity = 0.0f;
    if (avgRaw < DRY_ADC_THRESHOLD) {
        intensity = (float)(DRY_ADC_THRESHOLD - avgRaw) / (float)(DRY_ADC_THRESHOLD - SOAKED_ADC_THRESHOLD);
    }

    // Digital cross-validation: if DO comparator triggered wet, ensure intensity is at least 0.35
    if (digitalWet && intensity < 0.35f) {
        intensity = 0.35f;
    }

    if (intensity < 0.0f) intensity = 0.0f;
    if (intensity > 1.0f) intensity = 1.0f;

    return intensity;
}

int RainSensor::readRaw() {
    return analogRead(_analogPin);
}

bool RainSensor::isRaining() {
    if (_digitalPin >= 0) {
        if (digitalRead(_digitalPin) == LOW) return true;
    }
    return (readIntensity() > 0.15f);
}

float RainSensor::getRawValue() {
    return _lastRaw;
}

bool RainSensor::isHealthy() {
    int raw = analogRead(_analogPin);
    return (raw >= DISCONNECTED_ADC_MIN);
}
