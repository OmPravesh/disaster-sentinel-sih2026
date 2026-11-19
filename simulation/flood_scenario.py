"""
Disaster Sentinel — Flood Event Simulation Scenario

Simulates a realistic flood progression over time:
  Phase 1 (0-30s): Normal baseline readings
  Phase 2 (30-90s): Water level rising, rain intensity increasing (Elevated - YELLOW/ORANGE)
  Phase 3 (90-180s): Rapid water surge, heavy rain, pressure drop (Critical - RED alert, 3-layer confirmed)
  Phase 4 (180s+): Receding water levels (Recovery back to GREEN)
"""

import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "jetson"))

from simulation.fake_node import _build_raw_packet, HAZARD_FLOOD
from receiver.packet_decoder import decode_packet, format_packet_log

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("scenario_flood")


async def run_flood_scenario(on_packet_cb=None):
    logger.info("==================================================")
    logger.info("  STARTING FLOOD EVENT SIMULATION SCENARIO")
    logger.info("==================================================")

    seq = 1000
    
    # Timeline steps: (duration_sec, distance_cm sensor->water (lower = higher water; critical < 300), rain_intensity_0_1, pressure_hPa, l1_anom, l2_anom, l3_anom, rate_flag, desc)
    timeline = [
        # Normal
        (5, 510.0, 0.05, 1013.0, 0.05, 0.03, 0.02, 0, "NORMAL: Calm environmental conditions"),
        (5, 505.0, 0.10, 1012.5, 0.08, 0.05, 0.04, 0, "NORMAL: Slight rain starting"),
        # Rising / Elevated
        (5, 440.0, 0.35, 1010.0, 0.42, 0.38, 0.25, 1, "ELEVATED: Water 440cm below sensor, moderate rain"),
        (5, 370.0, 0.55, 1007.0, 0.61, 0.58, 0.45, 1, "ORANGE ALERT: Water 370cm below sensor, 2 layers anomalous"),
        # Surge / Critical RED
        (5, 240.0, 0.85, 1002.0, 0.88, 0.82, 0.76, 3, "RED ALERT: SURGE! Water 240cm below sensor, heavy rain, storm pressure (3-layer CONFIRMED)"),
        (5, 140.0, 0.95, 999.0, 0.96, 0.91, 0.88, 3, "CRITICAL RED: Water 140cm below sensor, sustained flood conditions"),
        # Receding
        (5, 320.0, 0.40, 1006.0, 0.65, 0.45, 0.35, 2, "RECOVERY: Water receding, 320cm below sensor"),
        (5, 490.0, 0.10, 1011.0, 0.15, 0.10, 0.08, 2, "NORMALIZED: Water level back to near baseline"),
    ]

    for step in timeline:
        duration, water, rain, pressure, l1_a, l2_a, l3_a, rate, desc = step
        logger.info(f"\n▶ SCENARIO STEP: {desc}")
        
        combined = 0.50 * l1_a + 0.30 * l2_a + 0.20 * l3_a
        is_priority = combined > 0.70

        raw_packet = _build_raw_packet(
            "FLD1", HAZARD_FLOOD,
            water, l1_a,
            rain, l2_a,
            pressure, l3_a,
            combined,
            rate,
            90,
            seq,
            priority=is_priority
        )

        pkt = decode_packet(raw_packet, rssi=-45)
        logger.info(format_packet_log(pkt))

        if on_packet_cb:
            if asyncio.iscoroutinefunction(on_packet_cb):
                await on_packet_cb(pkt)
            else:
                on_packet_cb(pkt)

        seq += 1
        await asyncio.sleep(duration)

    logger.info("==================================================")
    logger.info("  FLOOD SCENARIO COMPLETED")
    logger.info("==================================================")


if __name__ == "__main__":
    asyncio.run(run_flood_scenario())
