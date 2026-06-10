"""
api/models.py — Schemas Pydantic para request e response da API

Centraliza todos os contratos de dados entre o frontend e o backend.
Alterar um campo aqui propaga automaticamente para a documentação OpenAPI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Sessões ───────────────────────────────────────────────────────────────────

class SessaoCriada(BaseModel):
    """Retornado por POST /sessoes."""
    session_id: str = Field(..., description="UUID da sessão criada.")
    criada_em: datetime = Field(..., description="Timestamp UTC de criação.")


class SessaoInfo(BaseModel):
    """Retornado por GET /sessoes/{session_id}."""
    session_id: str
    criada_em: datetime
    total_mensagens: int = Field(..., description="Número de turnos na conversa.")


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Body de POST /sessoes/{session_id}/chat."""
    mensagem: str = Field(..., min_length=1, max_length=4096)


# ── Histórico ─────────────────────────────────────────────────────────────────

class MensagemHistorico(BaseModel):
    papel: Literal["user", "assistant", "tool"]
    conteudo: str
    timestamp: datetime


class HistoricoResponse(BaseModel):
    """Retornado por GET /sessoes/{session_id}/historico."""
    session_id: str
    mensagens: list[MensagemHistorico]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    agente_pronto: bool
    total_tools: int
    versao: str = "1.0.0"
