from fastapi import APIRouter

from app.api.v1.endpoints import chat, diagnostics, health, motors, multi_agent, predictions, reports, upload

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(motors.router)
api_router.include_router(diagnostics.router)
api_router.include_router(predictions.router)
api_router.include_router(upload.router)
api_router.include_router(reports.router)
api_router.include_router(chat.router)
api_router.include_router(multi_agent.router)
