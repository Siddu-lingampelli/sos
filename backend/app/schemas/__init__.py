from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
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
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: RoleEnum
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Login Schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Location Schemas
class LocationBase(BaseModel):
    name: str
    building: str
    floor: str

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Camera Schemas
class CameraBase(BaseModel):
    name: str
    status: str = "active"

class CameraCreate(CameraBase):
    location_id: int

class CameraResponse(CameraBase):
    id: int
    location_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Incident Schemas
class IncidentBase(BaseModel):
    event_type: str
    confidence: float
    status: IncidentStatus = IncidentStatus.OPEN
    snapshot_path: Optional[str] = None

class IncidentCreate(IncidentBase):
    camera_id: int

class IncidentResponse(IncidentBase):
    id: int
    camera_id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
