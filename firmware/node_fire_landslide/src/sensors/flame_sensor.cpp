/**
 * Disaster Sentinel — Flame/IR Sensor Implementation
 * Fire Layer 1 — Primary sensor.
 */

#include "flame_sensor.h"

void FlameSensor::begin(int analogPin, int digitalPin) {
    _analogPin = analogPin;
    _digitalPin = digitalPin;
    _lastRaw = 0.0f;

    if (_digitalPin >= 0) {
        pinMode(_digitalPin, INPUT);
    }
    analogSetAttenuation(ADC_11db);

    Serial.println("[FlameSensor] Initialized");
    Serial.printf("  Analog: GPIO%d | Digital: GPIO%d\n", _analogPin, 
                  _digitalPin >= 0 ? _digitalPin : -1);
}

float FlameSensor::readIntensity() {
    long sum = 0;
    const int samples = 10;

    for (int i = 0; i < samples; i++) {
        sum += analogRead(_analogPin);
        delay(2);
    }

    int avgRaw = sum / samples;
    _lastRaw = (float)avgRaw;

    // KY-026 is inverted: 4095 = no flame, ~0 = strong flame
    float intensity = 1.0f - (avgRaw / 4095.0f);

    if (intensity < 0.0f) intensity = 0.0f;
    if (intensity > 1.0f) intensity = 1.0f;

    return intensity;
}

bool FlameSensor::isFlameDetected() {
    if (_digitalPin >= 0) {
        return (digitalRead(_digitalPin) == LOW);  // KY-026: LOW = flame detected
    }
    return (readIntensity() > 0.4f);
}

int FlameSensor::readRaw() {
    return analogRead(_analogPin);
}

float FlameSensor::getRawValue() {
    return _lastRaw;
}

bool FlameSensor::isHealthy() {
    int raw = analogRead(_analogPin);
    return (raw > 5 && raw < 4090);
}
