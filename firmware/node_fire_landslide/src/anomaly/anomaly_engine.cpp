/**
 * Disaster Sentinel — Anomaly Detection Engine Implementation
 * 
 * Z-score based anomaly detection with sigmoid mapping
 * for smooth 0.0-1.0 score transition.
 */

#include "anomaly_engine.h"
#include <math.h>

void AnomalyEngine::begin(BaselineManager* baseline, float zThreshold) {
    _baseline = baseline;
    _zThreshold = zThreshold;

    Serial.println("[AnomalyEngine] Initialized");
    Serial.printf("  Z-score threshold: %.1f\n", _zThreshold);
}

AnomalyResult AnomalyEngine::computeAnomaly(uint8_t channel, float value) {
    AnomalyResult result = {0, 0, 0, 0, 0};

    if (!_baseline->isValid(channel)) {
        // Baseline not yet established — cannot compute anomaly
        return result;
    }

    BaselineStats stats = _baseline->getStats(channel);

    // Guard against zero standard deviation
    if (stats.stdDev < 1e-6f) {
        // All readings were identical during baseline — any deviation is anomalous
        result.zScore = (fabsf(value - stats.mean) > 0.01f) ? 10.0f : 0.0f;
    } else {
        result.zScore = fabsf(value - stats.mean) / stats.stdDev;
    }

    // Map z-score to 0.0-1.0 anomaly score using sigmoid
    result.valueAnomaly = sigmoidMap(result.zScore, _zThreshold);
    result.combinedAnomaly = result.valueAnomaly;

    return result;
}

AnomalyResult AnomalyEngine::computeAnomalyWithRate(uint8_t channel, float value, float rate) {
    // First compute value anomaly
    AnomalyResult result = computeAnomaly(channel, value);

    if (!_baseline->isValid(channel)) {
        return result;
    }

    BaselineStats stats = _baseline->getStats(channel);

    // Compute rate-of-change anomaly
    if (stats.rateStdDev < 1e-6f) {
        result.rateZScore = (fabsf(rate - stats.rateMean) > 0.001f) ? 10.0f : 0.0f;
    } else {
        result.rateZScore = fabsf(rate - stats.rateMean) / stats.rateStdDev;
    }

    result.rateAnomaly = sigmoidMap(result.rateZScore, _zThreshold);

    // Combined anomaly = max of value and rate anomalies
    // This catches both "value is abnormal" AND "rate of change is abnormal"
    result.combinedAnomaly = max(result.valueAnomaly, result.rateAnomaly);

    return result;
}

void AnomalyEngine::setZThreshold(float threshold) {
    _zThreshold = threshold;
}

float AnomalyEngine::sigmoidMap(float zScore, float threshold) {
    // Modified sigmoid that maps:
    // z-score = 0         → anomaly ≈ 0.0
    // z-score = threshold → anomaly ≈ 0.5
    // z-score = 2*threshold → anomaly ≈ 0.95
    // z-score >> threshold → anomaly → 1.0
    //
    // Formula: 1 / (1 + exp(-k * (z - threshold)))
    // Where k controls steepness (k=2.0 gives reasonable transition)

    float k = 2.0f;
    float exponent = -k * (zScore - threshold);

    // Prevent overflow
    if (exponent > 20.0f) return 0.0f;
    if (exponent < -20.0f) return 1.0f;

    return 1.0f / (1.0f + expf(exponent));
}
