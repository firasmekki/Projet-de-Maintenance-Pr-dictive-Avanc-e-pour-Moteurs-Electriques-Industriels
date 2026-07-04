"""
API tests for prediction endpoints.
Uses SQLite in-memory DB via the conftest.py fixtures.
Motor and sensor seed data are created per-test.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _seed_motor(db: Session) -> UUID:
    from app.db.models.motor import Motor
    motor = Motor(
        name="Test Motor M5",
        manufacturer="ORBIT",
        model="OM-400",
        rated_power_kw=Decimal("7.5"),
        rated_voltage=Decimal("380.00"),
        rated_current=Decimal("18.00"),
        rpm=1450,
        location="Test Bay",
        status="active",
    )
    db.add(motor)
    db.commit()
    db.refresh(motor)
    return motor.id  # UUID object


def _seed_sensor(db: Session, motor_id: UUID, **overrides) -> None:
    from app.db.models.sensor_data import SensorData
    defaults: dict = dict(
        motor_id=motor_id,
        temperature=Decimal("70.000"),
        vibration=Decimal("3.500"),
        current=Decimal("15.500"),
        voltage=Decimal("380.000"),
        power=Decimal("5600.000"),
        power_factor=Decimal("0.870"),
        thd=Decimal("3.500"),
        load=Decimal("77.000"),
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    record = SensorData(**defaults)
    db.add(record)
    db.commit()


class TestPredictEndpoint:

    def test_returns_404_for_unknown_motor(self, client: TestClient) -> None:
        response = client.post(f"/api/v1/predict/{uuid4()}")
        assert response.status_code == 404

    def test_returns_404_when_no_sensor_data(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        response = client.post(f"/api/v1/predict/{motor_id}")
        assert response.status_code == 404

    def test_returns_200_with_valid_motor_and_sensor(
        self, client: TestClient, db_session: Session
    ) -> None:
        motor_id = _seed_motor(db_session)
        for _ in range(5):
            _seed_sensor(db_session, motor_id)

        response = client.post(f"/api/v1/predict/{motor_id}")
        assert response.status_code == 200

    def test_response_schema(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}").json()

        assert "motor_id" in data
        assert "prediction_id" in data
        assert "predicted_at" in data
        assert "anomaly" in data
        assert "fault_classification" in data
        assert "health" in data
        assert "risk" in data
        assert "model_version" in data

    def test_anomaly_fields(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}").json()["anomaly"]
        assert isinstance(data["anomaly"], bool)
        assert 0.0 <= data["score"] <= 1.0

    def test_health_fields(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}").json()["health"]
        assert 0.0 <= data["health_score"] <= 100.0
        assert data["status"] in {"Healthy", "Warning", "Critical"}

    def test_risk_fields(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}").json()["risk"]
        assert 0.0 <= data["risk_7d"] <= 1.0
        assert 0.0 <= data["risk_30d"] <= 1.0
        assert data["risk_level"] in {"Low", "Medium", "High", "Critical"}

    def test_fault_classification_fields(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}").json()["fault_classification"]
        assert "fault" in data
        assert "confidence" in data
        assert "all_probabilities" in data
        assert 0.0 <= data["confidence"] <= 100.0

    def test_include_features_flag(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}", json={"include_features": True}).json()
        assert data["features"] is not None
        assert "temperature" in data["features"]

    def test_exclude_features_by_default(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        data = client.post(f"/api/v1/predict/{motor_id}").json()
        assert data["features"] is None

    def test_invalid_motor_id_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/predict/not-a-uuid")
        assert response.status_code == 422

    def test_prediction_persisted_to_db(self, client: TestClient, db_session: Session) -> None:
        from sqlalchemy import select
        from app.db.models.prediction_history import PredictionHistory

        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        client.post(f"/api/v1/predict/{motor_id}")

        count = db_session.scalar(
            select(PredictionHistory).where(PredictionHistory.motor_id == motor_id)
            .with_only_columns(PredictionHistory.id)
        )
        # Just verify a record was created (scalar returns the id if exists)
        records = db_session.scalars(
            select(PredictionHistory).where(PredictionHistory.motor_id == motor_id)
        ).all()
        assert len(records) == 1


class TestPredictionsListEndpoint:

    def test_returns_404_for_unknown_motor(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/motors/{uuid4()}/predictions")
        assert response.status_code == 404

    def test_returns_empty_list_before_predictions(
        self, client: TestClient, db_session: Session
    ) -> None:
        motor_id = _seed_motor(db_session)
        data = client.get(f"/api/v1/motors/{motor_id}/predictions").json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_returns_prediction_after_predict(
        self, client: TestClient, db_session: Session
    ) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        client.post(f"/api/v1/predict/{motor_id}")
        data = client.get(f"/api/v1/motors/{motor_id}/predictions").json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        record = data["items"][0]
        assert record["motor_id"] == str(motor_id)
        assert "health_score" in record
        assert "risk_score_7d" in record
        assert "anomaly_detected" in record

    def test_pagination_params(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        response = client.get(
            f"/api/v1/motors/{motor_id}/predictions",
            params={"limit": 10, "skip": 0},
        )
        assert response.status_code == 200

    def test_invalid_limit_returns_422(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        response = client.get(
            f"/api/v1/motors/{motor_id}/predictions",
            params={"limit": 0},
        )
        assert response.status_code == 422


class TestRiskEndpoint:

    def test_returns_404_for_unknown_motor(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/motors/{uuid4()}/risk")
        assert response.status_code == 404

    def test_returns_default_when_no_predictions(
        self, client: TestClient, db_session: Session
    ) -> None:
        motor_id = _seed_motor(db_session)
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()

        assert data["current_health_score"] == 100.0
        assert data["risk_level"] == "Low"
        assert data["last_predicted_at"] is None
        assert len(data["recommendations"]) >= 1

    def test_response_schema(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()

        assert "motor_id" in data
        assert "current_health_score" in data
        assert "risk_7d" in data
        assert "risk_30d" in data
        assert "risk_level" in data
        assert "trend" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_trend_is_valid(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()
        assert data["trend"] in {"Improving", "Stable", "Degrading"}

    def test_risk_level_is_valid(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()
        assert data["risk_level"] in {"Low", "Medium", "High", "Critical"}

    def test_risk_after_prediction(self, client: TestClient, db_session: Session) -> None:
        motor_id = _seed_motor(db_session)
        _seed_sensor(db_session, motor_id)

        client.post(f"/api/v1/predict/{motor_id}")
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()

        assert data["last_predicted_at"] is not None
        assert 0.0 <= data["risk_7d"] <= 1.0
        assert 0.0 <= data["risk_30d"] <= 1.0
