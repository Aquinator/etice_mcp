"""
api/services/saldo_service.py — Regras de negócio sobre saldo de contrato

A view SQL (vw_saldo_contrato) faz o cálculo pesado (JOIN + agregação).
Este serviço adiciona semântica de negócio sobre o resultado bruto:
classificação de criticidade, formatação, e ponto único de extensão
para regras futuras (ex: considerar aditivos de valor, retenções, etc.)
sem precisar tocar na view nem nas tools MCP.
"""

from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class SaldoContrato:
    id_contrato: int
    numero_contrato: str
    empresa: str
    valor_total: Decimal
    valor_consumido: Decimal
    saldo_disponivel: Decimal
    qtd_ordens_servico: int
    percentual_consumido: float
    criticidade: str  # "normal" | "atencao" | "critico" | "excedido"


def _classificar_criticidade(percentual: float) -> str:
    if percentual >= 100:
        return "excedido"
    if percentual >= 90:
        return "critico"
    if percentual >= 75:
        return "atencao"
    return "normal"


def obter_saldo_contrato(engine: Engine, id_contrato: int) -> SaldoContrato | None:
    """Busca o saldo de um único contrato via vw_saldo_contrato."""
    sql = text("SELECT * FROM vw_saldo_contrato WHERE pk_id_con = :id")
    with engine.connect() as conn:
        row = conn.execute(sql, {"id": id_contrato}).mappings().first()

    if row is None:
        return None

    valor_total = Decimal(str(row["valor_total_contrato"]))
    consumido   = Decimal(str(row["valor_total_consumido"]))
    pct = float(consumido / valor_total * 100) if valor_total > 0 else 0.0

    return SaldoContrato(
        id_contrato=row["pk_id_con"],
        numero_contrato=row["num_numero_contrato_con"],
        empresa=row["dsc_empresa_contratada_con"],
        valor_total=valor_total,
        valor_consumido=consumido,
        saldo_disponivel=Decimal(str(row["saldo_disponivel"])),
        qtd_ordens_servico=row["qtd_ordens_servico"],
        percentual_consumido=round(pct, 2),
        criticidade=_classificar_criticidade(pct),
    )


def listar_saldos_criticos(engine: Engine, limite: int = 20) -> list[SaldoContrato]:
    """Retorna contratos com saldo abaixo de 25% do valor total — útil para alertas."""
    sql = text("""
        SELECT * FROM vw_saldo_contrato
        WHERE valor_total_contrato > 0
          AND (saldo_disponivel / valor_total_contrato) < 0.25
        ORDER BY (saldo_disponivel / valor_total_contrato) ASC
        LIMIT :limite
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limite": limite}).mappings().all()

    resultado = []
    for row in rows:
        valor_total = Decimal(str(row["valor_total_contrato"]))
        consumido   = Decimal(str(row["valor_total_consumido"]))
        pct = float(consumido / valor_total * 100) if valor_total > 0 else 0.0
        resultado.append(SaldoContrato(
            id_contrato=row["pk_id_con"],
            numero_contrato=row["num_numero_contrato_con"],
            empresa=row["dsc_empresa_contratada_con"],
            valor_total=valor_total,
            valor_consumido=consumido,
            saldo_disponivel=Decimal(str(row["saldo_disponivel"])),
            qtd_ordens_servico=row["qtd_ordens_servico"],
            percentual_consumido=round(pct, 2),
            criticidade=_classificar_criticidade(pct),
        ))
    return resultado
