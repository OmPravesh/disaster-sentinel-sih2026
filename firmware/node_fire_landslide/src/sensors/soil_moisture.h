/**
 * Disaster Sentinel — Soil Moisture Sensor Driver
 * 
 * Reads capacitive soil moisture sensor v1.2 (analog).
 * Landslide Layer 2 — Corroborating sensor.
 * 
 * Saturated soil is a key precondition for landslides.
 */

#ifndef SOIL_MOISTURE_H
#define SOIL_MOISTURE_H

#include <Arduino.h>

class SoilMoistureSensor {
public:
    /**
     * @param analogPin  ADC input pin
     * @param airValue   ADC reading in completely dry conditions (~3500)
     * @param waterValue ADC reading in water (~1500)
     */
    void begin(int analogPin, int airValue = 3500, int waterValue = 1500);

    /**
     * Read soil moisture as percentage.
     * @return 0% (dry) to 100% (saturated)
     */
    float readPercent();

    int readRaw();
    float getRawValue();
    bool isHealthy();

private:
    int _analogPin;
    int _airValue;
    int _waterValue;
    float _lastRaw;
};

#endif // SOIL_MOISTURE_H
