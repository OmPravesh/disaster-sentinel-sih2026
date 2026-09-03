/**
 * Disaster Sentinel — Water Level Sensor Driver
 * 
 * Supports both ultrasonic (JSN-SR04T) and analog water-level sensors.
 * Returns water level in centimeters.
 * 
 * Layer 1 — Primary sensor for flood detection.
 */

#ifndef WATER_LEVEL_H
#define WATER_LEVEL_H

#include <Arduino.h>

class WaterLevelSensor {
public:
    /**
     * Initialize the water level sensor.
     * @param trigPin  Ultrasonic trigger pin (set -1 for analog-only mode)
     * @param echoPin  Ultrasonic echo pin
     * @param analogPin  Analog input pin (fallback / alternative sensor)
     * @param useUltrasonic  true = JSN-SR04T, false = analog sensor
     */
    void begin(int trigPin, int echoPin, int analogPin, bool useUltrasonic = true);

    /**
     * Read water level in centimeters.
     * Averages multiple readings for stability.
     * @return Water level in cm (0.0 = no water, higher = deeper)
     */
    float readCm();

    /**
     * Get the raw sensor value (for debugging/packet).
     */
    float getRawValue();

    /**
     * Check if sensor is responding.
     */
    bool isHealthy();

private:
    int _trigPin;
    int _echoPin;
    int _analogPin;
    bool _useUltrasonic;
    float _lastReading;
    unsigned long _lastReadTime;

    float readUltrasonic();
    float readAnalog();
    float averageReadings(int count = 5);
};

#endif // WATER_LEVEL_H
