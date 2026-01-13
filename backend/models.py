from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, BeforeValidator, EmailStr, ConfigDict, computed_field
from typing import Optional, Annotated, Dict, Any, List
from datetime import datetime
from config import settings

# --- Database Connection ---
client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

async def get_database():
    return db

# --- Models / Schemas ---
# Helper for handling MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]

# User & Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Endpoints
class EndpointBase(BaseModel):
    name: str = Field(..., min_length=1)
    url: str = Field(..., pattern="^https?://")
    method: str = "GET"
    interval: int = Field(60, ge=10)
    timeout: int = Field(5, ge=1)
    is_active: bool = True
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    
class EndpointCreate(EndpointBase):
    pass

class EndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    interval: Optional[int] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None

class EndpointResponse(EndpointBase):
    id: PyObjectId = Field(validation_alias="_id")
    owner_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None

    @computed_field
    @property
    def _id(self) -> str:
        return self.id

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

# Monitoring Logs
class MonitoringLogBase(BaseModel):
    endpoint_id: str
    status_code: Optional[int] = None
    response_time_ms: int
    success: bool
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)

class MonitoringLogResponse(MonitoringLogBase):
    id: PyObjectId = Field(validation_alias="_id")

    @computed_field
    @property
    def _id(self) -> str:
        return self.id

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
