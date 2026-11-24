# FastAPI + Redis Booking Template

Clean, modular backend boilerplate demonstrating **FastAPI**, **SQLAlchemy 2.0**, **MySQL**, **Redis Cache-Aside**, and **Docker Compose** for time-slot booking APIs.

## Architecture

- `app/core`: Environment configuration and `CacheBackend` abstraction (`RedisCache` with non-blocking `SCAN` + `UNLINK` prefix invalidation + `InMemoryCache` for unit tests).
- `app/data`: SQLAlchemy engine, session lifecycle, and relational models with composite indexing on `(service_id, scheduled_at)`.
- `app/domain`: Pydantic v2 schemas, domain errors (`NotFoundError`, `SlotConflictError`), and booking/cache-invalidation business logic.
- `app/presentation`: FastAPI `APIRouter` mapping domain outcomes to REST status codes (`200`, `201`, `404`, `409`).

## Caching & Conflict Handling

1. `GET /services` and `GET /bookings` use **Cache-Aside**: check Redis first, query MySQL on cache miss, and populate TTL keys (`CACHE_TTL_SECONDS`).
2. `POST /services`, `POST /bookings`, and `PATCH /bookings/{id}/status` write atomically to MySQL and invalidate the affected Redis key prefix.
3. `POST /bookings` checks overlapping duration windows for active bookings and returns `409 Conflict` to prevent double-booking.

## Quick Start (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service liveness probe |
| `GET` | `/services` | List active services (cached) |
| `POST` | `/services` | Create a service & invalidate cache |
| `GET` | `/bookings` | List recent bookings (cached) |
| `POST` | `/bookings` | Book a time slot with conflict check |
| `PATCH` | `/bookings/{id}/status` | Update booking status & invalidate cache |

## Testing

```bash
python -m unittest discover -s tests
```
