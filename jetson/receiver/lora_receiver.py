"""
Disaster Sentinel — LoRa Receiver

Listens for SX1278 LoRa packets via SPI on the Jetson Orin Nano.
Decodes incoming packets and pushes them to the processing pipeline.

For development/simulation: includes a SimulatedReceiver that generates
fake packets for testing without hardware.
"""

import asyncio
import logging
import struct
import time
from typing import Callable, Optional
from datetime import datetime

from receiver.packet_decoder import decode_packet, DecodedPacket, format_packet_log

logger = logging.getLogger(__name__)


class LoRaReceiver:
    """
    SX1278 LoRa receiver using SPI interface.
    
    On Jetson Orin Nano:
      MOSI → Pin 19 (SPI0_MOSI)
      MISO → Pin 21 (SPI0_MISO)
      SCLK → Pin 23 (SPI0_SCK)
      CS   → Pin 24 (SPI0_CS0)
      RST  → Pin 22 (GPIO25)
      DIO0 → Pin 7  (GPIO04, IRQ)
    """

    def __init__(self, config: dict):
        self.config = config
        self.spi = None
        self.running = False
        self._callbacks = []

    def on_packet(self, callback: Callable[[DecodedPacket], None]):
        """Register a callback for received packets."""
        self._callbacks.append(callback)

    async def start(self):
        """Start listening for LoRa packets."""
        try:
            import spidev
            import Jetson.GPIO as GPIO

            # Initialize SPI
            self.spi = spidev.SpiDev()
            self.spi.open(
                self.config.get("spi_bus", 0),
                self.config.get("spi_device", 0)
            )
            self.spi.max_speed_hz = 5000000
            self.spi.mode = 0

            # Initialize GPIO for reset and DIO0
            GPIO.setmode(GPIO.BCM)
            rst_pin = self.config.get("reset_pin", 25)
            dio0_pin = self.config.get("dio0_pin", 4)

            GPIO.setup(rst_pin, GPIO.OUT)
            GPIO.setup(dio0_pin, GPIO.IN)

            # Reset LoRa module
            GPIO.output(rst_pin, GPIO.LOW)
            await asyncio.sleep(0.01)
            GPIO.output(rst_pin, GPIO.HIGH)
            await asyncio.sleep(0.01)

            # Configure SX1278 registers
            self._configure_sx1278()

            logger.info("LoRa receiver initialized on SPI")
            self.running = True

            # Main receive loop
            while self.running:
                # Check for incoming packet (DIO0 goes HIGH on packet received)
                if GPIO.input(dio0_pin):
                    raw_data = self._read_packet()
                    if raw_data:
                        rssi = self._read_rssi()
                        packet = decode_packet(raw_data, rssi)
                        if packet:
                            logger.info(format_packet_log(packet))
                            for cb in self._callbacks:
                                await cb(packet) if asyncio.iscoroutinefunction(cb) else cb(packet)

                await asyncio.sleep(0.01)  # 10ms poll interval

        except ImportError:
            logger.warning("SPI/GPIO libraries not available — use SimulatedReceiver for testing")
            raise

    def _configure_sx1278(self):
        """Configure SX1278 registers for LoRa reception."""
        freq = self.config.get("frequency", 433000000)
        sf = self.config.get("spreading_factor", 7)
        bw = self.config.get("bandwidth", 125000)
        sync = self.config.get("sync_word", 0xF3)

        # Set to sleep mode
        self._write_register(0x01, 0x00)
        # Set to LoRa mode
        self._write_register(0x01, 0x80)

        # Set frequency
        frf = int(freq * (2**19) / 32000000)
        self._write_register(0x06, (frf >> 16) & 0xFF)
        self._write_register(0x07, (frf >> 8) & 0xFF)
        self._write_register(0x08, frf & 0xFF)

        # Set spreading factor
        self._write_register(0x1E, (sf << 4) | 0x04)

        # Set sync word
        self._write_register(0x39, sync)

        # Set to continuous receive mode
        self._write_register(0x01, 0x85)

        logger.info(f"SX1278 configured: freq={freq/1e6}MHz, SF={sf}, sync=0x{sync:02X}")

    def _write_register(self, addr: int, value: int):
        """Write a single SX1278 register via SPI."""
        self.spi.xfer2([addr | 0x80, value])

    def _read_register(self, addr: int) -> int:
        """Read a single SX1278 register via SPI."""
        result = self.spi.xfer2([addr & 0x7F, 0x00])
        return result[1]

    def _read_packet(self) -> Optional[bytes]:
        """Read packet data from SX1278 FIFO."""
        # Get IRQ flags
        irq = self._read_register(0x12)
        # Check RxDone flag
        if not (irq & 0x40):
            return None

        # Check CRC error
        if irq & 0x20:
            logger.warning("LoRa CRC error — packet discarded")
            self._write_register(0x12, 0xFF)  # Clear IRQ
            return None

        # Get packet length
        length = self._read_register(0x13)
        # Set FIFO address to current RX address
        self._write_register(0x0D, self._read_register(0x10))

        # Read FIFO
        data = bytes(self.spi.xfer2([0x00] + [0x00] * length)[1:])

        # Clear IRQ flags
        self._write_register(0x12, 0xFF)

        return data

    def _read_rssi(self) -> int:
        """Read last packet RSSI."""
        return self._read_register(0x1A) - 157

    def stop(self):
        """Stop the receiver."""
        self.running = False
        if self.spi:
            self.spi.close()
        logger.info("LoRa receiver stopped")


class SimulatedReceiver:
    """
    Simulated LoRa receiver for development/testing without hardware.
    Generates realistic fake packets at configurable intervals.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.running = False
        self._callbacks = []
        self._scenarios = []

    def on_packet(self, callback: Callable):
        """Register a callback for received packets."""
        self._callbacks.append(callback)

    def add_scenario(self, scenario):
        """Add a simulation scenario that generates packets."""
        self._scenarios.append(scenario)

    async def start(self):
        """Start generating simulated packets."""
        from simulation.fake_node import (
            create_normal_flood_packet,
            create_normal_fire_packet,
            create_normal_landslide_packet,
            create_normal_pollution_packet,
        )

        self.running = True
        logger.info("Simulated LoRa receiver started (4 Nodes: FLD1, SLD2, FIR3, POL4)")

        seq = 0
        while self.running:
            # Generate normal packets from all 4 nodes
            for gen_func in [
                create_normal_flood_packet,
                create_normal_fire_packet,
                create_normal_landslide_packet,
                create_normal_pollution_packet,
            ]:
                raw = gen_func(seq)
                packet = decode_packet(raw, rssi=-50)
                if packet:
                    logger.info(format_packet_log(packet))
                    for cb in self._callbacks:
                        if asyncio.iscoroutinefunction(cb):
                            await cb(packet)
                        else:
                            cb(packet)
                seq += 1
                await asyncio.sleep(0.5)  # Stagger packets

            # Run any active scenarios
            for scenario in self._scenarios:
                if hasattr(scenario, 'generate_packet'):
                    raw = scenario.generate_packet(seq)
                    if raw:
                        packet = decode_packet(raw, rssi=-60)
                        if packet:
                            for cb in self._callbacks:
                                if asyncio.iscoroutinefunction(cb):
                                    await cb(packet)
                                else:
                                    cb(packet)
                        seq += 1

            await asyncio.sleep(2.0)  # Wait between cycles

    def stop(self):
        """Stop the simulated receiver."""
        self.running = False
        logger.info("Simulated receiver stopped")
