import httpx
import time
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from app.database import db
from bson import ObjectId

scheduler = AsyncIOScheduler()

async def perform_check(endpoint_id: str):
    """
    Background task to check an endpoint's status.
    """
    try:
        endpoint = await db.monitored_endpoints.find_one({"_id": ObjectId(endpoint_id)})
        if not endpoint:
            # Endpoint might have been deleted
            return

        url = endpoint['url']
        method = endpoint.get('method', 'GET')
        timeout = endpoint.get('timeout', 5)

        start = time.time()
        error = None
        status_code = None
        success = False

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url)
                status_code = response.status_code
                success = response.status_code < 400
        except httpx.TimeoutException:
            error = "Timeout"
        except httpx.RequestError as e:
            error = str(e)
        except Exception as e:
            error = str(e)

        response_time = int((time.time() - start) * 1000)
        checked_at = datetime.utcnow()

        # Log the result
        log_entry = {
            "endpoint_id": str(endpoint_id),
            "status_code": status_code,
            "response_time_ms": response_time,
            "success": success,
            "error": error,
            "checked_at": checked_at
        }
        await db.monitoring_logs.insert_one(log_entry)

        # Update last_checked and status in endpoint
        current_status = "up" if success else "down"
        await db.monitored_endpoints.update_one(
            {"_id": ObjectId(endpoint_id)},
            {
                "$set": {
                    "last_checked": checked_at,
                    "current_status": current_status,
                    "last_response_time": response_time
                }
            }
        )

    except Exception as e:
        print(f"Error checking endpoint {endpoint_id}: {e}")

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

async def load_jobs_from_db():
    """
    Load all active endpoints and schedule them.
    Useful on startup.
    """
    # Clear existing jobs to avoid duplicates if called multiple times (though usually only on startup)
    scheduler.remove_all_jobs()
    
    async for endpoint in db.monitored_endpoints.find({"is_active": True}):
        add_job(endpoint)

def add_job(endpoint):
    endpoint_id = str(endpoint["_id"])
    interval = endpoint.get("interval", 60)
    
    # Remove if exists (to be safe or if updating)
    try:
        scheduler.remove_job(endpoint_id)
    except JobLookupError:
        pass

    scheduler.add_job(
        perform_check, 
        "interval", 
        seconds=interval, 
        args=[endpoint_id], 
        id=endpoint_id,
        replace_existing=True
    )

def remove_job(endpoint_id: str):
    try:
        scheduler.remove_job(endpoint_id)
    except JobLookupError:
        pass
