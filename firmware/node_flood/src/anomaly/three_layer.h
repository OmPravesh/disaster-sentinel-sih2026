/**
 * Disaster Sentinel — Three-Layer Confidence Combiner
 * 
 * Combines anomaly scores from three sensor layers into a
 * single confidence score for calamity confirmation.
 * 
 * Layer 1 (Primary)       — weight 0.50
 * Layer 2 (Corroborating) — weight 0.30
 * Layer 3 (Context)       — weight 0.20
 * 
 * Also determines how many layers are in agreement (consensus).
 */

#ifndef THREE_LAYER_H
#define THREE_LAYER_H

#include <Arduino.h>
#include "anomaly_engine.h"

// Confirmation levels
enum ConfirmationLevel {
    CONFIRM_NONE   = 0,  // No anomaly detected
    CONFIRM_LOW    = 1,  // 1 layer anomalous — likely false alarm
    CONFIRM_MEDIUM = 2,  // 2 layers anomalous — possible calamity
    CONFIRM_HIGH   = 3   // 3 layers anomalous — confirmed calamity
};

// Three-layer analysis result
struct ThreeLayerResult {
    // Per-layer anomaly scores (0.0 - 1.0)
    float layer1Score;
    float layer2Score;
    float layer3Score;
    
    // Combined weighted score
    float combinedScore;
    
    // How many layers show anomaly (threshold > 0.5)
    uint8_t layersAnomalous;
    
    // Confirmation level
    ConfirmationLevel confirmation;
    
    // Rate flag: 0=stable, 1=rising, 2=falling, 3=rapid
    uint8_t rateFlag;
};

class ThreeLayerCombiner {
public:
    /**
     * Initialize with layer weights.
     * @param w1  Layer 1 weight (default: 0.50)
     * @param w2  Layer 2 weight (default: 0.30)
     * @param w3  Layer 3 weight (default: 0.20)
     */
    void begin(float w1 = 0.50f, float w2 = 0.30f, float w3 = 0.20f);

    /**
     * Compute three-layer confidence from individual anomaly results.
     * @param l1  Layer 1 anomaly result (primary sensor)
     * @param l2  Layer 2 anomaly result (corroborating sensor)
     * @param l3  Layer 3 anomaly result (context sensor)
     * @param primaryRate  Rate of change of primary sensor (for rate flag)
     * @return ThreeLayerResult with combined analysis
     */
    ThreeLayerResult compute(
        const AnomalyResult& l1,
        const AnomalyResult& l2,
        const AnomalyResult& l3,
        float primaryRate = 0.0f
    );

    /**
     * Set the threshold for a layer to be considered "anomalous".
     * Default: 0.5
     */
    void setLayerThreshold(float threshold);

private:
    float _w1, _w2, _w3;
    float _layerThreshold;

    uint8_t computeRateFlag(float rate);
    ConfirmationLevel computeConfirmation(uint8_t layersAnomalous, float combined);
};

#endif // THREE_LAYER_H
