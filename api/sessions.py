"""
api/sessions.py — Registry em memória de sessões abertas

Mantém os metadados de cada sessão (criada_em, contagem de mensagens).
O histórico real das mensagens vive no MemorySaver do LangGraph —
este módulo só guarda o envelope necessário para as respostas da API
e para reconstruir o histórico legível via GET /sessoes/{id}/historico.

Para produção, substitua o dict por Redis ou outro store externo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class SessaoMeta:
    session_id: str
    criada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_mensagens: int = 0

    def registrar_turno(self) -> None:
        """Incrementa o contador a cada par pergunta/resposta."""
        self.total_mensagens += 1


class SessionRegistry:
    """
    Dict-wrapper com interface explícita para evitar acesso direto ao _store.
    Thread-safe para leituras concorrentes (o GIL protege dict simples),
    suficiente para o protótipo single-process com uvicorn.
    """

    def __init__(self) -> None:
        self._store: dict[str, SessaoMeta] = {}

    def criar(self, session_id: str) -> SessaoMeta:
        meta = SessaoMeta(session_id=session_id)
        self._store[session_id] = meta
        return meta

    def obter(self, session_id: str) -> SessaoMeta | None:
        return self._store.get(session_id)

    def remover(self, session_id: str) -> bool:
        return self._store.pop(session_id, None) is not None

    def listar(self) -> list[SessaoMeta]:
        return list(self._store.values())

    def existe(self, session_id: str) -> bool:
        return session_id in self._store
