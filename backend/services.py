import httpx
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from fastapi import HTTPException, status

from config import settings
from models import db, EndpointCreate, EndpointUpdate, MonitoringLogBase

# --- Authentication Service ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def verify_password(plain_password, hashed_password) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def get_user_by_email(email: str):
        return await db.users.find_one({"email": email})

    @staticmethod
    async def create_user(email: str, password: str):
        existing_user = await AuthService.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = AuthService.get_password_hash(password)
        user_dict = {
            "email": email,
            "password": hashed_password
        }
        await db.users.insert_one(user_dict)
        return user_dict

# --- Scheduler & Monitoring Service ---
scheduler = AsyncIOScheduler()

async def perform_check(endpoint_id: str):
    """
    Background task to check an endpoint's status.
    """
    try:
        endpoint = await db.monitored_endpoints.find_one({"_id": ObjectId(endpoint_id)})
        if not endpoint:
            return

        url = endpoint['url']
        method = endpoint.get('method', 'GET')
        timeout = endpoint.get('timeout', 5)
        headers = endpoint.get('headers', {})
        body = endpoint.get('body', None)

        start = time.time()
        error = None
        status_code = None
        success = False

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, headers=headers, json=body)
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

        # Update last_checked in endpoint
        await db.monitored_endpoints.update_one(
            {"_id": ObjectId(endpoint_id)},
            {"$set": {"last_checked": checked_at}}
        )

    except Exception as e:
        print(f"Error checking endpoint {endpoint_id}: {e}")

async def cleanup_logs():
    """
    Delete logs older than 7 days.
    """
    try:
        retention_days = 7
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        result = await db.monitoring_logs.delete_many({"checked_at": {"$lt": cutoff_date}})
        print(f"Cleanup: Deleted {result.deleted_count} logs older than {retention_days} days.")
    except Exception as e:
        print(f"Error cleaning up logs: {e}")

class MonitoringService:
    @staticmethod
    def start_scheduler():
        if not scheduler.running:
            scheduler.start()
        
        # Schedule cleanup job
        try:
            scheduler.add_job(
                cleanup_logs,
                "interval",
                days=1,
                id="cleanup_logs_daily",
                replace_existing=True
            )
        except Exception as e:
            print(f"Failed to schedule cleanup job: {e}")

    @staticmethod
    async def load_jobs_from_db():
        scheduler.remove_all_jobs()
        # Re-add cleanup
        MonitoringService.start_scheduler() # Ensures cleanup is there
        
        async for endpoint in db.monitored_endpoints.find({"is_active": True}):
            MonitoringService.add_job(endpoint)

    @staticmethod
    def add_job(endpoint: dict):
        endpoint_id = str(endpoint["_id"])
        interval = endpoint.get("interval", 60)
        
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

    @staticmethod
    def remove_job(endpoint_id: str):
        try:
            scheduler.remove_job(endpoint_id)
        except JobLookupError:
            pass

# --- Endpoint Service ---
class EndpointService:
    @staticmethod
    async def create_endpoint(endpoint: EndpointCreate, user_email: str):
        endpoint_dict = endpoint.model_dump()
        endpoint_dict["created_at"] = datetime.utcnow()
        endpoint_dict["last_checked"] = None
        endpoint_dict["owner_email"] = user_email
        
        new_endpoint = await db.monitored_endpoints.insert_one(endpoint_dict)
        created_endpoint = await db.monitored_endpoints.find_one({"_id": new_endpoint.inserted_id})
        
        if created_endpoint["is_active"]:
            MonitoringService.add_job(created_endpoint)
            
        return created_endpoint

    @staticmethod
    async def get_endpoints(user_email: str, limit: int = 1000):
        return await db.monitored_endpoints.find({"owner_email": user_email}).to_list(limit)

    @staticmethod
    async def get_endpoint_by_id(id: str, user_email: str):
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        endpoint = await db.monitored_endpoints.find_one({
            "_id": ObjectId(id),
            "owner_email": user_email
        })
        
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return endpoint

    @staticmethod
    async def update_endpoint(id: str, endpoint_update: EndpointUpdate, user_email: str):
        # Verify existence and ownership
        await EndpointService.get_endpoint_by_id(id, user_email)
        
        update_data = {k: v for k, v in endpoint_update.model_dump().items() if v is not None}
        
        if len(update_data) >= 1:
            await db.monitored_endpoints.update_one(
                {"_id": ObjectId(id)}, {"$set": update_data}
            )

        updated_endpoint = await db.monitored_endpoints.find_one({"_id": ObjectId(id)})
        
        # Update scheduler
        if updated_endpoint["is_active"]:
            MonitoringService.add_job(updated_endpoint)
        else:
            MonitoringService.remove_job(str(updated_endpoint["_id"]))
            
        return updated_endpoint

    @staticmethod
    async def delete_endpoint(id: str, user_email: str):
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        delete_result = await db.monitored_endpoints.delete_one({
            "_id": ObjectId(id),
            "owner_email": user_email
        })
        
        if delete_result.deleted_count == 1:
            MonitoringService.remove_job(id)
        else:
            raise HTTPException(status_code=404, detail="Endpoint not found")

    @staticmethod
    async def get_logs(endpoint_id: str, limit: int = 50):
        if not ObjectId.is_valid(endpoint_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
            
        logs = await db.monitoring_logs.find(
            {"endpoint_id": endpoint_id}
        ).sort("checked_at", -1).limit(limit).to_list(limit)
        return logs

    @staticmethod
    async def get_stats(endpoint_id: str):
        if not ObjectId.is_valid(endpoint_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        pipeline = [
            {"$match": {"endpoint_id": endpoint_id}},
            {"$group": {
                "_id": None,
                "average_response_time": {"$avg": "$response_time_ms"},
                "total_checks": {"$sum": 1},
                "successful_checks": {
                    "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                }
            }}
        ]
        
        cursor = db.monitoring_logs.aggregate(pipeline)
        result = await cursor.to_list(1)
        
        if not result:
            return {
                "average_response_time": 0,
                "total_checks": 0,
                "successful_checks": 0,
                "uptime_percentage": 0
            }
        
        stats = result[0]
        total = stats["total_checks"]
        success = stats["successful_checks"]
        uptime = (success / total * 100) if total > 0 else 0
        
        return {
            "average_response_time": round(stats["average_response_time"], 2),
            "total_checks": total,
            "successful_checks": success,
            "uptime_percentage": round(uptime, 2)
        }
