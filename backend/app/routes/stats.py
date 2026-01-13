from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId
from app.database import db
from app.schemas import MonitoringLogResponse

router = APIRouter()

@router.get("/logs/{endpoint_id}", response_model=List[MonitoringLogResponse])
async def get_logs(endpoint_id: str, limit: int = 50):
    if not ObjectId.is_valid(endpoint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    logs = await db.monitoring_logs.find(
        {"endpoint_id": endpoint_id}
    ).sort("checked_at", -1).limit(limit).to_list(limit)
    
    return logs

@router.get("/stats/{endpoint_id}")
async def get_stats(endpoint_id: str):
    if not ObjectId.is_valid(endpoint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Simple aggregation
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
