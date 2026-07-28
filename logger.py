"""
logger.py
---------
Background CSV data logger for Smart Wearable Monitoring System.
Periodically logs sensor and fatigue metrics into a CSV file.
Includes thread synchronization and memory-efficient tail reading.
"""

import csv
import os
import threading
import time
import logging
from collections import deque
from datetime import datetime

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s]: %(message)s')
logger = logging.getLogger('DataLogger')

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'readings.csv')
LOG_INTERVAL = 5  # seconds between writes
HEADERS = ['Timestamp', 'Temperature_C', 'Humidity_pct', 'Gas_ppm', 'Fatigue_Status', 'Simulated']

_file_lock = threading.Lock()


def _init_file():
    """Ensure the logs directory and CSV header line exist."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with _file_lock:
            if not os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow(HEADERS)
                logger.info(f"Initialized CSV log file at {LOG_FILE}")
    except Exception as e:
        logger.error(f"Failed to initialize log file: {e}")


def start_logger(get_sensor_data_fn, get_fatigue_fn):
    """
    Spawns background logging thread.
    get_sensor_data_fn() -> dict with keys: temperature, humidity, gas, simulated
    get_fatigue_fn()     -> str ('ACTIVE' | 'FATIGUE' | ...)
    """
    _init_file()

    def _loop():
        logger.info("Background CSV Logger thread started.")
        while True:
            time.sleep(LOG_INTERVAL)
            try:
                data = get_sensor_data_fn()
                fatigue = get_fatigue_fn()
                row = [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('temperature', ''),
                    data.get('humidity', ''),
                    data.get('gas', ''),
                    fatigue,
                    data.get('simulated', True)
                ]
                with _file_lock:
                    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                        csv.writer(f).writerow(row)
            except Exception as e:
                logger.error(f"Error appending log entry: {e}")

    t = threading.Thread(target=_loop, daemon=True, name="LoggerThread")
    t.start()


def read_last(n=20):
    """
    Efficiently read the last n log entries from CSV without loading entire file into memory.
    Returns a list of dicts.
    """
    if not os.path.exists(LOG_FILE):
        return []
    
    try:
        with _file_lock:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Use deque to keep only the last n rows in memory
                last_rows = deque(reader, maxlen=n)
                return list(last_rows)
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return []

