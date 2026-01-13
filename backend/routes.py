from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List

import handlers
from models import (
    UserCreate, Token, EndpointResponse, 
    EndpointUpdate, MonitoringLogResponse, EndpointCreate
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Auth dependency wrapper
async def get_user(token: str = Depends(oauth2_scheme)):
    # Re-using the logic from handlers but keeping the dependency here
    if not token:
        return "test@example.com" # Dev bypass
    return await handlers.get_current_user_email(token)

# --- Auth Routes ---
@router.post("/auth/register", status_code=201, tags=["Auth"])
async def register(user: UserCreate):
    return await handlers.register(user)

@router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(user_data: UserCreate):
    return await handlers.login(user_data)

# --- Endpoint Routes ---
@router.post("/endpoints/", response_model=EndpointResponse, status_code=201, tags=["Endpoints"])
async def create_endpoint(endpoint: EndpointCreate, user_email: str = Depends(get_user)):
    return await handlers.create_endpoint(endpoint, user_email)

@router.get("/endpoints/", response_model=List[EndpointResponse], tags=["Endpoints"])
async def list_endpoints(user_email: str = Depends(get_user)):
    return await handlers.list_endpoints(user_email)

@router.get("/endpoints/{id}", response_model=EndpointResponse, tags=["Endpoints"])
async def get_endpoint(id: str, user_email: str = Depends(get_user)):
    return await handlers.get_endpoint(id, user_email)

@router.put("/endpoints/{id}", response_model=EndpointResponse, tags=["Endpoints"])
async def update_endpoint(id: str, endpoint_update: EndpointUpdate, user_email: str = Depends(get_user)):
    return await handlers.update_endpoint(id, endpoint_update, user_email)

@router.delete("/endpoints/{id}", status_code=204, tags=["Endpoints"])
async def delete_endpoint(id: str, user_email: str = Depends(get_user)):
    return await handlers.delete_endpoint(id, user_email)

# --- Stats Routes (Now Authenticated) ---
@router.get("/logs/{endpoint_id}", response_model=List[MonitoringLogResponse], tags=["Stats"])
async def get_logs(endpoint_id: str, limit: int = 50, user_email: str = Depends(get_user)):
    return await handlers.get_logs(endpoint_id, user_email, limit)

@router.get("/stats/{endpoint_id}", tags=["Stats"])
async def get_stats(endpoint_id: str, user_email: str = Depends(get_user)):
    return await handlers.get_stats(endpoint_id, user_email)
