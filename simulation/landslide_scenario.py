"""
Disaster Sentinel — Landslide Event Simulation Scenario

Simulates slope instability leading to a landslide:
  Phase 1: Normal ground stability
  Phase 2: Heavy rainfall causes soil saturation (Layer 2 anomalous)
  Phase 3: Ground movement/tilt detected + soil saturation + storm pressure (RED alert — 3-layer confirmed)
"""

import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "jetson"))

from simulation.fake_node import _build_raw_packet, HAZARD_LANDSLIDE
from receiver.packet_decoder import decode_packet, format_packet_log

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("scenario_landslide")


async def run_landslide_scenario(on_packet_cb=None):
    logger.info("==================================================")
    logger.info("  STARTING LANDSLIDE EVENT SIMULATION SCENARIO")
    logger.info("==================================================")

    seq = 3000
    
    timeline = [
        (5, 1.2, 32.0, 1012.0, 0.03, 0.04, 0.02, 0, "NORMAL: Slope stable, tilt 1.2°"),
        (5, 1.5, 68.0, 1008.0, 0.08, 0.58, 0.22, 1, "RAIN SATURATION: Soil moisture 68%, high slide vulnerability"),
        (5, 6.8, 88.0, 1004.0, 0.65, 0.82, 0.55, 3, "ORANGE ALERT: Slope movement 6.8°, soil saturated 88%"),
        (5, 18.5, 95.0, 999.0, 0.94, 0.92, 0.81, 3, "RED ALERT: LANDSLIDE IN PROGRESS! Tilt 18.5°, 3-layer CONFIRMED"),
        (5, 2.0, 50.0, 1010.0, 0.05, 0.15, 0.10, 0, "STABILIZED: Post-slide ground stabilization"),
    ]

    for step in timeline:
        duration, tilt, soil, pressure, l1_a, l2_a, l3_a, rate, desc = step
        logger.info(f"\n▶ SCENARIO STEP: {desc}")
        
        combined = 0.50 * l1_a + 0.30 * l2_a + 0.20 * l3_a
        is_priority = combined > 0.70

        raw_packet = _build_raw_packet(
            "SLD2", HAZARD_LANDSLIDE,
            tilt, l1_a,
            soil, l2_a,
            pressure, l3_a,
            combined,
            rate,
            85,
            seq,
            priority=is_priority
        )

        pkt = decode_packet(raw_packet, rssi=-48)
        logger.info(format_packet_log(pkt))

        if on_packet_cb:
            if asyncio.iscoroutinefunction(on_packet_cb):
                await on_packet_cb(pkt)
            else:
                on_packet_cb(pkt)

        seq += 1
        await asyncio.sleep(duration)

    logger.info("==================================================")
    logger.info("  LANDSLIDE SCENARIO COMPLETED")
    logger.info("==================================================")


if __name__ == "__main__":
    asyncio.run(run_landslide_scenario())
