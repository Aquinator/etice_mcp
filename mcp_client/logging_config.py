"""
mcp_client/logging_config.py — Configuração centralizada de logging

Configura dois handlers para o processo cliente (agent.py, chat.py, api/):
  - StreamHandler(stderr)   → visível no terminal em tempo real
  - RotatingFileHandler     → arquivo logs/etice_client.log, rotaciona em 5 MB,
                              mantém 3 backups (≈ 15 MB máximo em disco)

Por que arquivo no protótipo?
  O terminal do chat interativo não pode ser relido. Um arquivo de log permite
  inspecionar tool calls, latências e erros após uma sessão sem precisar
  reproduzir a conversa. Para produção, substituir por serviço centralizado
  (Loki, CloudWatch, etc.).

Uso:
    from mcp_client.logging_config import configurar_logging
    configurar_logging()   # idempotente — seguro chamar várias vezes
    logger = logging.getLogger("meu.modulo")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR  = Path(__file__).resolve().parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "etice_client.log"
_FORMAT   = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_CONFIGURED = False


def configurar_logging(level: int = logging.INFO) -> None:
    """
    Configura o root logger com stderr + arquivo rotativo.
    Idempotente: chamadas subsequentes são no-op.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    _LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(_FORMAT)

    # Handler 1: terminal (stderr)
    stream_h = logging.StreamHandler(sys.stderr)
    stream_h.setFormatter(formatter)

    # Handler 2: arquivo rotativo — 5 MB × 3 backups = 15 MB máximo
    file_h = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_h.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(stream_h)
    root.addHandler(file_h)

    # Silencia bibliotecas verbosas que poluem o log sem valor para o protótipo
    for lib in ("httpx", "httpcore", "urllib3", "asyncio",
                "langchain", "langsmith", "google"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    _CONFIGURED = True