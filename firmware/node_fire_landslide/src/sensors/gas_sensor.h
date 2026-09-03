/**
 * Disaster Sentinel — MQ-2 Gas/Smoke Sensor Driver
 * 
 * Reads MQ-2 gas sensor for smoke, CO, and combustible gas detection.
 * 
 * Fire Layer 2 — Corroborating sensor for fire detection.
 * 
 * IMPORTANT: MQ-2 heater requires 5V and ~150mA.
 * Must be powered from separate regulator, NOT from ESP32 3.3V pin.
 * Analog output is through a voltage divider to bring to 3.3V for ESP32 ADC.
 * Heater needs ~20 seconds warm-up before readings are accurate.
 */

#ifndef GAS_SENSOR_H
#define GAS_SENSOR_H

#include <Arduino.h>

class GasSensor {
public:
    /**
     * Initialize MQ-2 gas sensor.
     * @param analogPin   ADC input (through voltage divider)
     * @param digitalPin  Digital threshold output (DO), -1 to disable
     * @param heaterPin   GPIO controlling heater via MOSFET, -1 if always on
     */
    void begin(int analogPin, int digitalPin = -1, int heaterPin = -1);

    /**
     * Turn on heater and wait for warm-up.
     * Call this before reading. Takes ~20 seconds.
     */
    void warmUp();

    /**
     * Turn off heater (power saving during deep sleep).
     */
    void heaterOff();

    /**
     * Read gas/smoke concentration as normalized value.
     * @return 0.0 (clean air) to 1.0 (heavy smoke/gas)
     */
    float readConcentration();

    /**
     * Check if gas/smoke threshold exceeded (digital output).
     */
    bool isGasDetected();

    int readRaw();
    float getRawValue();
    bool isHealthy();
    bool isWarmedUp();

private:
    int _analogPin;
    int _digitalPin;
    int _heaterPin;
    float _lastRaw;
    bool _warmedUp;
    unsigned long _warmUpStartTime;
};

#endif // GAS_SENSOR_H
