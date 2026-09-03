/**
 * Disaster Sentinel — BME280 Environmental Sensor Driver
 * 
 * Reads temperature, humidity, and barometric pressure via I2C.
 * 
 * Layer 3 — Environmental context sensor.
 * 
 * For flood detection:
 *   - Low pressure + high humidity → storm conditions
 *   - Pressure drop rate → approaching weather system
 * 
 * For fire detection (on Node 2):
 *   - Temperature spike + humidity drop → fire conditions
 * 
 * For landslide detection (on Node 2):
 *   - Prolonged high humidity + low pressure → rain saturation
 */

#ifndef BME280_SENSOR_H
#define BME280_SENSOR_H

#include <Arduino.h>
#include <Adafruit_BME280.h>

struct BME280Reading {
    float temperature;    // °C
    float humidity;       // % RH
    float pressure;       // hPa
    bool valid;           // Reading successful
};

class BME280Sensor {
public:
    /**
     * Initialize BME280 on I2C bus.
     * @param addr I2C address (0x76 or 0x77)
     * @return true if sensor found
     */
    bool begin(uint8_t addr = 0x76);

    /**
     * Read all environmental parameters.
     * @return BME280Reading struct with temp, humidity, pressure
     */
    BME280Reading read();

    /**
     * Get individual readings.
     */
    float readTemperature();
    float readHumidity();
    float readPressure();

    /**
     * Get the last complete reading.
     */
    BME280Reading getLastReading();

    /**
     * Check if sensor is connected and responding.
     */
    bool isHealthy();

private:
    Adafruit_BME280 _bme;
    BME280Reading _lastReading;
    bool _initialized;
};

#endif // BME280_SENSOR_H
