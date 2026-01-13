from fastapi import APIRouter, HTTPException, status, Depends, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta
from jose import JWTError, jwt

from config import settings
from models import (
    UserCreate, Token, EndpointCreate, EndpointResponse, 
    EndpointUpdate, MonitoringLogResponse
)
from services import AuthService, EndpointService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# --- Dependencies ---
async def get_current_user_email(token: str = Depends(oauth2_scheme)):
    # Development bypass: If no token is provided, return a default test user
    if not token:
        # In a real prod env, you might strictly enforce this:
        # raise HTTPException(status_code=401, detail="Not authenticated")
        return "test@example.com"

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

# --- Auth Routes ---
@router.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user: UserCreate):
    await AuthService.create_user(user.email, user.password)
    return {"message": "User created successfully"}

@router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await AuthService.get_user_by_email(form_data.username)
    if not user or not AuthService.verify_password(form_data.password, user["password"]):
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

# --- Endpoint Routes ---
@router.post("/endpoints/", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED, tags=["Endpoints"])
async def create_endpoint(
    endpoint: EndpointCreate, 
    user_email: str = Depends(get_current_user_email)
):
    return await EndpointService.create_endpoint(endpoint, user_email)

@router.get("/endpoints/", response_model=List[EndpointResponse], tags=["Endpoints"])
async def list_endpoints(user_email: str = Depends(get_current_user_email)):
    return await EndpointService.get_endpoints(user_email)

@router.get("/endpoints/{id}", response_model=EndpointResponse, tags=["Endpoints"])
async def get_endpoint(id: str, user_email: str = Depends(get_current_user_email)):
    return await EndpointService.get_endpoint_by_id(id, user_email)

@router.put("/endpoints/{id}", response_model=EndpointResponse, tags=["Endpoints"])
async def update_endpoint(
    id: str, 
    endpoint_update: EndpointUpdate,
    user_email: str = Depends(get_current_user_email)
):
    return await EndpointService.update_endpoint(id, endpoint_update, user_email)

@router.delete("/endpoints/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Endpoints"])
async def delete_endpoint(id: str, user_email: str = Depends(get_current_user_email)):
    await EndpointService.delete_endpoint(id, user_email)

# --- Stats Routes ---
@router.get("/stats/logs/{endpoint_id}", response_model=List[MonitoringLogResponse], tags=["Stats"])
async def get_logs(endpoint_id: str, limit: int = 50):
    return await EndpointService.get_logs(endpoint_id, limit)

@router.get("/stats/stats/{endpoint_id}", tags=["Stats"])
async def get_stats(endpoint_id: str):
    return await EndpointService.get_stats(endpoint_id)
