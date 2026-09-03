/**
 * Disaster Sentinel — Rain Sensor Implementation
 * 
 * YL-83 rain sensor module driver.
 * Layer 2 — Corroborating sensor for flood detection.
 * 
 * The YL-83 outputs LOWER analog values when wet (inverted).
 * This driver normalizes output to: 0.0 = dry, 1.0 = heavy rain.
 */

#include "rain_sensor.h"

void RainSensor::begin(int analogPin, int digitalPin) {
    _analogPin = analogPin;
    _digitalPin = digitalPin;
    _lastRaw = 0.0f;

    if (_digitalPin >= 0) {
        pinMode(_digitalPin, INPUT);
    }

    // ESP32 ADC attenuation for full 0-3.3V range
    analogSetAttenuation(ADC_11db);

    Serial.println("[RainSensor] Initialized");
    Serial.printf("  Analog pin: GPIO%d\n", _analogPin);
    if (_digitalPin >= 0) {
        Serial.printf("  Digital pin: GPIO%d\n", _digitalPin);
    }
}

float RainSensor::readIntensity() {
    // Average multiple readings for stability
    long sum = 0;
    const int samples = 10;

    for (int i = 0; i < samples; i++) {
        sum += analogRead(_analogPin);
        delay(5);
    }

    int avgRaw = sum / samples;
    _lastRaw = (float)avgRaw;

    // YL-83 is inverted: 4095 = dry, ~0 = fully wet
    // Normalize: 0.0 = dry, 1.0 = heavy rain
    float intensity = 1.0f - (avgRaw / 4095.0f);

    // Clamp
    if (intensity < 0.0f) intensity = 0.0f;
    if (intensity > 1.0f) intensity = 1.0f;

    return intensity;
}

int RainSensor::readRaw() {
    return analogRead(_analogPin);
}

bool RainSensor::isRaining() {
    if (_digitalPin >= 0) {
        // YL-83 DO pin: LOW = rain detected (with potentiometer threshold)
        return (digitalRead(_digitalPin) == LOW);
    }
    // Fallback: use analog threshold
    return (readIntensity() > 0.3f);
}

float RainSensor::getRawValue() {
    return _lastRaw;
}

bool RainSensor::isHealthy() {
    int raw = analogRead(_analogPin);
    // If stuck at 0 or 4095 continuously, sensor may be disconnected
    return (raw > 5 && raw < 4090);
}
