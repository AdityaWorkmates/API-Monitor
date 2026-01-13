# API Monitor Backend

FastAPI backend for the API Monitor application.

## Features

- **Endpoint Management**: Create, Read, Update, Delete API endpoints to monitor.
- **Monitoring**: Background scheduler (APScheduler) checks endpoints periodically.
- **Logging**: Stores status, response time, and errors in MongoDB.
- **Stats**: Aggregates uptime and response time statistics.

## Setup

1.  **Prerequisites**:
    - Python 3.12+
    - MongoDB (running locally or remote)

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # OR using the pyproject.toml
    pip install .
    ```

3.  **Configuration**:
    - Copy `.env.example` to `.env`
    - Update `MONGO_URI` if needed.

4.  **Run**:
    ```bash
    python main.py
    # OR
    uvicorn app.main:app --reload
    ```

## API Documentation

Once running, visit `http://localhost:8000/docs` for the interactive API documentation (Swagger UI).
