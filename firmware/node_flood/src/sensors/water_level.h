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
     * Read water level / distance in centimeters.
     * Uses median filtering and temperature-compensated sound speed.
     * @param ambientTempC Current ambient temperature in Celsius (default 25.0C)
     * @return Measured distance in cm (20.0 to 600.0 cm)
     */
    float readCm(float ambientTempC = 25.0f);

    /**
     * Set linear calibration parameters: Calibrated = (Raw * scale) + offsetCm
     */
    void setCalibration(float scale, float offsetCm);

    /**
     * Get the raw sensor value before calibration (for debugging).
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
    float _rawDistance;
    unsigned long _lastReadTime;
    float _calScale;
    float _calOffset;

    float readUltrasonicSingle(float ambientTempC);
    float readAnalog();
    float medianReadings(int count = 5, float ambientTempC = 25.0f);
};

#endif // WATER_LEVEL_H
