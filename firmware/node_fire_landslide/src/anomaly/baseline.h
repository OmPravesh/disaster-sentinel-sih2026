/**
 * Disaster Sentinel — Baseline Manager
 * 
 * Collects and stores environmental baseline statistics during the
 * initial 48-78 hour calibration period. Baselines are stored in
 * ESP32 NVS (non-volatile storage) and persist across reboots.
 * 
 * For each sensor, stores: mean, std_dev, min, max, sample_count
 * Also stores rate-of-change statistics for temporal anomaly detection.
 */

#ifndef BASELINE_H
#define BASELINE_H

#include <Arduino.h>
#include <Preferences.h>

// Maximum number of sensor channels to track
#define MAX_CHANNELS 6

// Baseline statistics for a single sensor channel
struct BaselineStats {
    float mean;
    float variance;       // Running variance (Welford's algorithm)
    float stdDev;
    float minVal;
    float maxVal;
    float rateMean;       // Mean rate of change
    float rateVariance;   // Variance of rate of change
    float rateStdDev;
    uint32_t sampleCount;
    bool valid;           // Enough samples collected?
};

class BaselineManager {
public:
    /**
     * Initialize baseline manager.
     * @param nvs_namespace  NVS namespace for persistent storage
     * @param minSamples     Minimum samples before baseline is considered valid
     */
    void begin(const char* nvs_namespace = "baseline", uint32_t minSamples = 100);

    /**
     * Add a new reading for a sensor channel.
     * Uses Welford's online algorithm for running mean/variance.
     * @param channel  Sensor channel index (0-based)
     * @param value    Sensor reading
     */
    void addReading(uint8_t channel, float value);

    /**
     * Get baseline statistics for a channel.
     */
    BaselineStats getStats(uint8_t channel);

    /**
     * Check if baseline is valid (enough samples collected).
     */
    bool isValid(uint8_t channel);

    /**
     * Check if all channels have valid baselines.
     */
    bool allValid();

    /**
     * Save baselines to NVS (call periodically).
     */
    void save();

    /**
     * Load baselines from NVS (call on startup).
     * @return true if valid baselines were loaded
     */
    bool load();

    /**
     * Reset baseline for a channel (e.g., after sensor replacement).
     */
    void reset(uint8_t channel);

    /**
     * Reset all baselines.
     */
    void resetAll();

    /**
     * Get hours of data collected.
     */
    float getHoursCollected();

    /**
     * Check if baseline collection period is complete.
     * @param requiredHours  Required hours (default: 48)
     */
    bool isCollectionComplete(float requiredHours = 48.0f);

    /**
     * Set the number of active channels.
     */
    void setChannelCount(uint8_t count);

private:
    Preferences _prefs;
    BaselineStats _stats[MAX_CHANNELS];
    float _prevValues[MAX_CHANNELS];
    unsigned long _prevTimes[MAX_CHANNELS];
    bool _hasPrevValue[MAX_CHANNELS];
    uint8_t _channelCount;
    uint32_t _minSamples;
    unsigned long _startTime;
    const char* _namespace;

    void updateRateStats(uint8_t channel, float rate);
};

#endif // BASELINE_H
