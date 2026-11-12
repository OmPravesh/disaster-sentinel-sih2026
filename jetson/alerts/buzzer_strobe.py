"""
Disaster Sentinel — Buzzer & Strobe Control
Delegates physical actuation to the central Web Server GPIO engine
to avoid Tegra GPIO resource collisions (Errno 16 Device or Resource Busy).
"""

import asyncio
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)


def _call_hub_actuator(device: str, action: str):
    """Dispatches HTTP trigger to the local Web Server actuator endpoint."""
    try:
        url = f"http://127.0.0.1:5000/api/actuators/{device}/{action}"
        req = urllib.request.Request(url, data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
    except Exception as e:
        logger.debug(f"[Actuator API] Local hub dispatch {device}/{action}: {e}")


class BuzzerControl:
    """Controls buzzer via central web server GPIO engine."""

    def __init__(self, pin: int = 12, enabled: bool = True):
        self.pin = pin
        self.enabled = enabled
        self._is_on = False
        self._continuous_task: Optional[asyncio.Task] = None

    def initialize(self):
        """Initialize Buzzer control."""
        if not self.enabled:
            logger.info("[Buzzer] Disabled")
            return
        logger.info("[Buzzer] Initialized via Central Hub GPIO API")

    async def short_beep(self, duration_ms: int = 500):
        """Single short beep."""
        if not self.enabled:
            return
        logger.info(f"[Buzzer] Short beep ({duration_ms}ms)")
        _call_hub_actuator("buzzer", "pulse")

    async def continuous_on(self, interval_ms: int = 1000):
        """Start continuous alarm."""
        if not self.enabled or self._is_on:
            return
        self._is_on = True
        logger.warning("[Buzzer] CONTINUOUS ALARM ON")
        _call_hub_actuator("buzzer", "on")

    async def off(self):
        """Turn off buzzer (automatic background deactivation)."""
        self._is_on = False
        if self._continuous_task:
            self._continuous_task.cancel()
            self._continuous_task = None
        _call_hub_actuator("buzzer", "auto_off")
        logger.info("[Buzzer] OFF")

    def cleanup(self):
        """Cleanup buzzer."""
        self._is_on = False
        _call_hub_actuator("buzzer", "auto_off")


class StrobeControl:
    """Controls warning strobe/light via central web server GPIO engine."""

    def __init__(self, pin: int = 16, enabled: bool = True):
        self.pin = pin
        self.enabled = enabled
        self._is_on = False

    def initialize(self):
        """Initialize Strobe control."""
        if not self.enabled:
            logger.info("[Strobe] Disabled")
            return
        logger.info("[Strobe] Initialized via Central Hub GPIO API")

    async def on(self):
        """Turn strobe ON."""
        if not self.enabled or self._is_on:
            return
        self._is_on = True
        _call_hub_actuator("strobe", "on")
        logger.warning("[Strobe] WARNING LIGHT ON")

    async def off(self):
        """Turn strobe OFF (automatic background deactivation)."""
        self._is_on = False
        _call_hub_actuator("strobe", "auto_off")
        logger.info("[Strobe] Light OFF")

    def cleanup(self):
        """Cleanup strobe."""
        self._is_on = False
        _call_hub_actuator("strobe", "auto_off")
