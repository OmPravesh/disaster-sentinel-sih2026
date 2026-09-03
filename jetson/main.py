"""
═══════════════════════════════════════════════════════════
DISASTER SENTINEL — Main Orchestrator
═══════════════════════════════════════════════════════════

Ties together all subsystems:
  1. LoRa Receiver (or Simulated Receiver for testing)
  2. Packet Decoder
  3. Time-Series Store (SQLite)
  4. Three-Layer Validator
  5. Risk Predictor
  6. Alert Manager
  7. SMS / Buzzer / Strobe
  8. FastAPI Dashboard

Usage:
  # With simulated data (for development):
  python main.py --simulate

  # With real LoRa hardware:
  python main.py

  # Dashboard will be available at http://localhost:8080

SIH 2026 · Problem Statement SIH26178 · Qualcomm
═══════════════════════════════════════════════════════════
"""

import asyncio
import argparse
import logging
import os
import sys
import yaml
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from receiver.packet_decoder import DecodedPacket, format_packet_log
from receiver.lora_receiver import LoRaReceiver, SimulatedReceiver
from data.time_series_store import TimeSeriesStore
from engine.three_layer_validator import ThreeLayerValidator
from engine.risk_predictor import RiskPredictor
from engine.alert_manager import AlertManager
from alerts.sms_sender import SMSSender
from alerts.buzzer_strobe import BuzzerControl, StrobeControl
from dashboard.app import DashboardApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger("sentinel")


def load_config(path: str = "config.yaml") -> dict:
    """Load YAML configuration."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    logger.warning(f"Config not found at {config_path}, using defaults")
    return {}


class DisasterSentinel:
    """Main system orchestrator."""

    def __init__(self, config: dict, simulate: bool = False):
        self.config = config
        self.simulate = simulate

        # Initialize subsystems
        logger.info("═" * 50)
        logger.info("  DISASTER SENTINEL — Initializing")
        logger.info("═" * 50)

        # Data store
        db_path = config.get("database", {}).get("path", "data/disaster_sentinel.db")
        self.store = TimeSeriesStore(db_path)

        # Three-layer validator
        self.validator = ThreeLayerValidator(config.get("three_layer", {}))

        # Risk predictor
        self.risk_predictor = RiskPredictor(config.get("risk_levels", {}))

        # Alert manager
        alert_cfg = config.get("alerts", {})
        self.alert_manager = AlertManager(alert_cfg.get("sms", {}))

        # SMS
        self.sms = SMSSender(alert_cfg.get("sms", {}))

        # Buzzer & Strobe
        buzzer_cfg = alert_cfg.get("buzzer", {})
        strobe_cfg = alert_cfg.get("strobe", {})
        self.buzzer = BuzzerControl(
            pin=buzzer_cfg.get("gpio_pin", 12),
            enabled=buzzer_cfg.get("enabled", True),
        )
        self.strobe = StrobeControl(
            pin=strobe_cfg.get("gpio_pin", 16),
            enabled=strobe_cfg.get("enabled", True),
        )

        # Wire alert manager to output devices
        self.alert_manager.set_sms_sender(self.sms)
        self.alert_manager.set_buzzer(self.buzzer)
        self.alert_manager.set_strobe(self.strobe)

        # LoRa receiver
        if simulate:
            self.receiver = SimulatedReceiver(config.get("lora", {}))
            logger.info("Using SIMULATED receiver (no hardware)")
        else:
            self.receiver = LoRaReceiver(config.get("lora", {}))
            logger.info("Using REAL LoRa receiver")

        # Dashboard
        self.dashboard = DashboardApp(
            self.store,
            self.alert_manager,
            config.get("dashboard", {}),
        )

        # Wire alert manager to dashboard WebSocket
        self.alert_manager.on_alert(self.dashboard.broadcast)

        # Register packet callback
        self.receiver.on_packet(self.process_packet)

    async def process_packet(self, packet: DecodedPacket):
        """
        Main processing pipeline for each received packet.
        
        Flow:
          1. Store in database
          2. Validate 3-layer confirmation
          3. Get historical data for trend analysis
          4. Predict risk
          5. Evaluate alerts
          6. Push to dashboard via WebSocket
        """
        try:
            # 1. Store reading
            await self.store.store_reading(packet)

            # 2. Three-layer validation
            validation = self.validator.validate(packet)

            # 3. Get recent history
            history = await self.store.get_recent_readings(packet.node_id, minutes=30)

            # 4. Risk prediction
            risk = self.risk_predictor.predict(
                packet.to_dict(),
                validation,
                history,
            )

            # 5. Alert evaluation
            await self.alert_manager.evaluate(risk, self.store)

            # 6. Push combined data to dashboard
            dashboard_data = {
                **packet.to_dict(),
                **risk,
                "validation": validation,
            }
            await self.dashboard.broadcast(dashboard_data)

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)

    async def run(self):
        """Start all subsystems."""
        # Initialize database
        await self.store.initialize()

        # Initialize hardware (graceful failure)
        try:
            self.sms.initialize()
        except Exception as e:
            logger.warning(f"SMS init skipped: {e}")

        try:
            self.buzzer.initialize()
        except Exception:
            logger.warning("Buzzer init skipped (no GPIO)")

        try:
            self.strobe.initialize()
        except Exception:
            logger.warning("Strobe init skipped (no GPIO)")

        logger.info("═" * 50)
        logger.info("  DISASTER SENTINEL — Running")
        logger.info(f"  Mode: {'SIMULATION' if self.simulate else 'HARDWARE'}")
        logger.info(f"  Dashboard: http://0.0.0.0:{self.config.get('dashboard', {}).get('port', 8080)}")
        logger.info("═" * 50)

        # Run receiver and dashboard concurrently
        dashboard_config = self.config.get("dashboard", {})
        host = dashboard_config.get("host", "0.0.0.0")
        port = dashboard_config.get("port", 8080)

        # Create uvicorn server
        uvi_config = uvicorn.Config(
            self.dashboard.app,
            host=host,
            port=port,
            log_level="warning",
        )
        server = uvicorn.Server(uvi_config)

        # Run both
        await asyncio.gather(
            server.serve(),
            self.receiver.start(),
        )

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self.receiver.stop()
        await self.buzzer.off()
        await self.strobe.off()
        self.sms.close()
        await self.store.close()
        logger.info("Shutdown complete")


def main():
    parser = argparse.ArgumentParser(description="Disaster Sentinel — Central System")
    parser.add_argument("--simulate", action="store_true",
                        help="Use simulated data (no LoRa hardware needed)")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to configuration file")
    parser.add_argument("--port", type=int, default=None,
                        help="Dashboard port (overrides config)")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    if args.port:
        config.setdefault("dashboard", {})["port"] = args.port

    # Create and run system
    sentinel = DisasterSentinel(config, simulate=args.simulate)

    try:
        asyncio.run(sentinel.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        asyncio.run(sentinel.shutdown())


if __name__ == "__main__":
    main()
