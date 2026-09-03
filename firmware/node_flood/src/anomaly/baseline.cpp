/**
 * Disaster Sentinel — Baseline Manager Implementation
 * 
 * Uses Welford's online algorithm for numerically stable running
 * mean and variance computation. Stores results in ESP32 NVS.
 */

#include "baseline.h"

void BaselineManager::begin(const char* nvs_namespace, uint32_t minSamples) {
    _namespace = nvs_namespace;
    _minSamples = minSamples;
    _channelCount = MAX_CHANNELS;
    _startTime = millis();

    // Initialize all channels
    for (int i = 0; i < MAX_CHANNELS; i++) {
        _stats[i] = {0, 0, 0, 1e9f, -1e9f, 0, 0, 0, 0, false};
        _hasPrevValue[i] = false;
        _prevValues[i] = 0;
        _prevTimes[i] = 0;
    }

    Serial.println("[Baseline] Manager initialized");
    Serial.printf("  Min samples: %u\n", _minSamples);
}

void BaselineManager::addReading(uint8_t channel, float value) {
    if (channel >= MAX_CHANNELS) return;
    if (isnan(value) || isinf(value)) return;

    BaselineStats& s = _stats[channel];
    s.sampleCount++;

    // --- Welford's online algorithm ---
    // Numerically stable running mean and variance
    float delta = value - s.mean;
    s.mean += delta / s.sampleCount;
    float delta2 = value - s.mean;
    s.variance += delta * delta2;

    // Standard deviation
    if (s.sampleCount > 1) {
        s.stdDev = sqrtf(s.variance / (s.sampleCount - 1));
    }

    // Min/Max tracking
    if (value < s.minVal) s.minVal = value;
    if (value > s.maxVal) s.maxVal = value;

    // --- Rate of change statistics ---
    unsigned long now = millis();
    if (_hasPrevValue[channel] && (now - _prevTimes[channel]) > 0) {
        float timeDeltaSec = (now - _prevTimes[channel]) / 1000.0f;
        float rate = (value - _prevValues[channel]) / timeDeltaSec;
        updateRateStats(channel, rate);
    }

    _prevValues[channel] = value;
    _prevTimes[channel] = now;
    _hasPrevValue[channel] = true;

    // Mark valid when enough samples collected
    if (s.sampleCount >= _minSamples) {
        s.valid = true;
    }
}

void BaselineManager::updateRateStats(uint8_t channel, float rate) {
    BaselineStats& s = _stats[channel];

    // Use same Welford's algorithm for rate statistics
    // We use sampleCount-1 because rate stats lag by one sample
    uint32_t rateCount = s.sampleCount - 1;
    if (rateCount == 0) return;

    float delta = rate - s.rateMean;
    s.rateMean += delta / rateCount;
    float delta2 = rate - s.rateMean;
    s.rateVariance += delta * delta2;

    if (rateCount > 1) {
        s.rateStdDev = sqrtf(s.rateVariance / (rateCount - 1));
    }
}

BaselineStats BaselineManager::getStats(uint8_t channel) {
    if (channel >= MAX_CHANNELS) {
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, false};
    }
    return _stats[channel];
}

bool BaselineManager::isValid(uint8_t channel) {
    if (channel >= MAX_CHANNELS) return false;
    return _stats[channel].valid;
}

bool BaselineManager::allValid() {
    for (uint8_t i = 0; i < _channelCount; i++) {
        if (!_stats[i].valid) return false;
    }
    return true;
}

void BaselineManager::save() {
    _prefs.begin(_namespace, false);  // Read-write mode

    for (uint8_t i = 0; i < _channelCount; i++) {
        String prefix = "ch" + String(i) + "_";
        BaselineStats& s = _stats[i];

        _prefs.putFloat((prefix + "mean").c_str(), s.mean);
        _prefs.putFloat((prefix + "var").c_str(), s.variance);
        _prefs.putFloat((prefix + "sd").c_str(), s.stdDev);
        _prefs.putFloat((prefix + "min").c_str(), s.minVal);
        _prefs.putFloat((prefix + "max").c_str(), s.maxVal);
        _prefs.putFloat((prefix + "rmn").c_str(), s.rateMean);
        _prefs.putFloat((prefix + "rvr").c_str(), s.rateVariance);
        _prefs.putFloat((prefix + "rsd").c_str(), s.rateStdDev);
        _prefs.putUInt((prefix + "cnt").c_str(), s.sampleCount);
        _prefs.putBool((prefix + "val").c_str(), s.valid);
    }

    _prefs.putULong("startTime", _startTime);
    _prefs.end();

    Serial.println("[Baseline] Saved to NVS");
}

bool BaselineManager::load() {
    _prefs.begin(_namespace, true);  // Read-only mode

    bool anyLoaded = false;

    for (uint8_t i = 0; i < _channelCount; i++) {
        String prefix = "ch" + String(i) + "_";
        BaselineStats& s = _stats[i];

        s.sampleCount = _prefs.getUInt((prefix + "cnt").c_str(), 0);
        if (s.sampleCount > 0) {
            s.mean = _prefs.getFloat((prefix + "mean").c_str(), 0);
            s.variance = _prefs.getFloat((prefix + "var").c_str(), 0);
            s.stdDev = _prefs.getFloat((prefix + "sd").c_str(), 0);
            s.minVal = _prefs.getFloat((prefix + "min").c_str(), 0);
            s.maxVal = _prefs.getFloat((prefix + "max").c_str(), 0);
            s.rateMean = _prefs.getFloat((prefix + "rmn").c_str(), 0);
            s.rateVariance = _prefs.getFloat((prefix + "rvr").c_str(), 0);
            s.rateStdDev = _prefs.getFloat((prefix + "rsd").c_str(), 0);
            s.valid = _prefs.getBool((prefix + "val").c_str(), false);
            anyLoaded = true;
        }
    }

    _startTime = _prefs.getULong("startTime", millis());
    _prefs.end();

    if (anyLoaded) {
        Serial.println("[Baseline] Loaded from NVS");
    } else {
        Serial.println("[Baseline] No saved baselines found — starting fresh");
    }

    return anyLoaded;
}

void BaselineManager::reset(uint8_t channel) {
    if (channel >= MAX_CHANNELS) return;
    _stats[channel] = {0, 0, 0, 1e9f, -1e9f, 0, 0, 0, 0, false};
    _hasPrevValue[channel] = false;
    Serial.printf("[Baseline] Channel %d reset\n", channel);
}

void BaselineManager::resetAll() {
    for (uint8_t i = 0; i < MAX_CHANNELS; i++) {
        reset(i);
    }
    _startTime = millis();
    Serial.println("[Baseline] All channels reset");
}

float BaselineManager::getHoursCollected() {
    return (millis() - _startTime) / 3600000.0f;
}

bool BaselineManager::isCollectionComplete(float requiredHours) {
    return getHoursCollected() >= requiredHours && allValid();
}

void BaselineManager::setChannelCount(uint8_t count) {
    if (count > MAX_CHANNELS) count = MAX_CHANNELS;
    _channelCount = count;
}
