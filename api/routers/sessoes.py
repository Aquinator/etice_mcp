"""
api/routers/sessoes.py — Ciclo de vida das sessões de chat

POST   /sessoes                        → cria sessão, retorna session_id
GET    /sessoes/{session_id}           → metadados da sessão
GET    /sessoes/{session_id}/historico → histórico de mensagens (do MemorySaver)
DELETE /sessoes/{session_id}           → encerra sessão
"""

from __future__ import annotations

from datetime import timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from api.dependencies import agente_dep, registry_dep, sessao_dep
from api.models import (
    HistoricoResponse,
    MensagemHistorico,
    SessaoCriada,
    SessaoInfo,
)
from api.sessions import SessionRegistry, SessaoMeta
from mcp_client.agent import AppState, nova_sessao

router = APIRouter(prefix="/sessoes", tags=["sessoes"])


@router.post(
    "",
    response_model=SessaoCriada,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova sessão de chat",
)
async def criar_sessao(
    registry: Annotated[SessionRegistry, Depends(registry_dep)],
    _state: Annotated[AppState, Depends(agente_dep)],  # garante 503 se agente não estiver pronto
) -> SessaoCriada:
    session_id = nova_sessao()
    meta = registry.criar(session_id)
    return SessaoCriada(session_id=meta.session_id, criada_em=meta.criada_em)


@router.get(
    "/{session_id}",
    response_model=SessaoInfo,
    summary="Metadados de uma sessão",
)
async def obter_sessao(
    meta: Annotated[SessaoMeta, Depends(sessao_dep)],
) -> SessaoInfo:
    return SessaoInfo(
        session_id=meta.session_id,
        criada_em=meta.criada_em,
        total_mensagens=meta.total_mensagens,
    )


@router.get(
    "/{session_id}/historico",
    response_model=HistoricoResponse,
    summary="Histórico de mensagens da sessão",
    description=(
        "Reconstrói o histórico a partir do MemorySaver do LangGraph. "
        "Mensagens de tool call são incluídas com papel 'tool' para "
        "permitir que o frontend exiba o raciocínio do agente se desejar."
    ),
)
async def historico_sessao(
    session_id: str,
    meta: Annotated[SessaoMeta, Depends(sessao_dep)],
    state: Annotated[AppState, Depends(agente_dep)],
) -> HistoricoResponse:
    config = {"configurable": {"thread_id": session_id}}
    checkpoint = state.memory.get(config)

    mensagens: list[MensagemHistorico] = []

    if checkpoint:
        # channel_values["messages"] é a lista canônica do LangGraph
        raw_msgs = checkpoint.get("channel_values", {}).get("messages", [])
        ts = meta.criada_em  # timestamp de criação como fallback

        for msg in raw_msgs:
            if isinstance(msg, HumanMessage):
                papel = "user"
                conteudo = msg.content if isinstance(msg.content, str) else str(msg.content)
            elif isinstance(msg, AIMessage):
                papel = "assistant"
                # AIMessage pode ter content = "" quando só emite tool_calls
                conteudo = msg.content if isinstance(msg.content, str) else str(msg.content)
                if not conteudo:
                    continue  # pula mensagens de tool-call puro sem texto visível
            elif isinstance(msg, ToolMessage):
                papel = "tool"
                conteudo = msg.content if isinstance(msg.content, str) else str(msg.content)
            else:
                continue

            # LangGraph não armazena timestamp por mensagem; usamos o da sessão
            # como aproximação. Produções futuras podem usar additional_kwargs.
            mensagens.append(
                MensagemHistorico(papel=papel, conteudo=conteudo, timestamp=ts)
            )

    return HistoricoResponse(session_id=session_id, mensagens=mensagens)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerra e remove uma sessão",
)
async def deletar_sessao(
    session_id: str,
    meta: Annotated[SessaoMeta, Depends(sessao_dep)],
    registry: Annotated[SessionRegistry, Depends(registry_dep)],
    state: Annotated[AppState, Depends(agente_dep)],
) -> None:
    registry.remover(session_id)
    # Remove o checkpoint do MemorySaver para liberar memória
    config = {"configurable": {"thread_id": session_id}}
    if hasattr(state.memory, "adelete"):
        await state.memory.adelete(config)
    elif hasattr(state.memory, "delete"):
        state.memory.delete(config)
