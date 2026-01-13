# ⚙️ API Monitor - Backend

The core engine of the API Monitor, responsible for scheduling health checks, managing data, and triggering notifications.

## 🚀 Technologies

- **FastAPI:** High-performance web framework for building APIs.
- **Motor:** Asynchronous Python driver for MongoDB.
- **APScheduler:** Background task scheduling for periodic health checks.
- **HTTPX:** Modern async HTTP client for probing endpoints.
- **Pydantic:** Data validation and settings management.

## 🔑 Key Components

- **Monitoring Service:** Manages the background worker pool. It reloads active jobs from the database on startup.
- **Threshold Logic:** Implements the `4/5 failure` rule. It evaluates the last 5 logs for an endpoint before deciding to trigger an alert.
- **Notification Engine:** 
  - `send_slack_notification`: Formats and sends Slack payloads.
  - `send_email_notification`: Uses `smtplib` and `asyncio.to_thread` to send rich HTML emails without blocking the main event loop.

## 🛠️ Configuration (.env)

| Variable | Description |
| :--- | :--- |
| `MONGO_URI` | Connection string for MongoDB. |
| `SECRET_KEY` | Secure key for generating JWT tokens. |
| `SMTP_HOST` | SMTP server address (e.g., smtp.gmail.com). |
| `SMTP_USER` | Your email address for sending alerts. |
| `SMTP_PASSWORD` | App-specific password (not your main password). |

## 📡 API Endpoints

- `POST /auth/register`: Create a new account.
- `POST /auth/login`: Authenticate and receive a JWT.
- `GET /endpoints/`: List all monitors for the current user.
- `POST /endpoints/`: Add a new endpoint to monitor.
- `GET /stats/{id}`: Get uptime percentage and average latency.
- `GET /logs/{id}`: Retrieve recent health check history.

## 🏃 How to Run

1. **Environment:** Ensure you have Python 3.12+ installed.
2. **Dependencies:** Use `uv` for fast dependency management:
   ```bash
   uv sync
   ```
3. **Configuration:** Copy `.env.example` to `.env` and fill in your MongoDB URI, JWT Secret, and SMTP credentials.
4. **Launch:**
   ```bash
   uv run main.py
   ```
   The backend uses Uvicorn with auto-reload enabled for development.