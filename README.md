# 🚀 API Monitor

A modern, professional-grade API monitoring and alerting system. Track the uptime and performance of your services with real-time dashboards, threshold-based alerting, and multi-channel notifications.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)
![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248.svg)
![Tailwind](https://img.shields.io/badge/Styling-TailwindCSS-38B2AC.svg)

---

## 🌟 Key Features

- **Real-time Monitoring:** Automated health checks with configurable intervals.
- **Smart Alerting:** Threshold-based logic (alerts only if 4 out of last 5 checks fail) to prevent false positives.
- **Rich Notifications:**
  - **Slack:** Instant alerts via Incoming Webhooks with status colors.
  - **Email:** Modern, professional HTML alerts sent via SMTP.
- **Performance Analytics:** Visual response time history using interactive charts.
- **Modern UI/UX:**
  - Full **Dark Mode** support.
  - Responsive Dashboard for mobile and desktop.
  - Automatic session management and auto-logout on token expiry.
- **Secure:** JWT-based authentication with ownership-based access control.

---

## 📂 Project Structure

```text
API-Monitor/
├── backend/            # FastAPI, MongoDB, & Background Scheduler
├── frontend/           # React, Tailwind CSS, & Vite
└── database/           # Database configuration/logs (if applicable)
```

---

## 🛠️ Tech Stack

- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons, Chart.js.
- **Backend:** Python 3.12, FastAPI, Motor (Async MongoDB), APScheduler, HTTPX.
- **Database:** MongoDB.

---

## 🚦 Getting Started

### Prerequisites
- **MongoDB:** Ensure MongoDB is installed and running on `localhost:27017` (or update `.env`).
- **Python 3.12+**
- **Node.js & npm**

### 1. Backend Setup
```bash
cd backend
# 1. Copy the example environment file
cp .env.example .env
# 2. Update .env with your SECRET_KEY and SMTP credentials
# 3. Install dependencies using 'uv' (recommended)
uv sync
# 4. Start the server
uv run main.py
```
*The API will be available at `http://localhost:8000`*

### 2. Frontend Setup
```bash
cd frontend
# 1. Install dependencies
npm install
# 2. Start the development server
npm run dev
```
*The UI will be available at `http://localhost:5173`*

---

## 🧪 Testing the Monitor
1. Create an account and log in.
2. Add a new endpoint with a 10s interval.
3. To test alerts, use a non-existent URL like `https://broken-api-test-123.com`.
4. Wait for 4-5 checks (~50 seconds) to receive your Slack/Email notification!

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
