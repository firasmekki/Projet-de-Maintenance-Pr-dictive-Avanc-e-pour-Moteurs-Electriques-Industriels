"""
API tests for prediction routes.

Uses FastAPI TestClient with dependency overrides — no live DB required.

Run with:
    pytest tests/api/ -v
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database.connection import get_session
from app.routes.predictions import router
from app.schemas.prediction import (
    AnomalyResult,
    FaultClassificationResult,
    HealthPredictionResult,
    PredictionHistoryRecord,
    PredictionListResponse,
    PredictionResponse,
    RiskPredictionResult,
    RiskResponse,
)
from app.services.ml.prediction_service import PredictionService


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def _prediction_response(motor_id: UUID) -> PredictionResponse:
    return PredictionResponse(
        motor_id=motor_id,
        prediction_id=uuid4(),
        prediction_date=datetime.utcnow(),
        anomaly=AnomalyResult(anomaly=False, score=0.12),
        fault_classification=FaultClassificationResult(
            fault="Normal",
            confidence=87.5,
            all_probabilities={"Normal": 87.5, "Bearing Wear": 12.5},
        ),
        health=HealthPredictionResult(health_score=85.0, status="Healthy"),
        risk=RiskPredictionResult(risk_7d=0.04, risk_30d=0.08, risk_level="Low"),
        features=None,
        model_version="1.0.0",
    )


def _risk_response(motor_id: UUID) -> RiskResponse:
    return RiskResponse(
        motor_id=motor_id,
        current_health_score=85.0,
        risk_7d=0.04,
        risk_30d=0.08,
        risk_level="Low",
        trend="Stable",
        last_prediction=datetime.utcnow(),
        recommendations=["Motor operating within normal parameters"],
    )


def _list_response(motor_id: UUID) -> PredictionListResponse:
    record = PredictionHistoryRecord(
        id=uuid4(),
        motor_id=motor_id,
        predicted_fault=None,
        confidence=87.5,
        health_score=85.0,
        health_status="Healthy",
        risk_score_7d=0.04,
        risk_score_30d=0.08,
        anomaly_detected=False,
        anomaly_score=0.12,
        model_version="1.0.0",
        prediction_date=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    return PredictionListResponse(motor_id=motor_id, total=1, predictions=[record])


@pytest.fixture
def motor_id() -> UUID:
    return uuid4()


@pytest.fixture
def client(motor_id: UUID) -> TestClient:
    app = _build_app()

    mock_service = MagicMock(spec=PredictionService)
    mock_service.predict = AsyncMock(return_value=_prediction_response(motor_id))
    mock_service.get_predictions = AsyncMock(return_value=_list_response(motor_id))
    mock_service.get_risk = AsyncMock(return_value=_risk_response(motor_id))

    async def _override_session():
        yield AsyncMock()

    def _override_service(session=None):
        return mock_service

    app.dependency_overrides[get_session] = _override_session

    from app.routes.predictions import _get_prediction_service
    app.dependency_overrides[_get_prediction_service] = _override_service

    return TestClient(app)


class TestPredictEndpoint:

    def test_predict_returns_200(self, client: TestClient, motor_id: UUID) -> None:
        response = client.post(f"/api/v1/predict/{motor_id}")
        assert response.status_code == 200

    def test_predict_response_schema(self, client: TestClient, motor_id: UUID) -> None:
        data = client.post(f"/api/v1/predict/{motor_id}").json()
        assert "motor_id" in data
        assert "anomaly" in data
        assert "fault_classification" in data
        assert "health" in data
        assert "risk" in data
        assert "model_version" in data

    def test_predict_anomaly_fields(self, client: TestClient, motor_id: UUID) -> None:
        anomaly = client.post(f"/api/v1/predict/{motor_id}").json()["anomaly"]
        assert "anomaly" in anomaly
        assert "score" in anomaly
        assert isinstance(anomaly["anomaly"], bool)
        assert 0.0 <= anomaly["score"] <= 1.0

    def test_predict_health_fields(self, client: TestClient, motor_id: UUID) -> None:
        health = client.post(f"/api/v1/predict/{motor_id}").json()["health"]
        assert health["status"] in {"Healthy", "Warning", "Critical"}
        assert 0.0 <= health["health_score"] <= 100.0

    def test_predict_risk_fields(self, client: TestClient, motor_id: UUID) -> None:
        risk = client.post(f"/api/v1/predict/{motor_id}").json()["risk"]
        assert "risk_7d" in risk
        assert "risk_30d" in risk
        assert "risk_level" in risk
        assert risk["risk_level"] in {"Low", "Medium", "High", "Critical"}

    def test_predict_with_include_features(self, client: TestClient, motor_id: UUID) -> None:
        response = client.post(
            f"/api/v1/predict/{motor_id}",
            json={"include_features": True},
        )
        assert response.status_code == 200

    def test_predict_invalid_motor_id(self, client: TestClient) -> None:
        response = client.post("/api/v1/predict/not-a-uuid")
        assert response.status_code == 422

    def test_predict_motor_not_found(self, client: TestClient, motor_id: UUID) -> None:
        from fastapi import HTTPException
        client.app.dependency_overrides.clear()

        app = _build_app()
        mock_svc = MagicMock(spec=PredictionService)
        mock_svc.predict = AsyncMock(side_effect=ValueError("Motor not found"))

        app.dependency_overrides[get_session] = lambda: AsyncMock()
        from app.routes.predictions import _get_prediction_service
        app.dependency_overrides[_get_prediction_service] = lambda: mock_svc

        c = TestClient(app)
        response = c.post(f"/api/v1/predict/{motor_id}")
        assert response.status_code == 404


class TestPredictionsListEndpoint:

    def test_list_returns_200(self, client: TestClient, motor_id: UUID) -> None:
        response = client.get(f"/api/v1/motors/{motor_id}/predictions")
        assert response.status_code == 200

    def test_list_response_schema(self, client: TestClient, motor_id: UUID) -> None:
        data = client.get(f"/api/v1/motors/{motor_id}/predictions").json()
        assert "motor_id" in data
        assert "total" in data
        assert "predictions" in data
        assert isinstance(data["predictions"], list)

    def test_list_pagination_params(self, client: TestClient, motor_id: UUID) -> None:
        response = client.get(
            f"/api/v1/motors/{motor_id}/predictions",
            params={"limit": 10, "offset": 5},
        )
        assert response.status_code == 200

    def test_list_invalid_limit(self, client: TestClient, motor_id: UUID) -> None:
        response = client.get(
            f"/api/v1/motors/{motor_id}/predictions",
            params={"limit": 0},
        )
        assert response.status_code == 422

    def test_list_limit_max(self, client: TestClient, motor_id: UUID) -> None:
        response = client.get(
            f"/api/v1/motors/{motor_id}/predictions",
            params={"limit": 201},
        )
        assert response.status_code == 422


class TestRiskEndpoint:

    def test_risk_returns_200(self, client: TestClient, motor_id: UUID) -> None:
        response = client.get(f"/api/v1/motors/{motor_id}/risk")
        assert response.status_code == 200

    def test_risk_response_schema(self, client: TestClient, motor_id: UUID) -> None:
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()
        assert "motor_id" in data
        assert "current_health_score" in data
        assert "risk_7d" in data
        assert "risk_30d" in data
        assert "risk_level" in data
        assert "trend" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_risk_level_valid_value(self, client: TestClient, motor_id: UUID) -> None:
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()
        assert data["risk_level"] in {"Low", "Medium", "High", "Critical"}

    def test_risk_trend_valid_value(self, client: TestClient, motor_id: UUID) -> None:
        data = client.get(f"/api/v1/motors/{motor_id}/risk").json()
        assert data["trend"] in {"Improving", "Stable", "Degrading"}
