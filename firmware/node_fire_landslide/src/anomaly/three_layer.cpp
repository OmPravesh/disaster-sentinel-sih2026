/**
 * Disaster Sentinel — Three-Layer Confidence Combiner Implementation
 */

#include "three_layer.h"

void ThreeLayerCombiner::begin(float w1, float w2, float w3) {
    _w1 = w1;
    _w2 = w2;
    _w3 = w3;
    _layerThreshold = 0.5f;

    Serial.println("[ThreeLayer] Initialized");
    Serial.printf("  Weights: L1=%.2f, L2=%.2f, L3=%.2f\n", _w1, _w2, _w3);
}

ThreeLayerResult ThreeLayerCombiner::compute(
    const AnomalyResult& l1,
    const AnomalyResult& l2,
    const AnomalyResult& l3,
    float primaryRate
) {
    ThreeLayerResult result;

    // Store individual scores
    result.layer1Score = l1.combinedAnomaly;
    result.layer2Score = l2.combinedAnomaly;
    result.layer3Score = l3.combinedAnomaly;

    // Weighted combination
    result.combinedScore = (_w1 * result.layer1Score) +
                           (_w2 * result.layer2Score) +
                           (_w3 * result.layer3Score);

    // Clamp to [0.0, 1.0]
    if (result.combinedScore > 1.0f) result.combinedScore = 1.0f;
    if (result.combinedScore < 0.0f) result.combinedScore = 0.0f;

    // Count anomalous layers
    result.layersAnomalous = 0;
    if (result.layer1Score > _layerThreshold) result.layersAnomalous++;
    if (result.layer2Score > _layerThreshold) result.layersAnomalous++;
    if (result.layer3Score > _layerThreshold) result.layersAnomalous++;

    // Determine confirmation level
    result.confirmation = computeConfirmation(result.layersAnomalous, result.combinedScore);

    // Rate flag
    result.rateFlag = computeRateFlag(primaryRate);

    return result;
}

void ThreeLayerCombiner::setLayerThreshold(float threshold) {
    _layerThreshold = threshold;
}

ConfirmationLevel ThreeLayerCombiner::computeConfirmation(uint8_t layersAnomalous, float combined) {
    // All 3 layers agree + high combined score = confirmed calamity
    if (layersAnomalous >= 3 && combined >= 0.75f) {
        return CONFIRM_HIGH;
    }
    // 2 layers agree + moderate combined score = possible calamity
    if (layersAnomalous >= 2 && combined >= 0.60f) {
        return CONFIRM_MEDIUM;
    }
    // 1 layer anomalous = suspicious but likely not a calamity
    if (layersAnomalous >= 1 && combined >= 0.40f) {
        return CONFIRM_LOW;
    }
    // Nothing anomalous
    return CONFIRM_NONE;
}

uint8_t ThreeLayerCombiner::computeRateFlag(float rate) {
    // Rate flags for the primary sensor's rate of change:
    // 0 = stable (small change)
    // 1 = rising (moderate positive change)
    // 2 = falling (moderate negative change)
    // 3 = rapid (large change in either direction)

    float absRate = fabsf(rate);

    if (absRate > 5.0f) {       // Rapid change (>5 units/minute)
        return 3;
    } else if (rate > 1.0f) {   // Rising
        return 1;
    } else if (rate < -1.0f) {  // Falling
        return 2;
    } else {
        return 0;               // Stable
    }
}
