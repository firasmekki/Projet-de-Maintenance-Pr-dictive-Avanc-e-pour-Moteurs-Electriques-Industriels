from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    version: str
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "ok",
            "service": "ORBIT AI Industrial Copilot API",
            "environment": "local",
            "version": "0.1.0",
            "timestamp": "2026-06-22T12:00:00Z",
        }
    })
