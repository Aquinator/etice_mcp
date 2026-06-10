"""
mcp_server/db.py — Conexão com MariaDB
"""

import os
from pathlib import Path
from typing import Any

import sqlalchemy
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_HOST = os.getenv("MARIADB_HOST", "localhost")
_PORT = os.getenv("MARIADB_PORT", "3306")
_DB   = os.getenv("MARIADB_DB",   "etice_contratos")
_USER = os.getenv("MARIADB_USER", "")
_PASS = os.getenv("MARIADB_PASS", "")

if not _USER or not _PASS:
    raise RuntimeError(
        "Credenciais do banco não configuradas. "
        "Defina MARIADB_USER e MARIADB_PASS no arquivo .env"
    )

DSN = f"mysql+pymysql://{_USER}:{_PASS}@{_HOST}:{_PORT}/{_DB}?charset=utf8mb4"

engine = sqlalchemy.create_engine(DSN, pool_pre_ping=True, pool_recycle=3600)


def query(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        cols   = list(result.keys())
        return [dict(zip(cols, row)) for row in result.fetchall()]


def check_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False