# ORBIT AI Industrial Copilot - Backend

## Architecture

- `app/main.py`: FastAPI application factory, middleware, exception handlers, router registration.
- `app/core/config.py`: environment-driven settings using Pydantic Settings.
- `app/core/logging.py`: structured JSON logging for containers and production observability.
- `app/dependencies.py`: dependency injection entry points.
- `app/api/v1`: versioned REST API routing.
- `app/schemas`: Pydantic response/request schemas.
- `app/services`: application services for motor monitoring and health scoring.
- `app/db`: SQLAlchemy base, engine/session management, and ORM models.
- `app/repositories`: repository pattern implementations for persistence access.
- `alembic`: database migration environment and revision files.
- `scripts/seed_data.py`: deterministic industrial motor telemetry seed script.
- `tests`: unit tests for foundational behavior.

## Database Relationships

- `motors` has many `sensor_data` rows.
- `motors` has many `fault_history` rows.
- `motors` has many `maintenance_history` rows.
- `motors` has many `recommendations` rows.
- Child records use `ON DELETE CASCADE`, so deleting a motor removes its related telemetry, faults, maintenance records, and recommendations.

## Run Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python scripts/seed_data.py --reset
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- Health: `http://127.0.0.1:8000/health`
- API health: `http://127.0.0.1:8000/api/v1/health`
- Docs: `http://127.0.0.1:8000/docs`

## Monitoring APIs

- `GET /api/v1/motors`
- `GET /api/v1/motors/{motor_id}`
- `GET /api/v1/motors/{motor_id}/sensor-data`
- `GET /api/v1/motors/{motor_id}/latest`
- `GET /api/v1/motors/{motor_id}/health`

## Diagnostic APIs

- `POST /api/v1/diagnose/{motor_id}`: runs rule-based diagnosis and stores a fault history record when a fault is detected.
- `GET /api/v1/motors/{motor_id}/faults`: returns persisted fault history.
- `GET /api/v1/motors/{motor_id}/diagnosis`: runs current diagnosis without storing a new fault.

Supported rule-based faults:

- Bearing Wear
- Misalignment
- Unbalance
- Rotor Fault
- Insulation Fault
- Overload

Trend analysis evaluates temperature, vibration, and current across:

- last 24 hours
- last 7 days
- last 30 days

Trend indicators are `RISING`, `STABLE`, and `FALLING`.

The temporary health score starts at 100 and applies penalties:

- temperature above 90 C: `-20`
- vibration above 7 mm/s: `-20`
- current above rated current: `-15`

Score status:

- `80-100`: Healthy
- `60-79`: Warning
- `0-59`: Critical

## Run Tests

```bash
cd backend
pytest
```

Repository tests use an in-memory SQLAlchemy database and do not require PostgreSQL.

## Seed Data

The default seed creates 10 motors and 10,200 sensor records:

```bash
cd backend
python scripts/seed_data.py --reset
```

Customize volume:

```bash
cd backend
python scripts/seed_data.py --motors 10 --days 30 --readings-per-day 34 --reset
```

Without `--reset`, the script skips seeding when the target volume already exists.

## Migrations

Create a migration after model changes:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
cd backend
alembic upgrade head
```

Rollback one migration:

```bash
cd backend
alembic downgrade -1
```

## Docker

```bash
docker compose up --build
```

The Compose stack starts PostgreSQL 16, waits for it to become healthy, applies Alembic migrations, then starts FastAPI.

Populate the Docker database:

```bash
docker compose exec backend python scripts/seed_data.py --reset
```

## Testing Fault Scenarios

Use the generated tests as executable examples:

```bash
cd backend
python -m pytest tests/test_fault_scoring_service.py
python -m pytest tests/test_trend_analysis_service.py
python -m pytest tests/test_diagnostic_api.py
```

The fault scoring tests create sensor snapshots for each diagnostic matrix case:

- Bearing Wear: high vibration, high temperature, medium current.
- Misalignment: very high vibration, medium temperature, normal current.
- Unbalance: high vibration, normal temperature, normal current.
- Rotor Fault: high current, medium vibration, medium temperature.
- Insulation Fault: high temperature, low vibration, high current.
- Overload: very high current, high temperature, high load.
