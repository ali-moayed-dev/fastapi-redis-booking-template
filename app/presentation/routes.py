"""FastAPI HTTP endpoints mapping domain results and errors to REST responses."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.cache import CacheBackend
from app.data.database import get_db
from app.domain import booking_service
from app.domain.errors import NotFoundError, SlotConflictError
from app.domain.schemas import (
    BookingCreate,
    BookingRead,
    BookingStatusUpdate,
    ServiceCreate,
    ServiceRead,
)

router = APIRouter()


def _get_cache(request: Request) -> CacheBackend:
    return request.app.state.cache


@router.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok"}


@router.get("/services", response_model=list[ServiceRead], tags=["services"])
def get_services(
    db: Session = Depends(get_db), cache: CacheBackend = Depends(_get_cache)
) -> list[dict]:
    return booking_service.list_services(db, cache)


@router.post(
    "/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    tags=["services"],
)
def post_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    cache: CacheBackend = Depends(_get_cache),
):
    return booking_service.create_service(db, cache, payload)


@router.get("/bookings", response_model=list[BookingRead], tags=["bookings"])
def get_bookings(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    cache: CacheBackend = Depends(_get_cache),
) -> list[dict]:
    return booking_service.list_bookings(db, cache, limit)


@router.post(
    "/bookings",
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bookings"],
)
def post_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    cache: CacheBackend = Depends(_get_cache),
):
    try:
        return booking_service.create_booking(db, cache, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SlotConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch(
    "/bookings/{booking_id}/status", response_model=BookingRead, tags=["bookings"]
)
def patch_booking_status(
    booking_id: int,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
    cache: CacheBackend = Depends(_get_cache),
):
    try:
        return booking_service.update_booking_status(db, cache, booking_id, payload.status)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
