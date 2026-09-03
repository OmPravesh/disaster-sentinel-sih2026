/**
 * Disaster Sentinel — MPU6050 Tilt/Vibration Implementation
 * Landslide Layer 1 — Primary sensor.
 */

#include "mpu6050_sensor.h"
#include <Wire.h>

bool MPU6050Sensor::begin(uint8_t addr) {
    _initialized = false;
    _lastReading = {0, 0, 0, 0, 0, 0, 0, 0, false};

    if (!_mpu.begin(addr)) {
        Serial.println("[MPU6050] ERROR: Sensor not found!");
        return false;
    }

    // Configure for low-power ground monitoring
    _mpu.setAccelerometerRange(MPU6050_RANGE_4_G);    // ±4g for landslide detection
    _mpu.setGyroRange(MPU6050_RANGE_500_DEG);         // ±500°/s
    _mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);      // Low-pass filter for stability

    _initialized = true;
    Serial.println("[MPU6050] Initialized successfully");
    return true;
}

MPU6050Reading MPU6050Sensor::read() {
    MPU6050Reading reading;

    if (!_initialized) {
        reading.valid = false;
        return reading;
    }

    sensors_event_t accel, gyro, temp;
    _mpu.getEvent(&accel, &gyro, &temp);

    reading.accelX = accel.acceleration.x;
    reading.accelY = accel.acceleration.y;
    reading.accelZ = accel.acceleration.z;
    reading.gyroX = gyro.gyro.x;
    reading.gyroY = gyro.gyro.y;
    reading.gyroZ = gyro.gyro.z;

    reading.tiltAngle = computeTilt(reading.accelX, reading.accelY, reading.accelZ);
    reading.vibrationMagnitude = computeVibration(reading.accelX, reading.accelY, reading.accelZ);
    reading.valid = true;

    _lastReading = reading;
    return reading;
}

float MPU6050Sensor::readTiltAngle() {
    MPU6050Reading r = read();
    return r.valid ? r.tiltAngle : -1.0f;
}

float MPU6050Sensor::readVibration() {
    // Average vibration over multiple rapid readings
    float sum = 0;
    const int samples = 20;

    for (int i = 0; i < samples; i++) {
        MPU6050Reading r = read();
        if (r.valid) {
            sum += r.vibrationMagnitude;
        }
        delay(5);
    }

    return sum / samples;
}

MPU6050Reading MPU6050Sensor::getLastReading() {
    return _lastReading;
}

bool MPU6050Sensor::isHealthy() {
    if (!_initialized) return false;
    MPU6050Reading r = read();
    return r.valid;
}

float MPU6050Sensor::computeTilt(float ax, float ay, float az) {
    // Calculate tilt angle from vertical using accelerometer data
    // When device is level: ax≈0, ay≈0, az≈9.81
    // Tilt angle = arccos(az / |a|) in degrees
    
    float magnitude = sqrtf(ax * ax + ay * ay + az * az);
    
    if (magnitude < 0.1f) return 0.0f;  // Guard against division by zero
    
    // Angle from vertical (Z-axis)
    float cosAngle = az / magnitude;
    
    // Clamp to valid range for acos
    if (cosAngle > 1.0f) cosAngle = 1.0f;
    if (cosAngle < -1.0f) cosAngle = -1.0f;
    
    float angleRad = acosf(cosAngle);
    float angleDeg = angleRad * 180.0f / PI;
    
    return angleDeg;
}

float MPU6050Sensor::computeVibration(float ax, float ay, float az) {
    // Vibration = deviation from static gravity (9.81 m/s²)
    // |a| - g  gives excess acceleration from movement/vibration
    
    float magnitude = sqrtf(ax * ax + ay * ay + az * az);
    float vibration = fabsf(magnitude - 9.81f);
    
    return vibration;
}
