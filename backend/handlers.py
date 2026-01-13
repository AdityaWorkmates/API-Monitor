from fastapi import HTTPException, status, Depends
from typing import List
from jose import JWTError, jwt

from config import settings
from models import (
    UserCreate, Token, EndpointCreate, EndpointResponse, 
    EndpointUpdate, MonitoringLogResponse
)
from services import AuthService, EndpointService

# --- Dependencies ---
async def get_current_user_email(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception

# --- Auth Handlers ---
async def register(user: UserCreate):
    await AuthService.create_user(user.email, user.password)
    return {"message": "User created successfully"}

async def login(user_data: UserCreate):
    return await AuthService.authenticate_user(user_data.email, user_data.password)

# --- Endpoint Handlers ---
async def create_endpoint(endpoint: EndpointCreate, user_email: str):
    return await EndpointService.create_endpoint(endpoint, user_email)

async def list_endpoints(user_email: str):
    return await EndpointService.get_endpoints(user_email)

async def get_endpoint(id: str, user_email: str):
    return await EndpointService.get_endpoint_by_id(id, user_email)

async def update_endpoint(id: str, endpoint_update: EndpointUpdate, user_email: str):
    return await EndpointService.update_endpoint(id, endpoint_update, user_email)

async def delete_endpoint(id: str, user_email: str):
    await EndpointService.delete_endpoint(id, user_email)

# --- Stats Handlers ---
async def get_logs(endpoint_id: str, user_email: str, limit: int = 50):
    return await EndpointService.get_logs(endpoint_id, user_email, limit)

async def get_stats(endpoint_id: str, user_email: str):
    return await EndpointService.get_stats(endpoint_id, user_email)