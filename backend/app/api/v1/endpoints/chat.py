"""POST /api/v1/chat — Industrial chatbot with streaming SSE."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role:    str
    content: str


class ChatRequest(BaseModel):
    message:          str
    history:          list[ChatMessage] = []
    analysis_context: dict[str, Any] | None = None
    filename:         str | None = None


@router.post("/chat", summary="Industrial AI chatbot (streaming SSE)")
def chat(req: ChatRequest) -> StreamingResponse:
    svc = ChatService()
    history = [{"role": m.role, "content": m.content} for m in req.history]

    return StreamingResponse(
        svc.stream_response(
            message=req.message,
            history=history,
            context=req.analysis_context,
            filename=req.filename,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )
