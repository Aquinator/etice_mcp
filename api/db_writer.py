"""
api/db_writer.py — Engine SQLAlchemy com usuário sac_writer (escrita)

Separado de mcp_server/db.py (sac_reader) por design de segurança.
O agente LangGraph nunca importa este módulo.
"""
import os
from pathlib import Path
from functools import lru_cache

import sqlalchemy
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_HOST = os.getenv("MARIADB_HOST", "localhost")
_PORT = os.getenv("MARIADB_PORT", "3306")
_DB   = os.getenv("MARIADB_DB",   "etice_contratos")
_USER = os.getenv("MARIADB_WRITER_USER", "")
_PASS = os.getenv("MARIADB_WRITER_PASS", "")

if not _USER or not _PASS:
    raise RuntimeError(
        "Credenciais de escrita não configuradas. "
        "Defina MARIADB_WRITER_USER e MARIADB_WRITER_PASS no .env"
    )

_DSN = f"mysql+pymysql://{_USER}:{_PASS}@{_HOST}:{_PORT}/{_DB}?charset=utf8mb4"

@lru_cache(maxsize=1)
def get_writer_engine() -> sqlalchemy.Engine:
    return sqlalchemy.create_engine(_DSN, pool_pre_ping=True, pool_recycle=3600)