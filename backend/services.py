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

    status_text = "RECOVERED" if success else "CRITICAL"
    status_color = "#10b981" if success else "#ef4444"
    subject = f"[{status_text}] API Status Alert: {endpoint_name}"
    
    body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;">
            <div style="background-color: {status_color}; padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 2px;">API {status_text}</h1>
            </div>
            <div style="padding: 40px;">
                <p style="font-size: 16px; color: #4b5563; margin-top: 0;">Hello,</p>
                <p style="font-size: 16px; color: #4b5563;">The status of your monitored endpoint <strong>{endpoint_name}</strong> has changed to <span style="color: {status_color}; font-weight: bold;">{status_text}</span>.</p>
                
                <div style="background-color: #f9fafb; border-radius: 12px; padding: 25px; margin: 30px 0; border: 1px solid #f3f4f6;">
                    <div style="margin-bottom: 15px;">
                        <span style="font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: bold; display: block;">Target URL</span>
                        <a href="{url}" style="font-size: 15px; color: #4f46e5; text-decoration: none; word-break: break-all;">{url}</a>
                    </div>
                    <div style="grid-template-cols: 1fr 1fr; display: grid; gap: 20px;">
                        <div>
                            <span style="font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: bold; display: block;">Status Code</span>
                            <span style="font-size: 15px; color: #1f2937; font-weight: bold;">{status_code if status_code else 'N/A'}</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: bold; display: block;">Check Time</span>
                            <span style="font-size: 15px; color: #1f2937;">{datetime.utcnow().strftime('%H:%M:%S')} UTC</span>
                        </div>
                    </div>
                    {f'<div style="margin-top: 15px; border-top: 1px solid #e5e7eb; padding-top: 15px;"><span style="font-size: 12px; color: #ef4444; text-transform: uppercase; font-weight: bold; display: block;">Error Detail</span><span style="font-size: 14px; color: #ef4444; font-family: monospace;">{error}</span></div>' if error else ''}
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <a href="http://localhost:5173" style="background-color: #4f46e5; color: #ffffff; padding: 14px 30px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 16px; display: inline-block;">View Dashboard</a>
                </div>
            </div>
            <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #9ca3af; margin: 0;">API Monitor - Real-time Status Tracking</p>
            </div>
        </div>
    </body>
    </html>
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
                print(f"Successfully sent status email to {to_email} for {endpoint_name}")
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
            print(f"Successfully sent Slack notification for {endpoint_name}")
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

        start = time.time()
        error = None
        status_code = None
        success = False

        # Browser-like headers
        request_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        if headers:
            request_headers.update(headers)

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(method, url, headers=request_headers, json=body)
                status_code = response.status_code
                success = 200 <= response.status_code < 300
        except httpx.TimeoutException:
            error = "Timeout"
        except httpx.RequestError as e:
            error = str(e)
        except Exception as e:
            error = str(e)

        # Failure = 0ms response time for graph cleanliness
        response_time = int((time.time() - start) * 1000) if success else 0
        checked_at = datetime.utcnow()

        # Log current result
        log_entry = {
            "endpoint_id": str(endpoint_id),
            "status_code": status_code,
            "response_time_ms": response_time,
            "success": success,
            "error": error,
            "checked_at": checked_at
        }
        await db.monitoring_logs.insert_one(log_entry)

        # Threshold Calculation (4 out of last 5)
        last_logs = await db.monitoring_logs.find(
            {"endpoint_id": str(endpoint_id)}
        ).sort("checked_at", -1).limit(5).to_list(5)
        
        failure_count = sum(1 for log in last_logs if not log['success'])
        currently_threshold_down = failure_count >= 4
        prev_threshold_down = endpoint.get('is_threshold_down', False)

        if currently_threshold_down and not prev_threshold_down:
            # Transition to DOWN
            if slack_webhook: await send_slack_notification(slack_webhook, endpoint['name'], url, False, status_code, error)
            if alert_email: await send_email_notification(alert_email, endpoint['name'], url, False, status_code, error)
        elif not currently_threshold_down and prev_threshold_down:
            # Transition to UP (Recovery)
            if slack_webhook: await send_slack_notification(slack_webhook, endpoint['name'], url, True, status_code, error)
            if alert_email: await send_email_notification(alert_email, endpoint['name'], url, True, status_code, error)

        # Update Database
        await db.monitored_endpoints.update_one(
            {"_id": ObjectId(endpoint_id)},
            {"$set": {
                "last_checked": checked_at,
                "last_status_success": success,
                "is_threshold_down": currently_threshold_down
            }}
        )

    except Exception as e:
        print(f"Critical error in perform_check for {endpoint_id}: {e}")

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
        endpoint_dict["last_status_success"] = None
        endpoint_dict["is_threshold_down"] = False
        
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
