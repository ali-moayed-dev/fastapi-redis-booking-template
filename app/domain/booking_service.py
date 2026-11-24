"""Booking and service use cases with Cache-Aside Redis caching."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import CacheBackend
from app.core.config import settings
from app.data.models import BookingModel, ServiceModel
from app.domain.errors import NotFoundError, SlotConflictError
from app.domain.schemas import BookingCreate, BookingRead, ServiceCreate, ServiceRead

SERVICES_CACHE_KEY = "services:active"
BOOKINGS_CACHE_PREFIX = "bookings:"


def list_services(db: Session, cache: CacheBackend) -> list[dict]:
    """Return active services using Cache-Aside lookup."""
    cached = cache.get_json(SERVICES_CACHE_KEY)
    if cached is not None:
        return cached
    rows = db.scalars(select(ServiceModel).where(ServiceModel.is_active.is_(True))).all()
    payload = [ServiceRead.model_validate(row).model_dump(mode="json") for row in rows]
    cache.set_json(SERVICES_CACHE_KEY, payload, settings.cache_ttl_seconds)
    return payload


def create_service(db: Session, cache: CacheBackend, data: ServiceCreate) -> ServiceModel:
    """Create a service and invalidate the active services cache."""
    service = ServiceModel(**data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    cache.delete_prefix("services:")
    return service


def _has_slot_conflict(db: Session, service: ServiceModel, start_at) -> bool:
    """Detect active booking overlap against service duration."""
    end_at = start_at + timedelta(minutes=service.duration_minutes)
    existing = db.scalars(
        select(BookingModel).where(
            BookingModel.service_id == service.id,
            BookingModel.status != "cancelled",
        )
    ).all()
    for booking in existing:
        b_end = booking.scheduled_at + timedelta(minutes=service.duration_minutes)
        if booking.scheduled_at < end_at and start_at < b_end:
            return True
    return False


def create_booking(db: Session, cache: CacheBackend, data: BookingCreate) -> BookingModel:
    """Create a non-overlapping booking and invalidate booking list cache."""
    service = db.get(ServiceModel, data.service_id)
    if service is None or not service.is_active:
        raise NotFoundError(f"Service {data.service_id} not found")
    if _has_slot_conflict(db, service, data.scheduled_at):
        raise SlotConflictError("Requested time slot is already booked")
    booking = BookingModel(**data.model_dump(), status="pending")
    db.add(booking)
    db.commit()
    db.refresh(booking)
    cache.delete_prefix(BOOKINGS_CACHE_PREFIX)
    return booking


def list_bookings(db: Session, cache: CacheBackend, limit: int = 50) -> list[dict]:
    """Return recent bookings using Cache-Aside lookup."""
    cache_key = f"{BOOKINGS_CACHE_PREFIX}list:{limit}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached
    rows = db.scalars(
        select(BookingModel).order_by(BookingModel.scheduled_at.desc()).limit(limit)
    ).all()
    payload = [BookingRead.model_validate(row).model_dump(mode="json") for row in rows]
    cache.set_json(cache_key, payload, settings.cache_ttl_seconds)
    return payload


def update_booking_status(
    db: Session, cache: CacheBackend, booking_id: int, status: str
) -> BookingModel:
    """Update booking status and invalidate cached booking lists."""
    booking = db.get(BookingModel, booking_id)
    if booking is None:
        raise NotFoundError(f"Booking {booking_id} not found")
    booking.status = status
    db.commit()
    db.refresh(booking)
    cache.delete_prefix(BOOKINGS_CACHE_PREFIX)
    return booking
