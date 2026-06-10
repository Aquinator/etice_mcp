"""
api/main.py — Aplicação FastAPI

Execução (a partir da raiz do projeto, etice_mcp/):
    uvicorn api.main:app --reload --port 8000

Documentação interativa:
    http://localhost:8000/docs
    http://localhost:8000/redoc
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Garante que etice_mcp/ esteja no sys.path independente de onde
# o uvicorn é invocado. Path(__file__) = etice_mcp/api/main.py,
# portanto .parent.parent = etice_mcp/.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importações diretas dos módulos — nunca via pacote intermediário
# para evitar import circular durante a inicialização do uvicorn.
from mcp_client.agent import AppState
from api.sessions import SessionRegistry
from api.routers.health import router as health_router
from api.routers.sessoes import router as sessoes_router
from api.routers.chat import router as chat_router

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("api")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa o agente antes de aceitar requisições e encerra o
    subprocesso MCP ao desligar o servidor.
    """
    logger.info("Iniciando agente e conexão MCP...")
    state = AppState()
    await state.inicializar()
    app.state.agente_state = state
    app.state.session_registry = SessionRegistry()
    logger.info("Agente pronto | %d tool(s) disponível(is)", len(state.tools))

    yield

    logger.info("Encerrando agente e conexão MCP...")
    await state.encerrar()
    logger.info("Encerrado com sucesso.")


# ── Aplicação ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ETICE — API de Contratos de Nuvem",
    description=(
        "API REST com streaming SSE para consulta de contratos de fornecedores "
        "de nuvem da ETICE via agente ReAct (LangGraph + Gemini + MCP)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(sessoes_router)
app.include_router(chat_router)