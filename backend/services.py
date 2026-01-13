import httpx
import time
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

    @staticmethod
    async def authenticate_user(email: str, password: str):
        user = await AuthService.get_user_by_email(email)
        if not user or not AuthService.verify_password(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

# --- Scheduler & Monitoring Service ---
scheduler = AsyncIOScheduler()

async def send_email_notification(to_email: str, endpoint_name: str, url: str, success: bool, status_code: Optional[int], error: Optional[str]):
    """
    Sends an email notification using SMTP.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD or not to_email:
        return

    status_text = "UP" if success else "DOWN"
    subject = f"API Status Change: {endpoint_name} is {status_text}"
    
    body = f"""
    <h3>API Status Alert</h3>
    <p>The status of your monitored API has changed.</p>
    <ul>
        <li><b>Endpoint:</b> {endpoint_name}</li>
        <li><b>URL:</b> {url}</li>
        <li><b>New Status:</b> <span style="color: {'green' if success else 'red'}">{status_text}</span></li>
        <li><b>Status Code:</b> {status_code if status_code else 'N/A'}</li>
        <li><b>Error:</b> {error if error else 'None'}</li>
        <li><b>Checked At:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
    </ul>
    """

    message = MIMEMultipart()
    message["From"] = settings.EMAILS_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    def send_sync_email():
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
        except Exception as e:
            print(f"Failed to send email notification: {e}")

    await asyncio.to_thread(send_sync_email)

async def send_slack_notification(webhook_url: str, endpoint_name: str, url: str, success: bool, status_code: Optional[int], error: Optional[str]):
    """
    Sends a notification to Slack via Webhook.
    """
    if not webhook_url:
        return

    status_text = "UP" if success else "DOWN"
    color = "#36a64f" if success else "#ff0000"
    emoji = "✅" if success else "❌"
    
    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"{emoji} API Status Change: {endpoint_name} is {status_text}",
                "fields": [
                    {"title": "URL", "value": url, "short": False},
                    {"title": "Status Code", "value": str(status_code) if status_code else "N/A", "short": True},
                    {"title": "Error", "value": error if error else "None", "short": True}
                ],
                "ts": time.time()
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")

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
        slack_webhook = endpoint.get('slack_webhook_url')
        alert_email = endpoint.get('alert_email')
        last_status_success = endpoint.get('last_status_success') # Previous state

        start = time.time()
        error = None
        status_code = None
        success = False

        # Add default browser-like headers if not present
        request_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        if headers:
            request_headers.update(headers)

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(method, url, headers=request_headers, json=body)
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

        # Trigger notification if status changed
        if last_status_success is not None and last_status_success != success:
            if slack_webhook:
                await send_slack_notification(
                    slack_webhook, endpoint['name'], url, success, status_code, error
                )
            if alert_email:
                await send_email_notification(
                    alert_email, endpoint['name'], url, success, status_code, error
                )

        # Update last_checked and last_status_success in endpoint
        await db.monitored_endpoints.update_one(
            {"_id": ObjectId(endpoint_id)},
            {"$set": {
                "last_checked": checked_at,
                "last_status_success": success
            }}
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
    async def get_logs(endpoint_id: str, user_email: str, limit: int = 50):
        # Verify ownership
        await EndpointService.get_endpoint_by_id(endpoint_id, user_email)
        
        logs = await db.monitoring_logs.find(
            {"endpoint_id": endpoint_id}
        ).sort("checked_at", -1).limit(limit).to_list(limit)
        return logs

    @staticmethod
    async def get_stats(endpoint_id: str, user_email: str):
        # Verify ownership
        await EndpointService.get_endpoint_by_id(endpoint_id, user_email)
        
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