# 🤖 AI Face-Recognition Attendance System

A high-performance, automated attendance tracking system leveraging AI and Computer Vision. This project integrates a Django-based management dashboard with hardware edge devices (ESP32/Raspberry Pi) for seamless, contactless attendance marking.

![Project Banner](https://img.shields.io/badge/AI-Attendance-blueviolet?style=for-the-badge&logo=django)
![Face Recognition](https://img.shields.io/badge/Powered%20By-Face--Recognition-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

---

## 🏗️ Project Architecture

This system follows a client-server architecture where:
1. **Edge Device (Hardware):** Captures live frames and sends them to the server for processing.
2. **Django Server (Core):** Handles face encoding, recognition logic, and attendance records.
3. **Web Dashboard:** Provides a user-friendly interface for administrators to manage students and view analytics.

## 🚀 Key Features

- **🧠 Advanced Face Recognition**: Powered by `dlib` and `face_recognition`, providing high accuracy and lightning-fast matching.
- **📸 Smart Student Registration**:
  - **Single Upload**: Register students one-by-one with clear photo validation.
  - **Bulk Upload**: Rapidly import entire classes using standard naming conventions (`RollNumber_Name.jpg`).
- **📊 Interactive Dashboard**:
  - Daily attendance summaries with filtering by date.
  - Real-time present/total student counters.
  - **Hardware Heartbeat**: Monitor the connection status of your scanning devices in real-time.
- **🔌 Hardware-Agnostic API**: Specially designed endpoints to receive data from ESP32-CAM glasses or Raspberry Pi devices.
- **☁️ Deployment Ready**: Optimized for platforms like Hugging Face Spaces or Render, with Gunicorn and WhiteNoise pre-configured.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Django 5.x
- **AI/ML**: `face_recognition` (dlib), `OpenCV`, `NumPy`
- **Frontend**: HTML5, Vanilla CSS, JavaScript (Real-time polling)
- **Database**: SQLite (Dev) / PostgreSQL (Optional)
- **Infrastructure**: Docker, Gunicorn, WhiteNoise

---

## 📂 Project Structure

```text
AI_Attendance/
├── attendance_app/        # Main logic: models, views, and templates
├── core/                  # Django project configuration & settings
├── raspberry_code/        # Scripts for running on Raspberry Pi edge devices
├── media/                 # Storage for uploaded student photos
├── staticfiles/           # Collected static assets
├── manage.py              # Django management script
├── Dockerfile             # Container configuration
└── requirements.txt       # Python dependencies
```

---

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.10+
- C++ Compiler (required for `dlib`)
- CMake

### 2. Installation

1. **Clone the Repo**
   ```bash
   git clone <your-repo-url>
   cd AI_Attendance
   ```

2. **Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # .venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

---

## 📁 Bulk Upload Convention

To use the Bulk Upload feature, ensure your photos are named as follows:
- **Format**: `RollNumber_Name.jpg`
- **Example**: `2021CS101_John-Doe.jpg`
- **Note**: Hyphens in the name will be automatically converted to spaces.

---

## 📡 Hardware Integration

The server exposes a `@csrf_exempt` endpoint at `/hardware-scan/`. Edge devices can POST image bytes directly to this URL. The system will process the image, match faces against the database, and mark attendance instantly.

---

## 📝 License

This project is for educational and administrative purposes. Feel free to contribute!

---

*Developed with ❤️ by [Hardik Mittal](https://github.com/mittalhardik)*
