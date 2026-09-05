"""
Disaster Sentinel — False Alarm Rejection Scenario

Tests the system's ability to reject false alarms when only a SINGLE
sensor layer shows anomalous readings.

Scenarios tested:
  1. Water sensor glitch (L1=0.92, L2=0.05, L3=0.04) → Result: LOW confirmation (No SMS, No Alarm)
  2. Flame sensor direct sunlight reflection (L1=0.88, L2=0.04, L3=0.05) → Result: LOW confirmation
  3. MPU6050 vibration from passing truck (L1=0.85, L2=0.10, L3=0.05) → Result: LOW confirmation
"""

import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "jetson"))

from simulation.fake_node import _build_raw_packet, HAZARD_FLOOD, HAZARD_FIRE, HAZARD_LANDSLIDE
from receiver.packet_decoder import decode_packet, format_packet_log
from engine.three_layer_validator import ThreeLayerValidator
from engine.risk_predictor import RiskPredictor

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("scenario_false_alarm")


async def run_false_alarm_test():
    validator = ThreeLayerValidator()
    predictor = RiskPredictor()

    logger.info("==================================================")
    logger.info("  FALSE ALARM REJECTION TEST")
    logger.info("==================================================")

    test_cases = [
        {
            "name": "TEST 1: Water Level Sensor Glitch (L1 High, L2 & L3 Normal)",
            "node_id": "FLD1", "hazard_type": HAZARD_FLOOD, "hazard_name": "FLOOD",
            "l1_raw": 280.0, "l1_anom": 0.95,  # Glitch high reading
            "l2_raw": 0.02,  "l2_anom": 0.05,  # No rain
            "l3_raw": 1013.0,"l3_anom": 0.04,  # Normal pressure
        },
        {
            "name": "TEST 2: Sunlight Reflection on Flame Sensor (L1 High, L2 & L3 Normal)",
            "node_id": "FIR2", "hazard_type": HAZARD_FIRE, "hazard_name": "FIRE",
            "l1_raw": 0.85,  "l1_anom": 0.90,  # IR flare
            "l2_raw": 0.05,  "l2_anom": 0.06,  # Clean air
            "l3_raw": 27.0,  "l3_anom": 0.03,  # Normal temp
        },
        {
            "name": "TEST 3: Passing Truck Vibration on MPU6050 (L1 High, L2 & L3 Normal)",
            "node_id": "SLD2", "hazard_type": HAZARD_LANDSLIDE, "hazard_name": "LANDSLIDE",
            "l1_raw": 12.5,  "l1_anom": 0.88,  # Vibration spike
            "l2_raw": 25.0,  "l2_anom": 0.08,  # Dry soil
            "l3_raw": 1012.0,"l3_anom": 0.04,  # Normal pressure
        },
    ]

    all_passed = True

    for tc in test_cases:
        logger.info(f"\n--- {tc['name']} ---")
        
        combined = 0.50 * tc["l1_anom"] + 0.30 * tc["l2_anom"] + 0.20 * tc["l3_anom"]
        raw = _build_raw_packet(
            tc["node_id"], tc["hazard_type"],
            tc["l1_raw"], tc["l1_anom"],
            tc["l2_raw"], tc["l2_anom"],
            tc["l3_raw"], tc["l3_anom"],
            combined, 0, 90, 9999, priority=False
        )

        pkt = decode_packet(raw)
        val = validator.validate(pkt)
        risk = predictor.predict(pkt.to_dict(), val)

        logger.info(format_packet_log(pkt))
        logger.info(f"  ➜ 3-Layer Confirmation Level: {val['confirmation_level']}")
        logger.info(f"  ➜ Layers Anomalous: {val['layers_anomalous']}/3")
        logger.info(f"  ➜ Predicted Risk Level: {risk['risk_level']}")
        logger.info(f"  ➜ Explanation: {val['explanation']}")

        # Verification: False alarm MUST NOT produce RED risk level or HIGH confirmation
        if val["confirmation_level"] != "HIGH" and risk["risk_level"] != "RED":
            logger.info("  ✅ TEST PASSED: False alarm successfully rejected (No RED alert / No SMS)")
        else:
            logger.error("  ❌ TEST FAILED: False alarm improperly triggered RED alert!")
            all_passed = False

    logger.info("\n==================================================")
    if all_passed:
        logger.info("  ALL FALSE ALARM REJECTION TESTS PASSED ✅")
    else:
        logger.error("  SOME TESTS FAILED ❌")
    logger.info("==================================================")

    return all_passed


if __name__ == "__main__":
    asyncio.run(run_false_alarm_test())
