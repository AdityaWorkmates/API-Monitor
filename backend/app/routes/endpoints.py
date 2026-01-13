from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from bson import ObjectId
from app.database import db
from app.schemas import EndpointCreate, EndpointResponse, EndpointUpdate
from app.scheduler import add_job, remove_job

router = APIRouter()

@router.post("/", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(endpoint: EndpointCreate):
    endpoint_dict = endpoint.model_dump()
    endpoint_dict["created_at"] = endpoint_dict.get("created_at")  # Should be handled by default factory in schema if needed, but model_dump might need help or we let DB handle it? 
    # Actually schema has default factory for response, but for creation we insert.
    # We should let python handle datetime.
    from datetime import datetime
    endpoint_dict["created_at"] = datetime.utcnow()
    endpoint_dict["last_checked"] = None
    
    new_endpoint = await db.monitored_endpoints.insert_one(endpoint_dict)
    created_endpoint = await db.monitored_endpoints.find_one({"_id": new_endpoint.inserted_id})
    
    if created_endpoint["is_active"]:
        add_job(created_endpoint)
        
    return created_endpoint

@router.get("/", response_model=List[EndpointResponse])
async def list_endpoints():
    endpoints = await db.monitored_endpoints.find().to_list(1000)
    return endpoints

@router.get("/{id}", response_model=EndpointResponse)
async def get_endpoint(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    endpoint = await db.monitored_endpoints.find_one({"_id": ObjectId(id)})
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint

@router.put("/{id}", response_model=EndpointResponse)
async def update_endpoint(id: str, endpoint_update: EndpointUpdate):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Filter out None values
    update_data = {k: v for k, v in endpoint_update.model_dump().items() if v is not None}
    
    if len(update_data) >= 1:
        update_result = await db.monitored_endpoints.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )
        if update_result.matched_count == 0:
             raise HTTPException(status_code=404, detail="Endpoint not found")

    updated_endpoint = await db.monitored_endpoints.find_one({"_id": ObjectId(id)})
    
    # Update scheduler
    if updated_endpoint["is_active"]:
        add_job(updated_endpoint)
    else:
        remove_job(str(updated_endpoint["_id"]))
        
    return updated_endpoint

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    delete_result = await db.monitored_endpoints.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        remove_job(id)
    else:
        raise HTTPException(status_code=404, detail="Endpoint not found")
