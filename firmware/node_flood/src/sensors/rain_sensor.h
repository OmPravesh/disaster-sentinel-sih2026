/**
 * Disaster Sentinel — Rain Sensor Driver
 * 
 * Reads YL-83 rain sensor module (analog + digital).
 * Returns rain intensity as a normalized value (0.0 = dry, 1.0 = heavy rain).
 * 
 * Layer 2 — Corroborating sensor for flood detection.
 * 
 * Note: YL-83 analog output is INVERTED — lower values = more rain.
 */

#ifndef RAIN_SENSOR_H
#define RAIN_SENSOR_H

#include <Arduino.h>

class RainSensor {
public:
    /**
     * Initialize the rain sensor.
     * @param analogPin  Analog output pin (AO)
     * @param digitalPin  Digital threshold pin (DO), -1 to disable
     */
    void begin(int analogPin, int digitalPin = -1);

    /**
     * Read rain intensity as normalized value.
     * @return 0.0 (dry) to 1.0 (heavy rain)
     */
    float readIntensity();

    /**
     * Read raw analog value (0-4095).
     * Lower values = more rain for YL-83.
     */
    int readRaw();

    /**
     * Check digital threshold output.
     * @return true if rain detected above module's potentiometer threshold.
     */
    bool isRaining();

    /**
     * Get last reading raw value.
     */
    float getRawValue();

    /**
     * Check sensor health.
     */
    bool isHealthy();

private:
    int _analogPin;
    int _digitalPin;
    float _lastRaw;
};

#endif // RAIN_SENSOR_H
