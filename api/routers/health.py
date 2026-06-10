"""
api/routers/health.py — Health check da aplicação

GET /health
  Retorna 200 se o agente está pronto, 503 caso contrário.
  Útil para monitoramento, liveness probes e o próprio frontend
  saber se pode habilitar o campo de chat.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from api.models import HealthResponse
from mcp_client.agent import AppState

router = APIRouter(tags=["infra"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check — verifica se o agente está pronto",
)
async def health(request: Request) -> JSONResponse:
    state: AppState = request.app.state.agente_state
    pronto = state.pronto
    payload = HealthResponse(
        status="ok" if pronto else "degraded",
        agente_pronto=pronto,
        total_tools=len(state.tools),
    )
    return JSONResponse(
        content=payload.model_dump(),
        status_code=status.HTTP_200_OK if pronto else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
