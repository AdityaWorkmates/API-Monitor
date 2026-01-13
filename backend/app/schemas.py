from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, Annotated
from datetime import datetime

# Helper for handling MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]

class EndpointBase(BaseModel):
    name: str = Field(..., min_length=1)
    url: str = Field(..., pattern="^https?://")
    method: str = "GET"
    interval: int = Field(60, ge=10)  # Minimum 10 seconds
    timeout: int = Field(5, ge=1)
    is_active: bool = True

class EndpointCreate(EndpointBase):
    pass

class EndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    interval: Optional[int] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None

class EndpointResponse(EndpointBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    current_status: Optional[str] = None
    last_response_time: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class MonitoringLogBase(BaseModel):
    endpoint_id: str
    status_code: Optional[int] = None
    response_time_ms: int
    success: bool
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)

class MonitoringLogResponse(MonitoringLogBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
