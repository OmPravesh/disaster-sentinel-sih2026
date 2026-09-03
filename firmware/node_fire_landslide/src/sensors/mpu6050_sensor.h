/**
 * Disaster Sentinel — MPU6050 Tilt/Vibration Sensor Driver
 * 
 * Reads accelerometer and gyroscope data from MPU6050.
 * Computes tilt angle and vibration magnitude for landslide detection.
 * 
 * Landslide Layer 1 — Primary sensor.
 */

#ifndef MPU6050_SENSOR_H
#define MPU6050_SENSOR_H

#include <Arduino.h>
#include <Adafruit_MPU6050.h>

struct MPU6050Reading {
    float accelX, accelY, accelZ;  // m/s²
    float gyroX, gyroY, gyroZ;    // rad/s
    float tiltAngle;                // degrees from vertical
    float vibrationMagnitude;       // combined acceleration magnitude
    bool valid;
};

class MPU6050Sensor {
public:
    bool begin(uint8_t addr = 0x68);
    
    /**
     * Read all axes and compute tilt + vibration.
     */
    MPU6050Reading read();

    /**
     * Get tilt angle from vertical (degrees).
     * 0° = perfectly level, 90° = sideways
     */
    float readTiltAngle();

    /**
     * Get vibration magnitude (acceleration RMS minus gravity).
     * Higher values = more movement/vibration.
     */
    float readVibration();

    MPU6050Reading getLastReading();
    bool isHealthy();

private:
    Adafruit_MPU6050 _mpu;
    MPU6050Reading _lastReading;
    bool _initialized;

    float computeTilt(float ax, float ay, float az);
    float computeVibration(float ax, float ay, float az);
};

#endif // MPU6050_SENSOR_H
