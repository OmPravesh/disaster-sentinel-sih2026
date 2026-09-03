"""
Disaster Sentinel — Risk Predictor & Severity Calculator

Combines 3-layer validation, temporal trends, and multi-node
analysis into a final risk assessment with:
  - Hazard type
  - Probability
  - Severity level (LOW/MEDIUM/HIGH/CRITICAL)
  - Estimated time to critical escalation (ETA)
  - Risk color (GREEN/YELLOW/ORANGE/RED)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Risk levels
RISK_GREEN = "GREEN"
RISK_YELLOW = "YELLOW"
RISK_ORANGE = "ORANGE"
RISK_RED = "RED"

# Severity levels
SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"


class RiskPredictor:
    """
    AI-based risk prediction engine.
    
    For MVP: uses a rule-based decision tree combining:
      - 3-layer confirmation level
      - Combined anomaly score
      - Rate of change
      - Duration of sustained anomaly
      - Trend analysis
    
    Can be upgraded to ML model (XGBoost/LSTM) with training data.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        # Track sustained anomaly durations per node
        self._anomaly_start: Dict[str, datetime] = {}
        self._last_scores: Dict[str, List[float]] = {}

    def predict(self, packet_data: Dict, validation: Dict,
                history: List[Dict] = None) -> Dict:
        """
        Predict risk level from current data and history.
        
        Args:
            packet_data: Decoded packet as dict
            validation: 3-layer validation result
            history: Recent readings from time-series store
            
        Returns:
            Risk assessment dict with probability, severity, ETA, color
        """
        node_id = packet_data.get("node_id", "")
        hazard_name = packet_data.get("hazard_name", "")
        combined = packet_data.get("combined_score", 0)
        rate_flag = packet_data.get("rate_flag", 0)
        confirmation = validation.get("confirmation_level", "NONE")
        layers_anomalous = validation.get("layers_anomalous", 0)

        # --- Temporal analysis ---
        trend = self._analyze_trend(node_id, combined, history)
        sustained_minutes = self._get_sustained_minutes(node_id, combined)

        # --- Compute probability ---
        # Base probability from 3-layer score
        probability = combined

        # Boost from sustained anomaly
        if sustained_minutes > 5:
            probability = min(1.0, probability + 0.05)
        if sustained_minutes > 10:
            probability = min(1.0, probability + 0.05)

        # Boost from rate of change
        if rate_flag == 3:  # Rapid
            probability = min(1.0, probability + 0.08)
        elif rate_flag in (1, 2):  # Rising or falling
            probability = min(1.0, probability + 0.03)

        # Boost from trend
        if trend.get("accelerating", False):
            probability = min(1.0, probability + 0.05)

        # Penalty if not all layers confirm
        if layers_anomalous < 3:
            probability *= (0.6 + layers_anomalous * 0.15)

        probability = round(min(1.0, max(0.0, probability)), 3)

        # --- Determine severity ---
        severity = self._compute_severity(probability, confirmation, sustained_minutes, rate_flag)

        # --- Determine risk color ---
        risk_level = self._compute_risk_level(probability, confirmation, sustained_minutes)

        # --- Estimate ETA ---
        eta = self._estimate_eta(history, hazard_name, trend)

        result = {
            "node_id": node_id,
            "hazard_name": hazard_name,
            "probability": probability,
            "probability_percent": round(probability * 100, 1),
            "severity": severity,
            "risk_level": risk_level,
            "eta_minutes": eta,
            "confirmation_level": confirmation,
            "layers_anomalous": layers_anomalous,
            "combined_score": combined,
            "sustained_minutes": round(sustained_minutes, 1),
            "trend": trend,
            "timestamp": datetime.now().isoformat(),
        }

        if risk_level in (RISK_ORANGE, RISK_RED):
            logger.warning(
                f"[Risk] {node_id} | {hazard_name} | {risk_level} | "
                f"Prob={probability:.1%} | Severity={severity} | "
                f"ETA={eta}min | Sustained={sustained_minutes:.0f}min"
            )

        return result

    def _analyze_trend(self, node_id: str, current_score: float,
                       history: List[Dict] = None) -> Dict:
        """Analyze trend from recent history."""
        # Track scores for simple moving average
        if node_id not in self._last_scores:
            self._last_scores[node_id] = []

        self._last_scores[node_id].append(current_score)
        # Keep last 30 readings
        if len(self._last_scores[node_id]) > 30:
            self._last_scores[node_id] = self._last_scores[node_id][-30:]

        scores = self._last_scores[node_id]

        if len(scores) < 3:
            return {"direction": "insufficient_data", "accelerating": False, "slope": 0}

        # Simple linear regression for trend
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n

        numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(scores))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        # Check acceleration (is the rate of increase itself increasing?)
        if len(scores) >= 6:
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            accelerating = (second_avg - first_avg) > 0.05
        else:
            accelerating = False

        if slope > 0.01:
            direction = "rising"
        elif slope < -0.01:
            direction = "falling"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "accelerating": accelerating,
            "slope": round(slope, 4),
        }

    def _get_sustained_minutes(self, node_id: str, combined: float) -> float:
        """Track how long a node has been in anomalous state."""
        now = datetime.now()

        if combined >= 0.5:
            if node_id not in self._anomaly_start:
                self._anomaly_start[node_id] = now
            elapsed = (now - self._anomaly_start[node_id]).total_seconds() / 60
            return elapsed
        else:
            # Reset tracker
            if node_id in self._anomaly_start:
                del self._anomaly_start[node_id]
            return 0.0

    def _compute_severity(self, probability: float, confirmation: str,
                          sustained: float, rate_flag: int) -> str:
        """Compute severity level."""
        if probability >= 0.90 and confirmation == "HIGH" and sustained > 5:
            return SEVERITY_CRITICAL
        elif probability >= 0.75 and confirmation in ("HIGH", "MEDIUM"):
            return SEVERITY_HIGH
        elif probability >= 0.50:
            return SEVERITY_MEDIUM
        else:
            return SEVERITY_LOW

    def _compute_risk_level(self, probability: float, confirmation: str,
                            sustained: float) -> str:
        """Compute risk color level."""
        if probability >= 0.75 and confirmation == "HIGH" and sustained >= 3:
            return RISK_RED
        elif probability >= 0.60 and confirmation in ("HIGH", "MEDIUM") and sustained >= 5:
            return RISK_ORANGE
        elif probability >= 0.40:
            return RISK_YELLOW
        else:
            return RISK_GREEN

    def _estimate_eta(self, history: List[Dict], hazard_name: str,
                      trend: Dict) -> Optional[float]:
        """
        Estimate time to critical escalation (minutes).
        
        Uses rate of change to extrapolate when threshold will be reached.
        Returns None if not enough data or not trending toward critical.
        """
        if not history or len(history) < 3:
            return None

        slope = trend.get("slope", 0)
        if slope <= 0:
            return None  # Not trending toward critical

        # Current combined score
        current = history[-1].get("combined_score", 0) if history else 0
        critical_threshold = 0.90

        if current >= critical_threshold:
            return 0  # Already critical

        # Simple linear extrapolation
        remaining = critical_threshold - current
        # Slope is per-reading; approximate readings per minute
        readings_per_minute = 0.5  # ~1 reading per 2 minutes
        slope_per_minute = slope * readings_per_minute

        if slope_per_minute <= 0:
            return None

        eta = remaining / slope_per_minute
        return round(min(eta, 999), 1)  # Cap at 999 minutes
