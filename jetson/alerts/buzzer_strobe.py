"""
Disaster Sentinel — Buzzer & Strobe GPIO Control

Controls physical alarm devices at the Disaster Relief Center.
Uses Jetson GPIO (or simulated GPIO for development).
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BuzzerControl:
    """Controls buzzer via GPIO pin."""

    def __init__(self, pin: int = 12, enabled: bool = True):
        self.pin = pin
        self.enabled = enabled
        self._gpio = None
        self._is_on = False
        self._continuous_task: Optional[asyncio.Task] = None

    def initialize(self):
        """Initialize GPIO for buzzer."""
        if not self.enabled:
            logger.info("[Buzzer] Disabled")
            return

        try:
            import Jetson.GPIO as GPIO
            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
            logger.info(f"[Buzzer] Initialized on GPIO {self.pin}")
        except ImportError:
            logger.warning("[Buzzer] GPIO not available — running in simulation mode")
            self._gpio = None

    async def short_beep(self, duration_ms: int = 500):
        """Single short beep."""
        logger.info(f"[Buzzer] Short beep ({duration_ms}ms)")
        if self._gpio:
            self._gpio.output(self.pin, self._gpio.HIGH)
            await asyncio.sleep(duration_ms / 1000)
            self._gpio.output(self.pin, self._gpio.LOW)

    async def continuous_on(self, interval_ms: int = 1000):
        """Start continuous beeping pattern."""
        if self._is_on:
            return

        self._is_on = True
        logger.warning("[Buzzer] CONTINUOUS ALARM ON")

        async def _beep_loop():
            while self._is_on:
                if self._gpio:
                    self._gpio.output(self.pin, self._gpio.HIGH)
                    await asyncio.sleep(0.3)
                    self._gpio.output(self.pin, self._gpio.LOW)
                    await asyncio.sleep(interval_ms / 1000 - 0.3)
                else:
                    await asyncio.sleep(1)

        self._continuous_task = asyncio.create_task(_beep_loop())

    async def off(self):
        """Turn off buzzer."""
        self._is_on = False
        if self._continuous_task:
            self._continuous_task.cancel()
            self._continuous_task = None
        if self._gpio:
            self._gpio.output(self.pin, self._gpio.LOW)
        logger.info("[Buzzer] OFF")

    def cleanup(self):
        """Cleanup GPIO."""
        if self._gpio:
            self._gpio.output(self.pin, self._gpio.LOW)


class StrobeControl:
    """Controls warning strobe/light via GPIO + relay."""

    def __init__(self, pin: int = 16, enabled: bool = True):
        self.pin = pin
        self.enabled = enabled
        self._gpio = None
        self._is_on = False

    def initialize(self):
        """Initialize GPIO for strobe."""
        if not self.enabled:
            logger.info("[Strobe] Disabled")
            return

        try:
            import Jetson.GPIO as GPIO
            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
            logger.info(f"[Strobe] Initialized on GPIO {self.pin}")
        except ImportError:
            logger.warning("[Strobe] GPIO not available — running in simulation mode")
            self._gpio = None

    async def on(self):
        """Turn strobe ON."""
        if self._is_on:
            return
        self._is_on = True
        if self._gpio:
            self._gpio.output(self.pin, self._gpio.HIGH)
        logger.warning("[Strobe] WARNING LIGHT ON")

    async def off(self):
        """Turn strobe OFF."""
        self._is_on = False
        if self._gpio:
            self._gpio.output(self.pin, self._gpio.LOW)
        logger.info("[Strobe] Light OFF")

    def cleanup(self):
        """Cleanup GPIO."""
        if self._gpio:
            self._gpio.output(self.pin, self._gpio.LOW)
