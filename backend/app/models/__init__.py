from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum
)
from sqlalchemy.orm import relationship
from ..db.session import Base

class RoleEnum(str, PyEnum):
    ADMIN = "ADMIN"
    SECURITY_OFFICER = "SECURITY_OFFICER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.SECURITY_OFFICER)
    is_active = Column(Boolean, default=True)

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    building = Column(String)
    floor = Column(String)

    cameras = relationship("Camera", back_populates="location")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    status = Column(String, default="active")

    location = relationship("Location", back_populates="cameras")
    incidents = relationship("Incident", back_populates="camera")

class IncidentStatus(str, PyEnum):
    OPEN = "OPEN"
    VERIFIED = "VERIFIED"
    DISMISSED = "DISMISSED"
    UNDER_REVIEW = "UNDER_REVIEW"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    event_type = Column(String) # e.g. "Fall + Inactivity"
    confidence = Column(Float)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN)
    snapshot_path = Column(String, nullable=True)

    camera = relationship("Camera", back_populates="incidents")
    events = relationship("DetectionEvent", back_populates="incident")
    alerts = relationship("Alert", back_populates="incident")

class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    event_type = Column(String) # "FALL", "DISTRESS_KEYWORD"
    value = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="events")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    channel = Column(String) # "websocket", "email"
    status = Column(String) # "sent", "failed"
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="alerts")
