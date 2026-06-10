"""
api/dependencies.py — Dependências FastAPI injetáveis via Depends()

Centraliza o acesso ao AppState e ao SessionRegistry para que os
routers não importem `app` diretamente (evita import circular).

Uso nos routers:
    from api.dependencies import agente_dep, registry_dep, sessao_dep

    @router.post("/")
    async def endpoint(
        state: Annotated[AppState, Depends(agente_dep)],
        registry: Annotated[SessionRegistry, Depends(registry_dep)],
    ): ...
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from mcp_client.agent import AppState
from api.sessions import SessionRegistry, SessaoMeta


def agente_dep(request: Request) -> AppState:
    """Retorna o AppState global. Falha com 503 se ainda não estiver pronto."""
    state: AppState = request.app.state.agente_state
    if not state.pronto:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agente ainda não está pronto. Tente novamente em instantes.",
        )
    return state


def registry_dep(request: Request) -> SessionRegistry:
    """Retorna o SessionRegistry global."""
    return request.app.state.session_registry


def sessao_dep(
    session_id: str,
    registry: Annotated[SessionRegistry, Depends(registry_dep)],
) -> SessaoMeta:
    """
    Valida que session_id existe. Injeta o SessaoMeta nos endpoints
    que recebem session_id como path parameter.
    """
    meta = registry.obter(session_id)
    if meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sessão '{session_id}' não encontrada.",
        )
    return meta
