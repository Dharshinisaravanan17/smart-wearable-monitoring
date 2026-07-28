"""
app.py
------
Smart Wearable Monitoring System — Flask Backend Server
Run locally:  python app.py
Production:   gunicorn app:app --bind 0.0.0.0:$PORT
"""

import os
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, Response

from sensor_reader import SensorReader
from fatigue_detector import FatigueDetector
import logger as Logger

# ── Configure Logging ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s]: %(message)s')
logger = logging.getLogger('SmartWearableApp')

# ── Flask Application Setup ────────────────────────────────────────────
app = Flask(__name__)

# ── Component Initialization ──────────────────────────────────────────
sensor = SensorReader()
fatigue = FatigueDetector()

# ── Shared Sensor State (Thread-safe) ──────────────────────────────────
_sensor_data = {
    'temperature': 36.5,
    'humidity': 60.0,
    'gas': 200,
    'simulated': True
}
_lock = threading.Lock()


def _get_sensor():
    with _lock:
        return dict(_sensor_data)


def _get_fatigue():
    return fatigue.status


# ── Background Sensor Sampling Thread ────────────────────────────────
def _sensor_loop():
    logger.info("Background sensor polling thread started.")
    while True:
        try:
            data = sensor.read()
            with _lock:
                _sensor_data.update(data)
        except Exception as e:
            logger.error(f"Error reading sensor data in background loop: {e}")
        time.sleep(2)


threading.Thread(target=_sensor_loop, daemon=True, name='SensorThread').start()

# ── Initialize CSV Logger ──────────────────────────────────────────────
Logger.start_logger(_get_sensor, _get_fatigue)


# ── Alert Evaluation Helper ───────────────────────────────────────────
def _build_alerts(data, fatigue_status):
    alerts = []

    # Temperature threshold checks
    temp = data.get('temperature', 36.5)
    if temp >= 38.0:
        alerts.append({
            'level': 'danger',
            'msg': f"High Temperature: {temp}°C — Immediate action required!"
        })
    elif temp >= 36.5:
        alerts.append({
            'level': 'warning',
            'msg': f"Elevated Temperature: {temp}°C — Monitor closely."
        })

    # Fatigue alert check
    if fatigue_status == 'FATIGUE':
        alerts.append({
            'level': 'danger',
            'msg': 'Fatigue Detected — Please take a break immediately!'
        })

    # Gas (MQ2) safety checks
    gas = data.get('gas', 200)
    if gas >= 500:
        alerts.append({
            'level': 'danger',
            'msg': f"Dangerous Gas Concentration: {gas} ppm — Ventilate room!"
        })
    elif gas >= 350:
        alerts.append({
            'level': 'warning',
            'msg': f"Elevated Gas Level: {gas} ppm — Caution advised."
        })

    return alerts


# ══════════════════════════════════════════════════════════════════════
# Routes & Controllers
# ══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Render the main responsive dashboard."""
    return render_template('dashboard.html')


@app.route('/api/data')
def api_data():
    """Return JSON payload of current real-time sensor metrics and alerts."""
    try:
        data = _get_sensor()
        fatigue_status = _get_fatigue()
        alerts = _build_alerts(data, fatigue_status)

        return jsonify({
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'gas': data['gas'],
            'fatigue': fatigue_status,
            'simulated': data['simulated'],
            'alerts': alerts,
            'alert_count': len(alerts),
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%d %b %Y')
        })
    except Exception as e:
        logger.error(f"Error serving /api/data: {e}")
        return jsonify({'error': 'Failed to retrieve telemetry data'}), 500


@app.route('/api/logs')
def api_logs():
    """Return recent historical CSV logs for UI table rendering."""
    try:
        rows = Logger.read_last(20)
        return jsonify(rows)
    except Exception as e:
        logger.error(f"Error serving /api/logs: {e}")
        return jsonify({'error': 'Failed to read telemetry logs'}), 500


@app.route('/video_feed')
def video_feed():
    """MJPEG streaming route for live video/fatigue detector feed."""
    try:
        return Response(
            fatigue.generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f"Error streaming video feed: {e}")
        return Response("Video stream unavailable", status=500)


# ── Standalone CLI Entrypoint ─────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']

    logger.info("═" * 55)
    logger.info("  🛡️  Smart Wearable Monitoring Dashboard")
    logger.info("═" * 55)
    logger.info(f"  Port: {port} | Debug: {debug}")
    logger.info(f"  Serial Port: {sensor.port} (Baud: {sensor.baud})")
    logger.info("═" * 55)

    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)

