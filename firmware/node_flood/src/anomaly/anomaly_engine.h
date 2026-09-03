/**
 * Disaster Sentinel — Anomaly Detection Engine
 * 
 * Computes per-sensor anomaly scores using z-score deviation
 * from the established baseline. Supports both value-based
 * and rate-of-change-based anomaly detection.
 * 
 * Output: anomaly_score ∈ [0.0, 1.0] for each sensor channel.
 */

#ifndef ANOMALY_ENGINE_H
#define ANOMALY_ENGINE_H

#include <Arduino.h>
#include "baseline.h"

// Anomaly result for a single sensor channel
struct AnomalyResult {
    float valueAnomaly;     // Anomaly score based on absolute value deviation
    float rateAnomaly;      // Anomaly score based on rate-of-change deviation
    float combinedAnomaly;  // max(valueAnomaly, rateAnomaly)
    float zScore;           // Raw z-score for debugging
    float rateZScore;       // Raw rate z-score
};

class AnomalyEngine {
public:
    /**
     * Initialize with reference to baseline manager.
     * @param baseline  Pointer to the baseline manager
     * @param zThreshold  Z-score threshold for anomaly mapping (default: 2.0)
     */
    void begin(BaselineManager* baseline, float zThreshold = 2.0f);

    /**
     * Compute anomaly score for a sensor channel.
     * @param channel  Sensor channel index
     * @param value    Current sensor reading
     * @return AnomalyResult with per-metric scores
     */
    AnomalyResult computeAnomaly(uint8_t channel, float value);

    /**
     * Compute anomaly with rate-of-change analysis.
     * @param channel  Sensor channel index
     * @param value    Current sensor reading
     * @param rate     Current rate of change (units/second)
     * @return AnomalyResult with both value and rate anomaly scores
     */
    AnomalyResult computeAnomalyWithRate(uint8_t channel, float value, float rate);

    /**
     * Set the z-score threshold.
     */
    void setZThreshold(float threshold);

private:
    BaselineManager* _baseline;
    float _zThreshold;

    /**
     * Sigmoid mapping: z-score → [0.0, 1.0] anomaly score.
     * Maps values around the threshold to a smooth 0-1 transition.
     */
    float sigmoidMap(float zScore, float threshold);
};

#endif // ANOMALY_ENGINE_H
