"""
mcp_client/agent.py — Agente LangGraph ReAct

Versão simplificada — apenas chat, sem pipeline de visualizações.
Tools retornam texto puro; o LLM responde em linguagem natural.

Smoke-test:
    python -m mcp_client.agent
"""

import asyncio
import logging
import sys
import uuid
import warnings
from pathlib import Path
from typing import AsyncGenerator

warnings.filterwarnings(
    "ignore",
    message=".*additionalProperties.*not supported.*",
    category=UserWarning,
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client.logging_config import configurar_logging
configurar_logging()
logger = logging.getLogger("mcp_client.agent")

import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv(Path(__file__).parent.parent / ".env")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MCP_CONFIG = {
    "etice-contratos": {
        "command": sys.executable,
        "args": ["-m", "mcp_server.server"],
        "transport": "stdio",
    }
}

SYSTEM_PROMPT = """Você é um assistente especializado em contratos de fornecedores
de nuvem da ETICE (Empresa de Tecnologia da Informação do Ceará).

Você tem acesso a ferramentas para consultar a base de contratos.
Sempre que o usuário fizer uma pergunta sobre contratos, empresas,
valores ou modalidades, use as ferramentas disponíveis antes de responder.

REGRAS DE FORMATAÇÃO — OBRIGATÓRIAS:
- Responda SEMPRE em texto puro, sem markdown.
- NUNCA use asteriscos, underscores, cerquilhas (#), backticks ou qualquer
  outro símbolo de formatação markdown.
- Para listas, use hífen simples seguido de espaço: "- item".
- Para separar seções, use linha em branco.
- Números e valores monetários podem usar formatação normal (R$ 1.200,00).
- Seja objetivo e apresente os dados de forma clara e estruturada em português.
"""


# ── AppState ──────────────────────────────────────────────────────────────────

class AppState:
    def __init__(self) -> None:
        self._mcp_client: MultiServerMCPClient | None = None
        self.agente  = None
        self.tools: list = []
        self.memory: MemorySaver | None = None
        self._pronto = False

    async def inicializar(self) -> None:
        logger.info("Inicializando AppState...")
        self._mcp_client = MultiServerMCPClient(MCP_CONFIG)
        self.tools = await self._mcp_client.get_tools()
        logger.info("%d tool(s): %s", len(self.tools), [t.name for t in self.tools])

        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        self.memory = MemorySaver()
        self.agente = create_react_agent(
            model=llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=self.memory,
        )
        self._pronto = True
        logger.info("AppState pronto.")

    async def encerrar(self) -> None:
        logger.info("Encerrando AppState...")
        if self._mcp_client is None:
            return
        if hasattr(self._mcp_client, "aclose"):
            await self._mcp_client.aclose()
        elif hasattr(self._mcp_client, "close"):
            self._mcp_client.close()
        self._pronto = False

    @property
    def pronto(self) -> bool:
        return self._pronto


def nova_sessao() -> str:
    return str(uuid.uuid4())


# ── Execução ──────────────────────────────────────────────────────────────────

async def invocar(agente, mensagem: str, thread_id: str) -> str:
    """Resposta completa — útil para testes e scripts batch."""
    config = {"configurable": {"thread_id": thread_id}}
    resultado = await agente.ainvoke(
        {"messages": [HumanMessage(content=mensagem)]},
        config=config,
    )
    return resultado["messages"][-1].content


async def invocar_stream(
    agente, mensagem: str, thread_id: str
) -> AsyncGenerator[str, None]:
    """
    Gerador assíncrono de chunks de texto conforme o LLM os produz.
    Filtra apenas on_chat_model_stream — metadados do LangGraph não chegam ao chamador.
    """
    config = {"configurable": {"thread_id": thread_id}}
    logger.info("invocar_stream | thread=%s | msg=%s", thread_id[:8], mensagem[:60])
    async for event in agente.astream_events(
        {"messages": [HumanMessage(content=mensagem)]},
        config=config,
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                yield chunk


# ── Smoke-test ────────────────────────────────────────────────────────────────

async def main() -> None:
    print()
    print("\033[96m═══════════════════════════════════════════════════════\033[0m")
    print("\033[96m  ETICE — Agente ReAct (LangGraph + MCP)               \033[0m")
    print("\033[96m═══════════════════════════════════════════════════════\033[0m")
    print()

    state = AppState()
    await state.inicializar()
    try:
        print(f"  \033[92m✓\033[0m {len(state.tools)} tool(s):")
        for t in state.tools:
            print(f"     • {t.name}")
        print()
        thread_id = nova_sessao()
        print("Agente: ", end="", flush=True)
        async for chunk in invocar_stream(state.agente, "Olá, você está funcionando?", thread_id):
            print(chunk, end="", flush=True)
        print("\n")
    finally:
        await state.encerrar()


if __name__ == "__main__":
    asyncio.run(main())