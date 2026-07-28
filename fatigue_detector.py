"""
fatigue_detector.py
-------------------
Uses OpenCV Haar cascades to detect face + eyes in real time.
If eyes are absent for FATIGUE_THRESHOLD consecutive frames -> FATIGUE status.
Provides an MJPEG byte generator for Flask's /video_feed route.
Supports synthetic interactive fallback frames when hosted on cloud servers without webcams.
"""

import os
import cv2
import time
import math
import numpy as np
import threading
import logging

logger = logging.getLogger('FatigueDetector')


class FatigueDetector:

    FATIGUE_THRESHOLD = 20  # consecutive no-eye frames before alert

    def __init__(self):
        # Load cascades from OpenCV's built-in data directory
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
        except Exception as e:
            logger.error(f"Error loading Haar cascades: {e}")
            self.face_cascade = None
            self.eye_cascade = None

        self.cap = None
        self.status = 'INITIALIZING'
        self._no_eye_frames = 0
        self._frame_lock = threading.Lock()
        self._camera_ok = False
        
        # Synthetic simulation frame parameters
        self._sim_frame_count = 0

        self._init_camera()

    # ── Camera init ───────────────────────────────────────────────────
    def _init_camera(self):
        # Allow disabling physical camera via environment variable (e.g. for cloud deployments)
        if os.getenv('DISABLE_WEBCAM', '0') == '1':
            logger.info("[Camera] Webcam explicitly disabled via environment variable.")
            self.status = 'DEMO MODE'
            return

        try:
            # CAP_DSHOW on Windows for fast init; fallback to standard backend
            backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap = cap
                self._camera_ok = True
                self.status = 'ACTIVE'
                logger.info("✅ Physical webcam opened successfully.")
            else:
                self.status = 'DEMO MODE'
                logger.warning("⚠️ Could not open webcam — switching to synthetic interactive stream mode.")
        except Exception as e:
            self.status = 'DEMO MODE'
            logger.warning(f"⚠️ Video capture initialization exception: {e} — using synthetic stream mode.")

    # ── Core detection (called inside generate_frames loop) ───────────
    def _process_frame(self, frame):
        if self.face_cascade is None or self.eye_cascade is None:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        eyes_detected = False

        for (fx, fy, fw, fh) in faces:
            # Draw face bounding box
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 200, 100), 2)

            roi_gray = gray[fy:fy + fh, fx:fx + fw]
            roi_color = frame[fy:fy + fh, fx:fx + fw]

            eyes = self.eye_cascade.detectMultiScale(
                roi_gray, scaleFactor=1.1, minNeighbors=10)

            if len(eyes) > 0:
                eyes_detected = True
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey),
                                  (ex + ew, ey + eh), (0, 100, 255), 2)

        # Update consecutive no-eye counter
        with self._frame_lock:
            if eyes_detected:
                self._no_eye_frames = 0
                self.status = 'ACTIVE'
            else:
                self._no_eye_frames += 1
                if self._no_eye_frames >= self.FATIGUE_THRESHOLD:
                    self.status = 'FATIGUE'

        # ── Overlay HUD ──────────────────────────────────────────────────
        return self._draw_hud_overlay(frame, is_synthetic=False)

    # ── Synthetic interactive frame generator (Cloud / Fallback Mode) ─
    def _generate_synthetic_frame(self):
        """
        Creates a dark cyberpunk simulation feed with animated face outline,
        simulated eye status, and real-time fatigue tracking.
        """
        self._sim_frame_count += 1
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (15, 23, 32)  # Dark cyber panel background

        # Draw grid lines
        for x in range(0, 640, 40):
            cv2.line(img, (x, 0), (x, 480), (25, 38, 52), 1)
        for y in range(0, 480, 40):
            cv2.line(img, (0, y), (640, y), (25, 38, 52), 1)

        # Animated synthetic face circle & eyes
        center_x = 320 + int(20 * math.sin(self._sim_frame_count * 0.05))
        center_y = 230 + int(10 * math.cos(self._sim_frame_count * 0.03))

        # Simulate periodic eye blink or closure (fatigue cycle every ~150 frames)
        cycle_phase = self._sim_frame_count % 160
        eyes_open = cycle_phase < 110

        with self._frame_lock:
            if eyes_open:
                self._no_eye_frames = max(0, self._no_eye_frames - 1)
                if self._no_eye_frames < self.FATIGUE_THRESHOLD:
                    self.status = 'ACTIVE'
            else:
                self._no_eye_frames += 1
                if self._no_eye_frames >= self.FATIGUE_THRESHOLD:
                    self.status = 'FATIGUE'

        # Face outline
        face_color = (0, 60, 0) if self.status == 'ACTIVE' else (0, 0, 80)
        cv2.ellipse(img, (center_x, center_y), (90, 115), 0, 0, 360, (0, 200, 100), 2)

        # Eye markers
        left_eye = (center_x - 35, center_y - 20)
        right_eye = (center_x + 35, center_y - 20)

        if eyes_open:
            cv2.circle(img, left_eye, 10, (0, 100, 255), 2)
            cv2.circle(img, right_eye, 10, (0, 100, 255), 2)
            cv2.circle(img, left_eye, 3, (0, 212, 255), -1)
            cv2.circle(img, right_eye, 3, (0, 212, 255), -1)
        else:
            # Eyes closed indicator line
            cv2.line(img, (left_eye[0] - 10, left_eye[1]), (left_eye[0] + 10, left_eye[1]), (0, 0, 220), 2)
            cv2.line(img, (right_eye[0] - 10, right_eye[1]), (right_eye[0] + 10, right_eye[1]), (0, 0, 220), 2)

        # Mouth arc
        cv2.ellipse(img, (center_x, center_y + 40), (25, 12), 0, 0, 180, (0, 200, 100), 2)

        # Watermark notice
        cv2.putText(img, '[CLOUD DEMO FEED — SYNTHETIC SIMULATION]',
                    (105, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 140, 170), 1, cv2.LINE_AA)

        return self._draw_hud_overlay(img, is_synthetic=True)

    # ── HUD Overlay renderer ──────────────────────────────────────────
    def _draw_hud_overlay(self, frame, is_synthetic=False):
        if self.status == 'FATIGUE':
            overlay_color = (0, 0, 220)
            label = 'WARNING: FATIGUE DETECTED'
        else:
            overlay_color = (0, 200, 80)
            label = 'STATUS: ACTIVE / NORMAL'

        # Top semi-transparent HUD banner
        bar = frame.copy()
        cv2.rectangle(bar, (0, 0), (frame.shape[1], 50), (15, 15, 20), -1)
        cv2.addWeighted(bar, 0.7, frame, 0.3, 0, frame)

        cv2.putText(frame, label, (12, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.7, overlay_color, 2, cv2.LINE_AA)

        counter_text = f'No-Eye: {self._no_eye_frames}/{self.FATIGUE_THRESHOLD}'
        cv2.putText(frame, counter_text, (frame.shape[1] - 210, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

        return frame

    # ── MJPEG generator (Flask uses this) ────────────────────────────
    def generate_frames(self):
        """Yields MJPEG-encoded frames continuously for web clients."""
        while True:
            try:
                if not self._camera_ok or self.cap is None:
                    frame = self._generate_synthetic_frame()
                else:
                    ret, frame = self.cap.read()
                    if not ret:
                        frame = self._generate_synthetic_frame()
                    else:
                        frame = self._process_frame(frame)

                # Encode frame to JPEG format
                ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ok:
                    time.sleep(0.05)
                    continue

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n'
                       + buf.tobytes()
                       + b'\r\n')

            except Exception as e:
                logger.error(f"Error in video frame generation loop: {e}")
                time.sleep(0.1)

            time.sleep(0.04)  # Target ~25 FPS

