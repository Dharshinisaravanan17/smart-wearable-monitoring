"""
sensor_reader.py
----------------
Reads temperature from Arduino over serial (format: TEMP:36.5).
Simulates humidity and gas values since only TEMP is sent over serial.
Falls back to full simulation if Arduino is not connected or fails.
"""

import os
import serial
import random
import time
import threading
import logging

logger = logging.getLogger('SensorReader')


class SensorReader:
    def __init__(self, port=None, baud=None):
        self.port = port or os.getenv('SERIAL_PORT', 'COM5')
        try:
            self.baud = int(baud or os.getenv('SERIAL_BAUD', 9600))
        except ValueError:
            self.baud = 9600

        self.ser = None
        self.simulated = False
        self._lock = threading.Lock()

        # Internal state metrics
        self._temp = 36.5
        self._humidity = 60.0
        self._gas = 200

        self._connect()

    # ── Connection ────────────────────────────────────────────────────
    def _connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=2)
            time.sleep(2)  # wait for Arduino reset
            self.simulated = False
            logger.info(f"✅ Connected to Arduino on {self.port} at {self.baud} baud")
        except Exception as e:
            logger.warning(f"⚠️ Cannot open serial port {self.port}: {e}")
            logger.info("🔄 Running in SIMULATION mode — plug in Arduino anytime to connect.")
            self.simulated = True

    # ── Public read ───────────────────────────────────────────────────
    def read(self):
        """Return dict with temperature, humidity, gas, simulated flag."""
        with self._lock:
            if self.simulated:
                return self._simulate_all()
            return self._read_serial()

    # ── Serial read ───────────────────────────────────────────────────
    def _read_serial(self):
        try:
            if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                raw = self.ser.readline().decode('utf-8', errors='ignore').strip()
                self._parse_line(raw)
        except Exception as e:
            logger.error(f"Serial read error: {e} — switching to simulation mode.")
            self.simulated = True

        # Humidity & gas drift simulation (Arduino currently sends temperature)
        self._humidity += random.uniform(-0.5, 0.5)
        self._humidity = round(max(30.0, min(95.0, self._humidity)), 1)

        self._gas += random.randint(-15, 15)
        self._gas = max(100, min(700, self._gas))

        return {
            'temperature': round(self._temp, 1),
            'humidity': self._humidity,
            'gas': self._gas,
            'simulated': False  # Real temperature from serial
        }

    def _parse_line(self, line):
        """Parse 'TEMP:36.5' line format from Arduino serial output."""
        if line.upper().startswith('TEMP:'):
            try:
                val = float(line.split(':')[1])
                if 10.0 < val < 60.0:  # Sanity range check for human body / ambient temp
                    self._temp = val
            except (IndexError, ValueError):
                pass  # Ignore malformed packets gracefully

    # ── Full simulation ───────────────────────────────────────────────
    def _simulate_all(self):
        """Smoothly drift all values for realistic demo / testing."""
        self._temp += random.uniform(-0.3, 0.4)
        self._temp = round(max(30.0, min(42.0, self._temp)), 1)

        self._humidity += random.uniform(-1.0, 1.0)
        self._humidity = round(max(30.0, min(95.0, self._humidity)), 1)

        self._gas += random.randint(-20, 25)
        self._gas = max(100, min(700, self._gas))

        return {
            'temperature': self._temp,
            'humidity': self._humidity,
            'gas': self._gas,
            'simulated': True
        }

