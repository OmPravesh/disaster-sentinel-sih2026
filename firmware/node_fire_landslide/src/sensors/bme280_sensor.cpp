/**
 * Disaster Sentinel — BME280 Environmental Sensor Implementation
 * 
 * Layer 3 — Environmental context for all calamity types.
 * Provides temperature, humidity, and barometric pressure readings.
 */

#include "bme280_sensor.h"
#include <Wire.h>

bool BME280Sensor::begin(uint8_t addr) {
    _initialized = false;
    _lastReading = {0, 0, 0, false};

    if (!_bme.begin(addr)) {
        Serial.println("[BME280] ERROR: Sensor not found!");
        Serial.printf("  Tried address: 0x%02X\n", addr);
        return false;
    }

    // Configure for weather monitoring (low power)
    _bme.setSampling(
        Adafruit_BME280::MODE_FORCED,      // Force mode — read on demand
        Adafruit_BME280::SAMPLING_X2,       // Temperature oversampling
        Adafruit_BME280::SAMPLING_X16,      // Pressure oversampling (high accuracy)
        Adafruit_BME280::SAMPLING_X1,       // Humidity oversampling
        Adafruit_BME280::FILTER_X16,        // IIR filter for pressure smoothing
        Adafruit_BME280::STANDBY_MS_0_5     // Standby time
    );

    _initialized = true;
    Serial.println("[BME280] Initialized successfully");
    Serial.printf("  Address: 0x%02X\n", addr);

    return true;
}

BME280Reading BME280Sensor::read() {
    BME280Reading reading;

    if (!_initialized) {
        reading.valid = false;
        return reading;
    }

    // Force a measurement in forced mode
    _bme.takeForcedMeasurement();

    reading.temperature = _bme.readTemperature();
    reading.humidity = _bme.readHumidity();
    reading.pressure = _bme.readPressure() / 100.0f;  // Pa → hPa
    reading.valid = true;

    // Sanity checks
    if (isnan(reading.temperature) || isnan(reading.humidity) || isnan(reading.pressure)) {
        reading.valid = false;
        Serial.println("[BME280] WARNING: NaN reading detected");
        return reading;
    }

    // Reasonable range check
    if (reading.temperature < -40.0f || reading.temperature > 85.0f) {
        reading.valid = false;
        Serial.printf("[BME280] WARNING: Temperature out of range: %.1f°C\n", reading.temperature);
        return reading;
    }

    _lastReading = reading;
    return reading;
}

float BME280Sensor::readTemperature() {
    if (!_initialized) return NAN;
    _bme.takeForcedMeasurement();
    return _bme.readTemperature();
}

float BME280Sensor::readHumidity() {
    if (!_initialized) return NAN;
    _bme.takeForcedMeasurement();
    return _bme.readHumidity();
}

float BME280Sensor::readPressure() {
    if (!_initialized) return NAN;
    _bme.takeForcedMeasurement();
    return _bme.readPressure() / 100.0f;  // Pa → hPa
}

BME280Reading BME280Sensor::getLastReading() {
    return _lastReading;
}

bool BME280Sensor::isHealthy() {
    if (!_initialized) return false;
    BME280Reading test = read();
    return test.valid;
}
