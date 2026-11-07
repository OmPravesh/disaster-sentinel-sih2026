/**
 * Disaster Sentinel — Water Level Sensor Implementation
 * 
 * Supports JSN-SR04T waterproof ultrasonic sensor and analog water-level sensor.
 * Layer 1 — Primary sensor for flood detection.
 * 
 * JSN-SR04T Specifications:
 *   - Effective Range: 20 cm to 600 cm (0.2m to 6.0m)
 *   - Blind Zone: < 20 cm
 *   - Requires min 20us trigger pulse & >=60ms inter-measurement delay
 *   - Temperature compensation: v = 331.3 + (0.606 * Temp_C) m/s
 */

#include "water_level.h"

// Maximum valid distance for JSN-SR04T (cm)
static const float MAX_DISTANCE_CM = 600.0f;
static const float MIN_DISTANCE_CM = 18.0f; // Blind zone limit

// Ultrasonic timeout (microseconds) — 50ms allows measurements up to ~8.5m round trip
static const unsigned long ULTRASONIC_TIMEOUT_US = 50000;

void WaterLevelSensor::begin(int trigPin, int echoPin, int analogPin, bool useUltrasonic) {
    _trigPin = trigPin;
    _echoPin = echoPin;
    _analogPin = analogPin;
    _useUltrasonic = useUltrasonic;
    _lastReading = 0.0f;
    _rawDistance = 0.0f;
    _lastReadTime = 0;
    _calScale = 1.1039f;
    _calOffset = -4.90f;

    if (_useUltrasonic) {
        pinMode(_trigPin, OUTPUT);
        pinMode(_echoPin, INPUT);
        digitalWrite(_trigPin, LOW);
    }
    
    if (_analogPin >= 0) {
        analogSetAttenuation(ADC_11db);  // Full 0-3.3V range
    }

    Serial.println("[WaterLevel] Initialized JSN-SR04T Driver");
    Serial.printf("  Mode: %s | Max Range: %.0f cm | Timeout: %lu us\n",
                  _useUltrasonic ? "Ultrasonic (JSN-SR04T)" : "Analog",
                  MAX_DISTANCE_CM, ULTRASONIC_TIMEOUT_US);
}

void WaterLevelSensor::setCalibration(float scale, float offsetCm) {
    _calScale = scale;
    _calOffset = offsetCm;
    Serial.printf("[WaterLevel] Calibration set: Calibrated = (Raw * %.4f) + (%.2f cm)\n",
                  _calScale, _calOffset);
}

float WaterLevelSensor::readCm(float ambientTempC) {
    float reading;
    
    if (_useUltrasonic) {
        reading = medianReadings(5, ambientTempC);
    } else {
        reading = readAnalog();
    }
    
    if (reading > 0.0f) {
        _rawDistance = reading;
        // Apply linear calibration: y = scale * x + offset
        float calibrated = (_rawDistance * _calScale) + _calOffset;
        if (calibrated < 0.0f) calibrated = 0.0f;
        if (calibrated > MAX_DISTANCE_CM) calibrated = MAX_DISTANCE_CM;
        reading = calibrated;
    } else {
        // If timed out, retain last valid reading or return 0
        if (_lastReading > 0.0f) {
            reading = _lastReading;
        } else {
            reading = 0.0f;
        }
    }
    
    _lastReading = reading;
    _lastReadTime = millis();
    
    return reading;
}

float WaterLevelSensor::getRawValue() {
    return _rawDistance > 0.0f ? _rawDistance : _lastReading;
}

bool WaterLevelSensor::isHealthy() {
    if (_useUltrasonic) {
        float test = readUltrasonicSingle(25.0f);
        return (test >= MIN_DISTANCE_CM && test <= MAX_DISTANCE_CM);
    } else {
        int raw = analogRead(_analogPin);
        return (raw > 10 && raw < 4080);
    }
}

float WaterLevelSensor::readUltrasonicSingle(float ambientTempC) {
    // Dynamic sound speed calculation based on temperature:
    // v = 331.3 + (0.606 * Temp_C) m/s
    // Convert to cm/us: multiply by (100 cm / 1,000,000 us) = 0.0001
    float soundSpeedCmUs = (331.3f + (0.606f * ambientTempC)) * 0.0001f;

    // Ensure clean LOW state before trigger
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(4);
    
    // Send 20us trigger pulse (required for robust JSN-SR04T transducer excitation)
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(20);
    digitalWrite(_trigPin, LOW);
    
    // Measure echo duration with 50,000us timeout (supports >6m range)
    unsigned long duration = pulseIn(_echoPin, HIGH, ULTRASONIC_TIMEOUT_US);
    
    if (duration == 0) {
        // Timeout — obstacle out of range or no echo received
        return -1.0f;
    }
    
    // Round trip calculation: distance = (duration * speed) / 2
    float distance = (duration * soundSpeedCmUs) / 2.0f;
    
    // Discard false echo in the blind zone (< 18cm)
    if (distance < MIN_DISTANCE_CM || distance > MAX_DISTANCE_CM) {
        return -1.0f;
    }
    
    return distance;
}

float WaterLevelSensor::readAnalog() {
    int raw = analogRead(_analogPin);
    float cm = (raw / 4095.0f) * 300.0f;
    return cm;
}

float WaterLevelSensor::medianReadings(int count, float ambientTempC) {
    float samples[7];
    int valid = 0;
    
    if (count > 7) count = 7;
    if (count < 3) count = 3;

    for (int i = 0; i < count; i++) {
        float r = readUltrasonicSingle(ambientTempC);
        if (r >= MIN_DISTANCE_CM && r <= MAX_DISTANCE_CM) {
            samples[valid++] = r;
        }
        // Essential: JSN-SR04T needs 60ms between pings to let acoustic reflections damp out
        delay(60);
    }
    
    if (valid == 0) {
        if (_analogPin >= 0) {
            return readAnalog();
        }
        return -1.0f;
    }
    
    // Simple sort for median
    for (int i = 0; i < valid - 1; i++) {
        for (int j = i + 1; j < valid; j++) {
            if (samples[i] > samples[j]) {
                float tmp = samples[i];
                samples[i] = samples[j];
                samples[j] = tmp;
            }
        }
    }
    
    // Return median (middle element)
    return samples[valid / 2];
}
