/**
 * Disaster Sentinel — BME280 / BMP280 Environmental Sensor Implementation
 * 
 * Layer 3 — Environmental context for all calamity types.
 * Provides temperature, humidity, and barometric pressure readings.
 * Auto-detects BME280 or BMP280 on addresses 0x76 or 0x77.
 */

#include "bme280_sensor.h"
#include <Wire.h>

bool BME280Sensor::begin(uint8_t addr) {
    _initialized = false;
    _isBmp = false;
    _lastReading = {0, 0, 0, false};

    uint8_t addrs[2] = {addr, (uint8_t)(addr == 0x76 ? 0x77 : 0x76)};

    // Step 1: Try BME280 (Temp + Humidity + Pressure)
    for (uint8_t a : addrs) {
        if (_bme.begin(a)) {
            _bme.setSampling(
                Adafruit_BME280::MODE_FORCED,
                Adafruit_BME280::SAMPLING_X2,
                Adafruit_BME280::SAMPLING_X16,
                Adafruit_BME280::SAMPLING_X1,
                Adafruit_BME280::FILTER_X16,
                Adafruit_BME280::STANDBY_MS_0_5
            );
            _initialized = true;
            _isBmp = false;
            Serial.println("[BME280] BME280 detected and initialized successfully!");
            Serial.printf("  Address: 0x%02X\n", a);
            return true;
        }
    }

    // Step 2: Try BMP280 (Temp + Pressure)
    for (uint8_t a : addrs) {
        if (_bmp.begin(a)) {
            _bmp.setSampling(
                Adafruit_BMP280::MODE_FORCED,
                Adafruit_BMP280::SAMPLING_X2,
                Adafruit_BMP280::SAMPLING_X16,
                Adafruit_BMP280::FILTER_X16,
                Adafruit_BMP280::STANDBY_MS_500
            );
            _initialized = true;
            _isBmp = true;
            Serial.println("[BME280] BMP280 detected and initialized successfully!");
            Serial.printf("  Address: 0x%02X (Temperature & Pressure active)\n", a);
            return true;
        }
    }

    Serial.println("[BME280] ERROR: Sensor not found on 0x76 or 0x77!");
    Serial.println("  Check wiring: VCC->3.3V, GND->GND, SCL->GPIO22, SDA->GPIO21, CSB->3.3V");
    return false;
}

BME280Reading BME280Sensor::read() {
    BME280Reading reading;

    if (!_initialized) {
        reading.valid = false;
        return reading;
    }

    if (_isBmp) {
        _bmp.takeForcedMeasurement();
        reading.temperature = _bmp.readTemperature();
        reading.pressure = _bmp.readPressure() / 100.0f;  // Pa -> hPa
        reading.humidity = 50.0f;  // BMP280 does not have humidity; nominal baseline
        reading.valid = true;
    } else {
        _bme.takeForcedMeasurement();
        reading.temperature = _bme.readTemperature();
        reading.humidity = _bme.readHumidity();
        reading.pressure = _bme.readPressure() / 100.0f;  // Pa -> hPa
        reading.valid = true;
    }

    if (isnan(reading.temperature) || isnan(reading.pressure)) {
        reading.valid = false;
        Serial.println("[BME280] WARNING: NaN reading detected");
        return reading;
    }

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
    if (_isBmp) {
        _bmp.takeForcedMeasurement();
        return _bmp.readTemperature();
    }
    _bme.takeForcedMeasurement();
    return _bme.readTemperature();
}

float BME280Sensor::readHumidity() {
    if (!_initialized) return NAN;
    if (_isBmp) return 50.0f;
    _bme.takeForcedMeasurement();
    return _bme.readHumidity();
}

float BME280Sensor::readPressure() {
    if (!_initialized) return NAN;
    if (_isBmp) {
        _bmp.takeForcedMeasurement();
        return _bmp.readPressure() / 100.0f;
    }
    _bme.takeForcedMeasurement();
    return _bme.readPressure() / 100.0f;
}

BME280Reading BME280Sensor::getLastReading() {
    return _lastReading;
}

bool BME280Sensor::isHealthy() {
    if (!_initialized) return false;
    BME280Reading test = read();
    return test.valid;
}
