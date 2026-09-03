/**
 * Disaster Sentinel — MQ-2 Gas/Smoke Sensor Implementation
 * Fire Layer 2 — Corroborating sensor.
 */

#include "gas_sensor.h"

static const unsigned long MQ2_WARMUP_TIME_MS = 20000;  // 20 seconds

void GasSensor::begin(int analogPin, int digitalPin, int heaterPin) {
    _analogPin = analogPin;
    _digitalPin = digitalPin;
    _heaterPin = heaterPin;
    _lastRaw = 0.0f;
    _warmedUp = false;
    _warmUpStartTime = 0;

    if (_digitalPin >= 0) {
        pinMode(_digitalPin, INPUT);
    }

    if (_heaterPin >= 0) {
        pinMode(_heaterPin, OUTPUT);
        digitalWrite(_heaterPin, LOW);  // Heater off initially
    }

    analogSetAttenuation(ADC_11db);

    Serial.println("[GasSensor] MQ-2 Initialized");
    Serial.printf("  Analog: GPIO%d | Digital: GPIO%d | Heater: GPIO%d\n",
                  _analogPin,
                  _digitalPin >= 0 ? _digitalPin : -1,
                  _heaterPin >= 0 ? _heaterPin : -1);
}

void GasSensor::warmUp() {
    if (_heaterPin >= 0) {
        digitalWrite(_heaterPin, HIGH);  // Turn on heater
        Serial.println("[GasSensor] Heater ON — warming up...");
    }

    _warmUpStartTime = millis();

    // Wait for heater warm-up
    delay(MQ2_WARMUP_TIME_MS);

    _warmedUp = true;
    Serial.println("[GasSensor] Warm-up complete — ready for readings");
}

void GasSensor::heaterOff() {
    if (_heaterPin >= 0) {
        digitalWrite(_heaterPin, LOW);
        Serial.println("[GasSensor] Heater OFF — power saving");
    }
    _warmedUp = false;
}

float GasSensor::readConcentration() {
    if (!_warmedUp) {
        Serial.println("[GasSensor] WARNING: Reading before warm-up!");
    }

    long sum = 0;
    const int samples = 10;

    for (int i = 0; i < samples; i++) {
        sum += analogRead(_analogPin);
        delay(5);
    }

    int avgRaw = sum / samples;
    _lastRaw = (float)avgRaw;

    // MQ-2: Higher analog value = higher gas concentration
    // Normalize to 0.0-1.0 range
    float concentration = avgRaw / 4095.0f;

    if (concentration < 0.0f) concentration = 0.0f;
    if (concentration > 1.0f) concentration = 1.0f;

    return concentration;
}

bool GasSensor::isGasDetected() {
    if (_digitalPin >= 0) {
        return (digitalRead(_digitalPin) == LOW);  // MQ-2 DO: LOW = gas detected
    }
    return (readConcentration() > 0.4f);
}

int GasSensor::readRaw() {
    return analogRead(_analogPin);
}

float GasSensor::getRawValue() {
    return _lastRaw;
}

bool GasSensor::isHealthy() {
    if (!_warmedUp) return true;  // Can't check before warm-up
    int raw = analogRead(_analogPin);
    return (raw > 5 && raw < 4090);
}

bool GasSensor::isWarmedUp() {
    return _warmedUp;
}
