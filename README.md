# 🛡️ Smart Wearable Telemetry & Fatigue Monitoring Dashboard

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205.3-7952b3.svg)](https://getbootstrap.com/)
[![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV%204.8-red.svg)](https://opencv.org/)
[![Deployment](https://img.shields.io/badge/Deployed%20on-Render-46E3B7.svg)](https://render.com/)

A production-grade, industrial-themed real-time monitoring dashboard designed for smart wearable safety systems. It collects biometric temperature, relative humidity, MQ2 gas concentration levels, and real-time computer vision worker fatigue/drowsiness detection.

---

## 📸 Screenshots & Demonstrations

> [!NOTE]
> *Placeholder for application UI screenshots in local and cloud deployment mode.*

| Live Telemetry Dashboard | OpenCV Fatigue Detection HUD |
| :---: | :---: |
| ![Dashboard Screenshot Placeholder](https://via.placeholder.com/600x350/0d1520/00d4ff?text=Smart+Wearable+Dashboard+UI) | ![Fatigue Detection Placeholder](https://via.placeholder.com/600x350/0d1520/ff3d3d?text=OpenCV+Haar+Fatigue+HUD) |

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph Hardware Layer
        A[Arduino Uno / DHT11 Sensor] -->|Serial COM / USB| B[SensorReader Module]
        C[USB Webcam] -->|OpenCV VideoCapture| D[FatigueDetector Engine]
    end

    subgraph Backend Core (Flask & Python)
        B -->|Thread Lock| E[Shared Telemetry State]
        D -->|Haar Cascades| E
        E --> F[Flask Web Server / WSGI Gunicorn]
        E -->|5s Interval| G[CSV Background Logger]
        G --> H[(readings.csv)]
    end

    subgraph Web Client (Bootstrap 5 UI)
        F -->|/api/data JSON Poll| I[Dashboard UI]
        F -->|/video_feed MJPEG Stream| I
        F -->|/api/logs JSON| I
        I --> J[Chart.js Telemetry Trend]
        I --> K[WebRTC Client Camera Toggle]
    end
```

---

## ✨ Key Features

- **Real-Time Telemetry Tracking**: Monitors temperature, humidity, and MQ2 gas levels.
- **Computer Vision Drowsiness Detection**: OpenCV Haar cascades track face and eye status continuously.
- **Dual Camera Mode (Cloud Compatible)**:
  - **Server Stream Mode**: Server-side MJPEG stream with synthetic fallback mode when hosted on cloud servers (Render/Heroku) without physical webcams.
  - **Browser Camera Mode**: Client-side WebRTC (`navigator.mediaDevices.getUserMedia`) captures local webcam directly inside the browser.
- **Thread-Safe Data Pipeline**: Dedicated background threads with mutex synchronization prevent I/O race conditions.
- **Responsive Bootstrap 5 UI**: Industrial cyber/amber dark aesthetic with Chart.js trend charts, SVG gauges, and alerts.
- **CSV Data Logging**: Memory-efficient tail-reading logging system using Python `collections.deque`.

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.9+
- Pip package manager
- (Optional) Arduino Uno with DHT11 temperature sensor

### 2. Clone & Setup Environment
```bash
git clone https://github.com/your-username/smart-wearable-monitoring.git
cd smart-wearable-monitoring/smart_wearable

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Locally
```bash
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## 🔌 Hardware Setup (Arduino Sketch)

Connect your DHT11 sensor to Arduino Pin 2 and upload the following code:

```cpp
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float t = dht.readTemperature();
  if (!isnan(t)) {
    Serial.print("TEMP:");
    Serial.println(t);
  }
  delay(2000);
}
```

> **Note**: If no Arduino is connected, the system automatically falls back to smooth **Simulation Mode** (indicated by the `⚡ SIM MODE` badge in the header).

---

## ☁️ Deployment on Render

This application is fully optimized for **Render** cloud deployment.

### Deploy Steps:
1. Push your repository to **GitHub**.
2. Log into [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Set the following environment configuration:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Deploy Web Service**.

> [!TIP]
> **Webcam on Cloud**: Render servers run headless (no physical camera). The application automatically switches to **Interactive Synthetic Demo Stream Mode** on the server, while allowing users to click **Browser Cam** in the UI to stream their own laptop camera via WebRTC!

---

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Main responsive dashboard interface |
| `/api/data` | `GET` | Current telemetry values, fatigue status, and active alerts |
| `/api/logs` | `GET` | Last 20 logged historical sensor entries |
| `/video_feed` | `GET` | MJPEG video stream (OpenCV camera or synthetic HUD) |

---

## 🔮 Future Enhancements

- [ ] **MediaPipe 468-Point Face Mesh**: Upgrade from Haar Cascades to Google MediaPipe for high-precision Eye Aspect Ratio (EAR) PERCLOS fatigue scoring.
- [ ] **AWS IoT Core Integration**: Stream telemetry data directly to AWS IoT MQTT topics for enterprise cloud storage.
- [ ] **Mobile Progressive Web App (PWA)**: Service worker caching and web manifest for native installation on Android/iOS.
- [ ] **Hardware BLE Wireless Upgrade**: Migrate from USB Serial to ESP32 / Bluetooth Low Energy (BLE) wireless transmission.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for details.
