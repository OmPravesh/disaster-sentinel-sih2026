/**
 * Disaster Sentinel — Water Level Sensor Implementation
 * 
 * Supports JSN-SR04T ultrasonic sensor and analog water-level sensor.
 * Layer 1 — Primary sensor for flood detection.
 */

#include "water_level.h"

// Speed of sound in cm/us (at ~25°C)
static const float SOUND_SPEED_CM_US = 0.0343f;

// Maximum valid distance for ultrasonic (cm)
static const float MAX_DISTANCE_CM = 400.0f;

// Ultrasonic timeout (microseconds) — ~23ms for 4m round trip
static const unsigned long ULTRASONIC_TIMEOUT_US = 23200;

void WaterLevelSensor::begin(int trigPin, int echoPin, int analogPin, bool useUltrasonic) {
    _trigPin = trigPin;
    _echoPin = echoPin;
    _analogPin = analogPin;
    _useUltrasonic = useUltrasonic;
    _lastReading = 0.0f;
    _lastReadTime = 0;

    if (_useUltrasonic) {
        pinMode(_trigPin, OUTPUT);
        pinMode(_echoPin, INPUT);
        digitalWrite(_trigPin, LOW);
    }
    
    if (_analogPin >= 0) {
        // Analog pins on ESP32 don't need explicit pinMode for ADC
        analogSetAttenuation(ADC_11db);  // Full 0-3.3V range
    }

    Serial.println("[WaterLevel] Initialized");
    Serial.printf("  Mode: %s\n", _useUltrasonic ? "Ultrasonic" : "Analog");
}

float WaterLevelSensor::readCm() {
    float reading;
    
    if (_useUltrasonic) {
        reading = averageReadings(5);
    } else {
        reading = readAnalog();
    }
    
    // Sanity check
    if (reading < 0.0f) reading = 0.0f;
    if (reading > MAX_DISTANCE_CM) reading = MAX_DISTANCE_CM;
    
    _lastReading = reading;
    _lastReadTime = millis();
    
    return reading;
}

float WaterLevelSensor::getRawValue() {
    return _lastReading;
}

bool WaterLevelSensor::isHealthy() {
    if (_useUltrasonic) {
        // Try a reading — if timeout, sensor might be disconnected
        float test = readUltrasonic();
        return (test > 0.0f && test < MAX_DISTANCE_CM);
    } else {
        int raw = analogRead(_analogPin);
        return (raw > 10 && raw < 4080);  // Not stuck at 0 or max
    }
}

float WaterLevelSensor::readUltrasonic() {
    // Send trigger pulse
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);
    
    // Measure echo duration
    unsigned long duration = pulseIn(_echoPin, HIGH, ULTRASONIC_TIMEOUT_US);
    
    if (duration == 0) {
        // Timeout — no echo received
        return -1.0f;
    }
    
    // Calculate distance in cm (round trip, so divide by 2)
    float distance = (duration * SOUND_SPEED_CM_US) / 2.0f;
    
    return distance;
}

float WaterLevelSensor::readAnalog() {
    // Read ADC (12-bit, 0-4095)
    int raw = analogRead(_analogPin);
    
    // Convert to cm — this mapping depends on the specific sensor
    // For a typical analog water-level sensor:
    // 0 = no water, 4095 = max water level
    // Scale to 0-300 cm range (adjustable based on sensor spec)
    float cm = (raw / 4095.0f) * 300.0f;
    
    return cm;
}

float WaterLevelSensor::averageReadings(int count) {
    float sum = 0.0f;
    int valid = 0;
    
    for (int i = 0; i < count; i++) {
        float reading = readUltrasonic();
        if (reading > 0.0f && reading < MAX_DISTANCE_CM) {
            sum += reading;
            valid++;
        }
        delay(30);  // Small delay between readings
    }
    
    if (valid == 0) {
        // All readings failed — try analog fallback if available
        if (_analogPin >= 0) {
            return readAnalog();
        }
        return -1.0f;
    }
    
    return sum / valid;
}
