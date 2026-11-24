"""Unit tests for cache backend, schemas, and booking service."""

from datetime import datetime, timezone
import unittest

from pydantic import ValidationError

from app.core.cache import InMemoryCache
from app.domain.schemas import BookingCreate, ServiceCreate


class CacheAndSchemaTests(unittest.TestCase):
    """Verify cache invalidation and schema validation without external services."""

    def test_in_memory_cache_set_get_and_prefix_invalidation(self) -> None:
        cache = InMemoryCache()
        cache.set_json("bookings:list:50", [{"id": 1}], ttl_seconds=60)
        cache.set_json("services:active", [{"id": 2}], ttl_seconds=60)

        self.assertEqual(cache.get_json("bookings:list:50"), [{"id": 1}])
        cache.delete_prefix("bookings:")
        self.assertIsNone(cache.get_json("bookings:list:50"))
        self.assertEqual(cache.get_json("services:active"), [{"id": 2}])

    def test_service_and_booking_schema_validation(self) -> None:
        svc = ServiceCreate(name="Standard Inspection", duration_minutes=30, price_cents=2500)
        self.assertEqual(svc.duration_minutes, 30)

        booking = BookingCreate(
            service_id=1,
            customer_name="Sample Client",
            scheduled_at=datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(booking.service_id, 1)

        with self.assertRaises(ValidationError):
            ServiceCreate(name="X", duration_minutes=0, price_cents=-1)


if __name__ == "__main__":
    unittest.main()
