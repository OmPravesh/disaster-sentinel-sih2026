"""
Disaster Sentinel — Three-Layer Validator (Jetson)

Second-pass validation of 3-layer sensor confirmation.
This is the KEY mechanism that judges will evaluate.

Validates that a calamity is real by requiring all 3 sensor 
layers to independently show anomalous behavior.
"""

import logging
from typing import Dict, Optional
from receiver.packet_decoder import DecodedPacket

logger = logging.getLogger(__name__)


# Confirmation levels
CONFIRM_NONE = "NONE"
CONFIRM_LOW = "LOW"
CONFIRM_MEDIUM = "MEDIUM"
CONFIRM_HIGH = "HIGH"


class ThreeLayerValidator:
    """
    Validates 3-layer sensor confirmation for calamity detection.
    
    Rules:
      HIGH:   All 3 layers anomalous (>0.5) AND combined ≥ 0.75
      MEDIUM: 2+ layers anomalous AND combined ≥ 0.60
      LOW:    1+ layers anomalous AND combined ≥ 0.40
      NONE:   No significant anomaly
    """

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.high_min_layers = cfg.get("high_min_layers", 3)
        self.high_min_combined = cfg.get("high_min_combined", 0.75)
        self.medium_min_layers = cfg.get("medium_min_layers", 2)
        self.medium_min_combined = cfg.get("medium_min_combined", 0.60)
        self.low_min_layers = cfg.get("low_min_layers", 1)
        self.low_min_combined = cfg.get("low_min_combined", 0.40)
        self.layer_threshold = 0.5  # Score above which a layer is "anomalous"

    def validate(self, packet: DecodedPacket) -> Dict:
        """
        Validate the 3-layer confirmation from a decoded packet.
        
        Returns dict with:
          - confirmation_level: NONE/LOW/MEDIUM/HIGH
          - layers_anomalous: count of layers above threshold
          - layer_details: per-layer breakdown
          - explanation: human-readable explanation
        """
        # Count anomalous layers
        layers = {
            "L1 (Primary)": packet.l1_anomaly,
            "L2 (Corroborating)": packet.l2_anomaly,
            "L3 (Context)": packet.l3_anomaly,
        }

        anomalous = {name: score for name, score in layers.items() 
                     if score > self.layer_threshold}
        layers_count = len(anomalous)
        combined = packet.combined_score

        # Determine confirmation level
        if layers_count >= self.high_min_layers and combined >= self.high_min_combined:
            level = CONFIRM_HIGH
            explanation = (
                f"✅ ALL 3 LAYERS CONFIRMED — {packet.hazard_name} is very likely real. "
                f"Combined score {combined:.2f} exceeds threshold {self.high_min_combined}."
            )
        elif layers_count >= self.medium_min_layers and combined >= self.medium_min_combined:
            level = CONFIRM_MEDIUM
            non_anomalous = [n for n, s in layers.items() if s <= self.layer_threshold]
            explanation = (
                f"⚠️ 2/3 LAYERS CONFIRM — {packet.hazard_name} possible. "
                f"Layer(s) not confirming: {', '.join(non_anomalous)}. "
                f"Monitoring closely."
            )
        elif layers_count >= self.low_min_layers and combined >= self.low_min_combined:
            level = CONFIRM_LOW
            anomalous_names = [n for n, s in layers.items() if s > self.layer_threshold]
            explanation = (
                f"⚡ 1/3 LAYER ANOMALOUS — Likely NOT a real {packet.hazard_name}. "
                f"Only: {', '.join(anomalous_names)}. "
                f"Possible causes: sensor malfunction, local disturbance, temporary variation."
            )
        else:
            level = CONFIRM_NONE
            explanation = f"🟢 All layers normal for {packet.hazard_name}."

        result = {
            "confirmation_level": level,
            "layers_anomalous": layers_count,
            "layer_details": {
                "l1_anomaly": packet.l1_anomaly,
                "l1_status": "🔴 ANOMALOUS" if packet.l1_anomaly > self.layer_threshold else "🟢 Normal",
                "l2_anomaly": packet.l2_anomaly,
                "l2_status": "🔴 ANOMALOUS" if packet.l2_anomaly > self.layer_threshold else "🟢 Normal",
                "l3_anomaly": packet.l3_anomaly,
                "l3_status": "🔴 ANOMALOUS" if packet.l3_anomaly > self.layer_threshold else "🟢 Normal",
            },
            "combined_score": combined,
            "explanation": explanation,
        }

        if level in (CONFIRM_HIGH, CONFIRM_MEDIUM):
            logger.warning(f"[3-Layer] {packet.node_id}: {explanation}")
        elif level == CONFIRM_LOW:
            logger.info(f"[3-Layer] {packet.node_id}: {explanation}")

        return result
