from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime
from ..models import RoleEnum, IncidentStatus

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

class UserResponse(UserBase):
    id: int
    role: RoleEnum
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Login Schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

# Location Schemas
class LocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    building: str = Field(default="-", max_length=120)
    floor: str = Field(default="-", max_length=60)

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Camera Schemas
class CameraBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    status: Literal["active", "offline", "online", "disabled"] = "active"

class CameraCreate(CameraBase):
    location_id: int = Field(gt=0)

class CameraResponse(CameraBase):
    id: int
    location_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Incident Schemas
class IncidentBase(BaseModel):
    event_type: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
    status: IncidentStatus = IncidentStatus.OPEN
    snapshot_path: Optional[str] = Field(default=None, max_length=500)

class IncidentCreate(BaseModel):
    """Operator-filed incident. Only identity + type are client-controlled:
    status is always OPEN and snapshot_path is server-assigned, so a client
    can neither forge resolutions/scores nor plant a filesystem path that a
    later DELETE would remove (stored path traversal)."""
    camera_id: int = Field(gt=0)
    event_type: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)

class IncidentResponse(IncidentBase):
    id: int
    camera_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentUpdate(BaseModel):
    status: IncidentStatus

class DetectionEventResponse(BaseModel):
    id: int
    incident_id: Optional[int] = None
    event_type: str
    value: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentDetail(IncidentResponse):
    events: list["DetectionEventResponse"] = []
