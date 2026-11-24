"""Relational ORM models for services and time-slot bookings."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ServiceModel(Base):
    """Bookable service catalog item."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    bookings: Mapped[list["BookingModel"]] = relationship(back_populates="service")


class BookingModel(Base):
    """Customer reservation linked to a service and scheduled time."""

    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_service_slot", "service_id", "scheduled_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    service: Mapped[ServiceModel] = relationship(back_populates="bookings")
