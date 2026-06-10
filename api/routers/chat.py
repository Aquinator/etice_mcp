"""
api/routers/chat.py — Endpoint de chat com streaming SSE

Eventos SSE emitidos:

    event: heartbeat   → data: ping           (a cada 15s — mantém conexão viva)
    event: token       → data: "<chunk>"      (fragmento de texto do LLM)
    event: fim         → data: [DONE]
    event: sessao_reset→ data: {"novo_session_id": "...", "mensagem": "..."}
    event: erro        → data: "<mensagem>"
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from api.dependencies import agente_dep, registry_dep, sessao_dep
from api.models import ChatRequest
from api.sessions import SessaoMeta, SessionRegistry
from mcp_client.agent import AppState, invocar_stream, nova_sessao

logger = logging.getLogger("api.chat")
router = APIRouter(prefix="/sessoes", tags=["chat"])

_HEARTBEAT_INTERVAL = 15  # segundos


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def _is_corrupt_history(exc: Exception) -> bool:
    msg = str(exc)
    return (
        "AIMessages with tool_calls" in msg
        or "INVALID_CHAT_HISTORY" in msg
        or ("ToolMessage" in msg and "corresponding" in msg)
    )


async def _stream_resposta(
    agente,
    mensagem: str,
    session_id: str,
    meta: SessaoMeta,
    registry: SessionRegistry,
) -> AsyncGenerator[str, None]:
    heartbeat_task = None

    try:
        loop = asyncio.get_running_loop()
        heartbeat_queue: asyncio.Queue[str] = asyncio.Queue()

        async def heartbeat_producer():
            while True:
                try:
                    await asyncio.sleep(_HEARTBEAT_INTERVAL)
                    await heartbeat_queue.put(_sse("heartbeat", "ping"))
                except asyncio.CancelledError:
                    break

        heartbeat_task = loop.create_task(heartbeat_producer())

        stream_iter = invocar_stream(agente, mensagem, session_id).__aiter__()
        stream_done = False

        while not stream_done:
            try:
                chunk = await asyncio.wait_for(
                    stream_iter.__anext__(),
                    timeout=_HEARTBEAT_INTERVAL,
                )
                # Drena heartbeats acumulados antes de emitir token
                while not heartbeat_queue.empty():
                    yield heartbeat_queue.get_nowait()

                yield _sse("token", json.dumps(chunk, ensure_ascii=False))

            except StopAsyncIteration:
                stream_done = True
            except asyncio.TimeoutError:
                yield _sse("heartbeat", "ping")

        meta.registrar_turno()
        yield _sse("fim", "[DONE]")

    except Exception as exc:
        logger.error("Erro no stream | session=%s | %s", session_id, exc)

        if _is_corrupt_history(exc):
            # Histórico corrompido — cria nova sessão automaticamente
            registry.remover(session_id)
            novo_id = nova_sessao()
            registry.criar(novo_id)
            logger.warning("Sessão substituída | %s → %s", session_id[:8], novo_id[:8])
            yield _sse("sessao_reset", json.dumps({
                "novo_session_id": novo_id,
                "mensagem": "Sessão reiniciada. Por favor, repita sua pergunta.",
            }))
        else:
            yield _sse("erro", json.dumps(str(exc), ensure_ascii=False))

    finally:
        if heartbeat_task:
            heartbeat_task.cancel()


@router.post(
    "/{session_id}/chat",
    summary="Envia uma mensagem e recebe a resposta em streaming (SSE)",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"content": {"text/event-stream": {}}},
        404: {"description": "Sessão não encontrada"},
        503: {"description": "Agente não disponível"},
    },
)
async def chat_stream(
    session_id: str,
    body: ChatRequest,
    state: Annotated[AppState, Depends(agente_dep)],
    meta: Annotated[SessaoMeta, Depends(sessao_dep)],
    registry: Annotated[SessionRegistry, Depends(registry_dep)],
) -> StreamingResponse:
    return StreamingResponse(
        _stream_resposta(state.agente, body.mensagem, session_id, meta, registry),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )