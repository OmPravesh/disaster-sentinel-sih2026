"""
Disaster Sentinel — Three-Layer Validator (Jetson)

Second-pass validation of 3-layer sensor confirmation.
This is the KEY mechanism that judges will evaluate.

Validates that a calamity is real by requiring all sensor
layers to independently show anomalous behavior.

Supports both 3-layer nodes (Flood, Landslide, Fire) and
2-layer nodes (Pollution — MQ-135 + PM2.5, no BME280).
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
    Validates multi-layer sensor confirmation for calamity detection.
    
    Supports:
      - 3-layer nodes (FLD1, SLD2, FIR3):
          HIGH:   All 3 layers anomalous (>0.5) AND combined >= 0.75
          MEDIUM: 2+ layers anomalous AND combined >= 0.60
          LOW:    1+ layers anomalous AND combined >= 0.40
          NONE:   No significant anomaly

      - 2-layer nodes (POL4):
          HIGH:   Both layers anomalous (>0.5) AND combined >= 0.75
          MEDIUM: 1 layer anomalous AND combined >= 0.55
          LOW:    1 layer anomalous AND combined >= 0.35
          NONE:   No significant anomaly
    """

    def __init__(self, config: dict = None, node_configs: dict = None):
        self.config = config or {}
        self.node_configs = node_configs or {}
        self.layer_threshold = 0.5  # Score above which a layer is "anomalous"

        # Load 3-layer thresholds
        three_layer = self.config.get("three_layer_thresholds", {})
        self.three_layer_thresholds = {
            "high_min_layers": three_layer.get("high_min_layers", 3),
            "high_min_combined": three_layer.get("high_min_combined", 0.75),
            "medium_min_layers": three_layer.get("medium_min_layers", 2),
            "medium_min_combined": three_layer.get("medium_min_combined", 0.60),
            "low_min_layers": three_layer.get("low_min_layers", 1),
            "low_min_combined": three_layer.get("low_min_combined", 0.40),
        }

        # Load 2-layer thresholds
        two_layer = self.config.get("two_layer_thresholds", {})
        self.two_layer_thresholds = {
            "high_min_layers": two_layer.get("high_min_layers", 2),
            "high_min_combined": two_layer.get("high_min_combined", 0.75),
            "medium_min_layers": two_layer.get("medium_min_layers", 1),
            "medium_min_combined": two_layer.get("medium_min_combined", 0.55),
            "low_min_layers": two_layer.get("low_min_layers", 1),
            "low_min_combined": two_layer.get("low_min_combined", 0.35),
        }

    def _get_layer_count(self, node_id: str) -> int:
        """Get the number of sensor layers for a node."""
        node_cfg = self.node_configs.get(node_id, {})
        return node_cfg.get("layer_count", 3)

    def _get_thresholds(self, layer_count: int) -> dict:
        """Get the appropriate thresholds based on layer count."""
        if layer_count <= 2:
            return self.two_layer_thresholds
        return self.three_layer_thresholds

    def validate(self, packet: DecodedPacket) -> Dict:
        """
        Validate the multi-layer confirmation from a decoded packet.
        
        Automatically detects whether this is a 2-layer or 3-layer node
        and applies the appropriate validation thresholds.
        
        Returns dict with:
          - confirmation_level: NONE/LOW/MEDIUM/HIGH
          - layers_anomalous: count of layers above threshold
          - layer_count: total layers for this node (2 or 3)
          - layer_details: per-layer breakdown
          - explanation: human-readable explanation
        """
        layer_count = self._get_layer_count(packet.node_id)
        thresholds = self._get_thresholds(layer_count)

        # Build layer map based on layer count
        if layer_count >= 3:
            layers = {
                "L1 (Primary)": packet.l1_anomaly,
                "L2 (Corroborating)": packet.l2_anomaly,
                "L3 (Context)": packet.l3_anomaly,
            }
        else:
            # 2-layer mode: ignore L3
            layers = {
                "L1 (Primary)": packet.l1_anomaly,
                "L2 (Corroborating)": packet.l2_anomaly,
            }

        anomalous = {name: score for name, score in layers.items()
                     if score > self.layer_threshold}
        layers_count = len(anomalous)
        combined = packet.combined_score

        # Determine confirmation level
        if layers_count >= thresholds["high_min_layers"] and combined >= thresholds["high_min_combined"]:
            level = CONFIRM_HIGH
            if layer_count >= 3:
                explanation = (
                    f"✅ ALL 3 LAYERS CONFIRMED — {packet.hazard_name} is very likely real. "
                    f"Combined score {combined:.2f} exceeds threshold {thresholds['high_min_combined']}."
                )
            else:
                explanation = (
                    f"✅ BOTH LAYERS CONFIRMED — {packet.hazard_name} is very likely real. "
                    f"Combined score {combined:.2f} exceeds threshold {thresholds['high_min_combined']}."
                )
        elif layers_count >= thresholds["medium_min_layers"] and combined >= thresholds["medium_min_combined"]:
            level = CONFIRM_MEDIUM
            non_anomalous = [n for n, s in layers.items() if s <= self.layer_threshold]
            if layer_count >= 3:
                explanation = (
                    f"⚠️ {layers_count}/3 LAYERS CONFIRM — {packet.hazard_name} possible. "
                    f"Layer(s) not confirming: {', '.join(non_anomalous) if non_anomalous else 'none'}. "
                    f"Monitoring closely."
                )
            else:
                explanation = (
                    f"⚠️ 1/2 LAYERS CONFIRM — {packet.hazard_name} possible. "
                    f"Layer not confirming: {', '.join(non_anomalous) if non_anomalous else 'none'}. "
                    f"Monitoring closely."
                )
        elif layers_count >= thresholds["low_min_layers"] and combined >= thresholds["low_min_combined"]:
            level = CONFIRM_LOW
            anomalous_names = list(anomalous.keys())
            explanation = (
                f"⚡ LOW CONFIDENCE — Likely NOT a real {packet.hazard_name}. "
                f"Only: {', '.join(anomalous_names)}. "
                f"Possible causes: sensor malfunction, local disturbance, temporary variation."
            )
        else:
            level = CONFIRM_NONE
            explanation = f"🟢 All layers normal for {packet.hazard_name}."

        # Build layer details
        layer_details = {
            "l1_anomaly": packet.l1_anomaly,
            "l1_status": "🔴 ANOMALOUS" if packet.l1_anomaly > self.layer_threshold else "🟢 Normal",
            "l2_anomaly": packet.l2_anomaly,
            "l2_status": "🔴 ANOMALOUS" if packet.l2_anomaly > self.layer_threshold else "🟢 Normal",
        }

        if layer_count >= 3:
            layer_details["l3_anomaly"] = packet.l3_anomaly
            layer_details["l3_status"] = "🔴 ANOMALOUS" if packet.l3_anomaly > self.layer_threshold else "🟢 Normal"
        else:
            layer_details["l3_anomaly"] = 0.0
            layer_details["l3_status"] = "⬛ Not Used (2-Layer Node)"

        result = {
            "confirmation_level": level,
            "layers_anomalous": layers_count,
            "layer_count": layer_count,
            "layer_details": layer_details,
            "combined_score": combined,
            "explanation": explanation,
        }

        if level in (CONFIRM_HIGH, CONFIRM_MEDIUM):
            logger.warning(f"[Validator] {packet.node_id}: {explanation}")
        elif level == CONFIRM_LOW:
            logger.info(f"[Validator] {packet.node_id}: {explanation}")

        return result
