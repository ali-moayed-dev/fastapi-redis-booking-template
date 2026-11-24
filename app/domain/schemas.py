"""Pydantic request and response schemas for services and bookings."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


BookingStatus = Literal["pending", "confirmed", "cancelled"]


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    duration_minutes: int = Field(gt=0, le=480)
    price_cents: int = Field(ge=0)


class ServiceRead(ServiceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class BookingCreate(BaseModel):
    service_id: int = Field(gt=0)
    customer_name: str = Field(min_length=2, max_length=120)
    scheduled_at: datetime


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_id: int
    customer_name: str
    scheduled_at: datetime
    status: BookingStatus
    created_at: datetime
