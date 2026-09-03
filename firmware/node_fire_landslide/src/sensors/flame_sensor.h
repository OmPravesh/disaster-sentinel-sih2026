/**
 * Disaster Sentinel — Flame/IR Sensor Driver
 * 
 * Reads KY-026 flame sensor (analog + digital).
 * Detects infrared radiation from flames.
 * 
 * Fire Layer 1 — Primary sensor for fire detection.
 * 
 * Note: KY-026 analog output is INVERTED — lower values = stronger flame.
 */

#ifndef FLAME_SENSOR_H
#define FLAME_SENSOR_H

#include <Arduino.h>

class FlameSensor {
public:
    void begin(int analogPin, int digitalPin = -1);
    
    /**
     * Read flame intensity as normalized value.
     * @return 0.0 (no flame) to 1.0 (strong flame detected)
     */
    float readIntensity();
    
    /**
     * Check if flame is detected via digital output.
     */
    bool isFlameDetected();
    
    int readRaw();
    float getRawValue();
    bool isHealthy();

private:
    int _analogPin;
    int _digitalPin;
    float _lastRaw;
};

#endif // FLAME_SENSOR_H
