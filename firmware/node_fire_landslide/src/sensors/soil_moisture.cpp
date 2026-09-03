/**
 * Disaster Sentinel — Soil Moisture Sensor Implementation
 * Landslide Layer 2 — Corroborating sensor.
 */

#include "soil_moisture.h"

void SoilMoistureSensor::begin(int analogPin, int airValue, int waterValue) {
    _analogPin = analogPin;
    _airValue = airValue;
    _waterValue = waterValue;
    _lastRaw = 0.0f;

    analogSetAttenuation(ADC_11db);

    Serial.println("[SoilMoisture] Initialized");
    Serial.printf("  Pin: GPIO%d | Air: %d | Water: %d\n",
                  _analogPin, _airValue, _waterValue);
}

float SoilMoistureSensor::readPercent() {
    long sum = 0;
    const int samples = 10;

    for (int i = 0; i < samples; i++) {
        sum += analogRead(_analogPin);
        delay(5);
    }

    int avgRaw = sum / samples;
    _lastRaw = (float)avgRaw;

    // Capacitive sensor: lower ADC value = more moisture
    // Map from [airValue (dry), waterValue (wet)] to [0%, 100%]
    float percent = (float)(_airValue - avgRaw) / (float)(_airValue - _waterValue) * 100.0f;

    if (percent < 0.0f) percent = 0.0f;
    if (percent > 100.0f) percent = 100.0f;

    return percent;
}

int SoilMoistureSensor::readRaw() {
    return analogRead(_analogPin);
}

float SoilMoistureSensor::getRawValue() {
    return _lastRaw;
}

bool SoilMoistureSensor::isHealthy() {
    int raw = analogRead(_analogPin);
    return (raw > 100 && raw < 4000);
}
