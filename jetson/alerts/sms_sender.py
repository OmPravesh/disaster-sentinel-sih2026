"""
Disaster Sentinel — SMS Sender (SIM800L)

Controls SIM800L GSM module via UART to send emergency SMS alerts.
"""

import asyncio
import logging
import serial
from typing import List, Optional

logger = logging.getLogger(__name__)


class SMSSender:
    """SIM800L UART-based SMS sender."""

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.port = cfg.get("uart_port", "/dev/ttyTHS1")
        self.baud = cfg.get("baud_rate", 9600)
        self.recipients = cfg.get("recipients", [])
        self.enabled = cfg.get("enabled", True)
        self.serial: Optional[serial.Serial] = None

    def initialize(self):
        """Initialize UART connection to SIM800L."""
        if not self.enabled:
            logger.info("[SMS] Disabled in config")
            return

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=5,
                writeTimeout=5,
            )
            logger.info(f"[SMS] SIM800L connected on {self.port}")

            # Test AT command
            response = self._send_at("AT")
            if "OK" in response:
                logger.info("[SMS] SIM800L responding")
            else:
                logger.warning(f"[SMS] Unexpected response: {response}")

            # Set text mode
            self._send_at("AT+CMGF=1")

            # Check signal
            signal = self._send_at("AT+CSQ")
            logger.info(f"[SMS] Signal: {signal.strip()}")

        except Exception as e:
            logger.error(f"[SMS] Failed to initialize: {e}")
            self.serial = None

    async def send(self, message: str, recipients: List[str] = None):
        """Send SMS to all configured recipients."""
        if not self.enabled:
            logger.info(f"[SMS] Would send (disabled): {message[:50]}...")
            return

        targets = recipients or self.recipients
        if not targets:
            logger.warning("[SMS] No recipients configured")
            return

        for number in targets:
            await self._send_sms(number, message)

    async def _send_sms(self, number: str, message: str):
        """Send a single SMS."""
        if not self.serial:
            logger.warning(f"[SMS] Not connected — cannot send to {number}")
            logger.info(f"[SMS] Message: {message[:100]}...")
            return

        try:
            # Set recipient
            self._send_at(f'AT+CMGS="{number}"', wait=1)

            # Send message + Ctrl+Z
            self.serial.write((message + chr(26)).encode())
            await asyncio.sleep(5)  # Wait for transmission

            # Read response
            response = self.serial.read(self.serial.in_waiting).decode(errors='ignore')

            if "OK" in response:
                logger.info(f"[SMS] Sent to {number}")
            else:
                logger.error(f"[SMS] Failed to send to {number}: {response}")

        except Exception as e:
            logger.error(f"[SMS] Error sending to {number}: {e}")

    def _send_at(self, command: str, wait: float = 0.5) -> str:
        """Send AT command and return response."""
        if not self.serial:
            return ""
        self.serial.write((command + "\r\n").encode())
        import time
        time.sleep(wait)
        response = self.serial.read(self.serial.in_waiting).decode(errors='ignore')
        return response

    def close(self):
        """Close serial connection."""
        if self.serial:
            self.serial.close()
            logger.info("[SMS] Connection closed")
