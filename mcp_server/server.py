"""
mcp_server/server.py — Servidor MCP (FastMCP + SQLAlchemy)

Uso normal (pelo cliente):
    Invocado automaticamente pelo mcp_client como subprocesso stdio.

Uso com Inspector (sandbox):
    fastmcp dev mcp_server/server.py

Uso direto (teste de conexão com banco):
    python -m mcp_server.server
"""

import sys
import logging
import time
from functools import wraps
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastmcp import FastMCP
from mcp_server.db import check_connection, query, DSN

# ── Logging ───────────────────────────────────────────────────────────────────
# stderr  → visível no terminal e capturado pelo uvicorn se necessário
# arquivo → logs/etice_server.log, rotaciona em 5 MB, 3 backups
def _setup_logging() -> logging.Logger:
    from logging.handlers import RotatingFileHandler
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    try:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        fh = RotatingFileHandler(
            log_dir / "etice_server.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        pass  # contexto sem permissão de escrita (ex: Inspector isolado)

    return logging.getLogger("mcp_server")

logger = _setup_logging()


# ── Decorador de observabilidade ──────────────────────────────────────────────

def log_tool_execution(func):
    """Registra latência, parâmetros e resultado/erro de cada tool."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        logger.info("tool '%s' iniciada | kwargs=%s", func.__name__, kwargs)
        try:
            resultado = func(*args, **kwargs)
            ms = (time.perf_counter() - t0) * 1000
            logger.info("tool '%s' ok | %.1f ms", func.__name__, ms)
            return resultado
        except Exception as exc:
            ms = (time.perf_counter() - t0) * 1000
            logger.error("tool '%s' falhou | %.1f ms | %s", func.__name__, ms, exc)
            return f"Erro interno ao processar a solicitação: {exc}"
    return wrapper


# ── Servidor MCP ──────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="etice-contratos-nuvem",
    instructions=(
        "Você é um assistente especializado em contratos de fornecedores de "
        "nuvem da ETICE. Utilize as ferramentas disponíveis para consultar, "
        "analisar e responder perguntas sobre os contratos cadastrados."
    ),
)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
@log_tool_execution
def listar_contratos(limite: int = 10) -> str:
    """Lista os contratos de nuvem cadastrados com um resumo (ID, Número, Empresa, Modalidade, Valor, Vigência)."""
    sql = """
        SELECT pk_id_con, num_numero_contrato_con,
               dsc_empresa_contratada_con, tip_modalidade_con,
               vlr_valor_total_contrato_con, dat_prazo_vigencia_meses_con
        FROM tb_contrato_con
        ORDER BY pk_id_con DESC
        LIMIT :limite
    """
    try:
        rows = query(sql, {"limite": max(1, min(limite, 50))})
        if not rows:
            return "Nenhum contrato encontrado na base de dados."
        linhas = [f"Total retornado: {len(rows)}"]
        for r in rows:
            id_con   = r.get("pk_id_con", "N/A")
            num      = r.get("num_numero_contrato_con") or "S/N"
            empresa  = r.get("dsc_empresa_contratada_con") or "Não informada"
            mod      = r.get("tip_modalidade_con") or "Não classificada"
            vigencia = r.get("dat_prazo_vigencia_meses_con") or "Não informada"
            vlr      = float(r.get("vlr_valor_total_contrato_con") or 0.0)
            linhas.append(
                f"[{id_con}] Contrato {num} | {empresa} | {mod} | Vigência: {vigencia} | R$ {vlr:,.2f}"
            )
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao consultar contratos: {exc}"


@mcp.tool()
@log_tool_execution
def listar_gerentes() -> str:
    """Lista todos os gestores responsáveis pelos contratos de nuvem da ETICE."""
    sql = """
        SELECT DISTINCT dsc_nome_gestor_con
        FROM tb_contrato_con
        WHERE dsc_nome_gestor_con IS NOT NULL AND dsc_nome_gestor_con != ''
        ORDER BY dsc_nome_gestor_con ASC
    """
    try:
        rows = query(sql)
        if not rows:
            return "Nenhum gestor encontrado."
        gerentes = [r["dsc_nome_gestor_con"] for r in rows]
        return "Gestores de Contrato cadastrados:\n- " + "\n- ".join(gerentes)
    except Exception as exc:
        return f"Erro ao consultar gestores: {exc}"


@mcp.tool()
@log_tool_execution
def listar_empresas() -> str:
    """Lista todas as empresas fornecedoras com quantidade de contratos e valor total."""
    sql = """
        SELECT dsc_empresa_contratada_con AS empresa,
               COUNT(*) AS num_contratos,
               SUM(vlr_valor_total_contrato_con) AS valor_total
        FROM tb_contrato_con
        WHERE dsc_empresa_contratada_con IS NOT NULL AND dsc_empresa_contratada_con != ''
        GROUP BY dsc_empresa_contratada_con
        ORDER BY num_contratos DESC
    """
    try:
        rows = query(sql)
        if not rows:
            return "Nenhuma empresa encontrada."
        linhas = [f"Empresas contratadas ({len(rows)} encontradas):"]
        for r in rows:
            emp = r["empresa"]
            qtd = int(r["num_contratos"])
            vt  = float(r["valor_total"] or 0.0)
            linhas.append(f"- {emp}: {qtd} contrato(s) | R$ {vt:,.2f}")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao consultar empresas: {exc}"


_COLUNAS_BUSCA: dict[str, str] = {
    "numero":       "num_numero_contrato_con",
    "empresa":      "dsc_empresa_contratada_con",
    "termo_objeto": "dsc_objeto_contrato_con",
}

@mcp.tool()
@log_tool_execution
def buscar_contrato(
    numero:       Optional[str] = None,
    empresa:      Optional[str] = None,
    termo_objeto: Optional[str] = None,
    limite:       int = 20,
) -> str:
    """
    Busca contratos aplicando filtros opcionais. Retorna ID, Número, Empresa e Valor.

    Args:
        numero:       Trecho do número do contrato.
        empresa:      Trecho do nome da empresa contratada.
        termo_objeto: Trecho do objeto/descrição do contrato.
        limite:       Número máximo de resultados (1-50, padrão 20).
    """
    limite = max(1, min(limite, 50))
    sql = """
        SELECT pk_id_con, num_numero_contrato_con, dsc_empresa_contratada_con,
               vlr_valor_total_contrato_con, tip_modalidade_con
        FROM tb_contrato_con WHERE 1=1
    """
    params: dict = {}
    for chave, valor in {"numero": numero, "empresa": empresa, "termo_objeto": termo_objeto}.items():
        if valor:
            coluna = _COLUNAS_BUSCA[chave]
            param  = f"p_{chave}"
            sql   += f" AND {coluna} LIKE :{param}"
            params[param] = f"%{valor}%"
    sql += " ORDER BY pk_id_con DESC LIMIT :limite"
    params["limite"] = limite
    try:
        rows = query(sql, params)
        if not rows:
            return "Nenhum contrato encontrado com os filtros fornecidos."
        linhas = [f"Resultados encontrados: {len(rows)}"]
        for r in rows:
            id_con = r.get("pk_id_con", "N/A")
            num    = r.get("num_numero_contrato_con") or "S/N"
            emp    = r.get("dsc_empresa_contratada_con") or "Não informada"
            vlr    = float(r.get("vlr_valor_total_contrato_con") or 0.0)
            linhas.append(f"[{id_con}] Contrato {num} | Empresa: {emp} | Valor: R$ {vlr:,.2f}")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao buscar contratos: {exc}"


@mcp.tool()
@log_tool_execution
def detalhar_contrato(id_contrato: int) -> str:
    """
    Retorna a ficha completa de um único contrato dado o seu ID.
    Traz objeto completo, datas de assinatura, arquivo PDF e modalidade.
    """
    sql = "SELECT * FROM tb_contrato_con WHERE pk_id_con = :id"
    try:
        rows = query(sql, {"id": id_contrato})
        if not rows:
            return f"Contrato com ID {id_contrato} não encontrado."
        r   = rows[0]
        vlr = float(r.get("vlr_valor_total_contrato_con") or 0.0)
        return "\n".join([
            f"=== DETALHES DO CONTRATO ID {id_contrato} ===",
            f"Número:          {r.get('num_numero_contrato_con') or 'N/A'}",
            f"Empresa:         {r.get('dsc_empresa_contratada_con') or 'N/A'}",
            f"Modalidade:      {r.get('tip_modalidade_con') or 'Não informada'}",
            f"Valor Total:     R$ {vlr:,.2f}",
            f"Data Assinatura: {r.get('dat_data_assinatura_con') or 'N/A'}",
            f"Vigência:        {r.get('dat_prazo_vigencia_meses_con') or 'N/A'} "
            f"(Fim: {r.get('data_fim_vigencia_con') or 'N/A'})",
            f"Gestor:          {r.get('dsc_nome_gestor_con') or 'N/A'}",
            f"Arquivo PDF:     {r.get('dsc_nome_arquivo_pdf_con') or 'N/A'}",
            f"\nObjeto do Contrato:\n{r.get('dsc_objeto_contrato_con') or 'Sem descrição'}",
        ])
    except Exception as exc:
        return f"Erro ao detalhar contrato: {exc}"


@mcp.tool()
@log_tool_execution
def estatisticas_contratos() -> str:
    """
    Retorna métricas agregadas: valor total investido, média de valores
    e distribuição de contratos por modalidade (IaaS, SaaS, PaaS).
    """
    sql = """
        SELECT
            COALESCE(tip_modalidade_con, 'Não classificado') AS modalidade,
            COUNT(*)                                          AS quantidade,
            SUM(vlr_valor_total_contrato_con)                 AS valor_total,
            AVG(vlr_valor_total_contrato_con)                 AS valor_medio
        FROM tb_contrato_con
        GROUP BY tip_modalidade_con
        ORDER BY quantidade DESC
    """
    try:
        rows = query(sql)
        if not rows:
            return "Não há dados suficientes para gerar estatísticas."
        total_global = 0.0
        qtd_global   = 0
        linhas       = ["=== ESTATÍSTICAS DE CONTRATOS DE NUVEM (ETICE) ==="]
        for r in rows:
            mod     = r["modalidade"]
            qtd     = r["quantidade"]
            v_total = float(r["valor_total"] or 0.0)
            v_medio = float(r["valor_medio"] or 0.0)
            total_global += v_total
            qtd_global   += qtd
            linhas.append(
                f"- {mod}: {qtd} contrato(s) | Total: R$ {v_total:,.2f} | Média: R$ {v_medio:,.2f}"
            )
        linhas.insert(1, f"Total de Contratos: {qtd_global}")
        linhas.insert(2, f"Valor Global Investido: R$ {total_global:,.2f}\n")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao gerar estatísticas: {exc}"


@mcp.tool()
@log_tool_execution
def ranking_contratos(ordem: str = "valor_desc", limite: int = 10) -> str:
    """
    Retorna contratos ordenados por valor ou data. Use quando o usuário
    pedir ranking, os maiores contratos, ou ordenação por valor.

    Args:
        ordem:  "valor_desc" (maior valor primeiro, padrão),
                "valor_asc"  (menor valor primeiro),
                "recente"    (mais recente primeiro).
        limite: Número de contratos a retornar (1-20, padrão 10).
    """
    limite = max(1, min(limite, 20))
    _ORDENS = {
        "valor_desc": "vlr_valor_total_contrato_con DESC",
        "valor_asc":  "vlr_valor_total_contrato_con ASC",
        "recente":    "dat_data_assinatura_con DESC",
    }
    order_clause = _ORDENS.get(ordem, _ORDENS["valor_desc"])
    sql = f"""
        SELECT num_numero_contrato_con,
               dsc_empresa_contratada_con,
               vlr_valor_total_contrato_con,
               tip_modalidade_con
        FROM tb_contrato_con
        WHERE vlr_valor_total_contrato_con IS NOT NULL
        ORDER BY {order_clause}
        LIMIT :limite
    """
    try:
        rows = query(sql, {"limite": limite})
        if not rows:
            return "Nenhum contrato encontrado."
        linhas = [f"Ranking de contratos ({len(rows)} resultados):"]
        for i, r in enumerate(rows, 1):
            num = r.get("num_numero_contrato_con") or "S/N"
            emp = r.get("dsc_empresa_contratada_con") or "Não informada"
            mod = r.get("tip_modalidade_con") or "N/C"
            vlr = float(r.get("vlr_valor_total_contrato_con") or 0.0)
            linhas.append(f"{i}. Contrato {num} | {emp} | {mod} | R$ {vlr:,.2f}")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao gerar ranking: {exc}"


@mcp.tool()
@log_tool_execution
def analise_agregada_gerencial(nome_gestor: Optional[str] = None) -> str:
    """
    Retorna número de contratos e valor total por gestor.
    Se nome_gestor não for informado, lista o ranking completo por volume financeiro.

    Args:
        nome_gestor: Nome parcial ou completo do gestor para filtrar (opcional).
    """
    sql = """
        SELECT dsc_nome_gestor_con AS gestor,
               COUNT(*) AS num_contratos,
               SUM(vlr_valor_total_contrato_con) AS valor_total
        FROM tb_contrato_con
        WHERE dsc_nome_gestor_con IS NOT NULL AND dsc_nome_gestor_con != ''
    """
    params: dict = {}
    if nome_gestor:
        sql += " AND dsc_nome_gestor_con LIKE :gestor"
        params["gestor"] = f"%{nome_gestor}%"
    sql += " GROUP BY dsc_nome_gestor_con ORDER BY valor_total DESC"
    try:
        rows = query(sql, params)
        if not rows:
            return "Nenhum dado gerencial encontrado."
        linhas = [f"Ranking gerencial ({len(rows)} gestor(es)):"]
        for i, r in enumerate(rows, 1):
            g  = r["gestor"]
            n  = r["num_contratos"]
            vt = float(r["valor_total"] or 0.0)
            linhas.append(f"{i}. {g} | {n} contrato(s) | R$ {vt:,.2f}")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao gerar análise gerencial: {exc}"


@mcp.tool()
@log_tool_execution
def analise_vencimentos(proximos_meses: int = 6) -> str:
    """
    Lista contratos cujo prazo de vigência termina nos próximos N meses.
    Útil para planejamento de renovações.

    Args:
        proximos_meses: Janela em meses (padrão 6, máximo 36).
    """
    proximos_meses = max(1, min(proximos_meses, 36))
    sql = """
        SELECT pk_id_con, num_numero_contrato_con,
               dsc_empresa_contratada_con, data_fim_vigencia_con,
               vlr_valor_total_contrato_con
        FROM tb_contrato_con
        WHERE data_fim_vigencia_con IS NOT NULL
          AND data_fim_vigencia_con BETWEEN CURDATE()
              AND DATE_ADD(CURDATE(), INTERVAL :meses MONTH)
        ORDER BY data_fim_vigencia_con ASC
    """
    try:
        rows = query(sql, {"meses": proximos_meses})
        if not rows:
            return f"Nenhum contrato vence nos próximos {proximos_meses} meses."
        linhas = [f"Contratos vencendo nos próximos {proximos_meses} meses ({len(rows)} encontrados):"]
        for r in rows:
            num = r.get("num_numero_contrato_con") or "S/N"
            emp = r.get("dsc_empresa_contratada_con") or "Não informada"
            fim = r.get("data_fim_vigencia_con") or "N/A"
            vlr = float(r.get("vlr_valor_total_contrato_con") or 0.0)
            linhas.append(f"- Contrato {num} | {emp} | Vence: {fim} | R$ {vlr:,.2f}")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao analisar vencimentos: {exc}"


@mcp.tool()
@log_tool_execution
def historico_empresa(nome_empresa: str) -> str:
    """
    Resumo completo do relacionamento com uma empresa fornecedora:
    total de contratos, valor global e modalidades atendidas.

    Args:
        nome_empresa: Nome parcial ou completo da empresa contratada.
    """
    sql = """
        SELECT COUNT(*) AS total_contratos,
               SUM(vlr_valor_total_contrato_con) AS valor_global,
               GROUP_CONCAT(
                   DISTINCT COALESCE(tip_modalidade_con, 'Não classificada')
                   ORDER BY tip_modalidade_con SEPARATOR ', '
               ) AS modalidades
        FROM tb_contrato_con
        WHERE dsc_empresa_contratada_con LIKE :emp
    """
    try:
        rows = query(sql, {"emp": f"%{nome_empresa}%"})
        r = rows[0] if rows else {}
        total = r.get("total_contratos") or 0
        if not total:
            return f"Nenhum contrato encontrado para a empresa '{nome_empresa}'."
        vg   = float(r.get("valor_global") or 0.0)
        mods = r.get("modalidades") or "N/A"
        return (
            f"Histórico de '{nome_empresa}':\n"
            f"  Total de contratos: {total}\n"
            f"  Valor global:       R$ {vg:,.2f}\n"
            f"  Modalidades:        {mods}"
        )
    except Exception as exc:
        return f"Erro ao buscar histórico da empresa: {exc}"


@mcp.tool()
@log_tool_execution
def estatisticas_anuais() -> str:
    """
    Valor médio, total e quantidade de contratos agrupados por ano de assinatura.
    Útil para análise de tendência histórica.
    """
    sql = """
        SELECT YEAR(dat_data_assinatura_con) AS ano,
               COUNT(*) AS quantidade,
               SUM(vlr_valor_total_contrato_con) AS valor_total,
               AVG(vlr_valor_total_contrato_con) AS valor_medio
        FROM tb_contrato_con
        WHERE dat_data_assinatura_con IS NOT NULL
        GROUP BY YEAR(dat_data_assinatura_con)
        ORDER BY ano ASC
    """
    try:
        rows = query(sql)
        if not rows:
            return "Não há dados suficientes para estatísticas anuais."
        linhas = ["Estatísticas por ano de assinatura:"]
        for r in rows:
            ano = r["ano"]
            qtd = r["quantidade"]
            vt  = float(r["valor_total"] or 0.0)
            vm  = float(r["valor_medio"] or 0.0)
            linhas.append(f"{ano}: {qtd} contrato(s) | Total: R$ {vt:,.2f} | Média: R$ {vm:,.2f}")
        return "\n".join(linhas)
    except Exception as exc:
        return f"Erro ao gerar estatísticas anuais: {exc}"


@mcp.tool()
@log_tool_execution
def estatisticas_vigencia() -> str:
    """
    Calcula média, mínimo e máximo de vigência em meses de todos os contratos
    com datas de assinatura e fim de vigência registradas.
    """
    sql = """
        SELECT AVG(TIMESTAMPDIFF(MONTH, dat_data_assinatura_con, data_fim_vigencia_con)) AS media_meses,
               MIN(TIMESTAMPDIFF(MONTH, dat_data_assinatura_con, data_fim_vigencia_con)) AS min_meses,
               MAX(TIMESTAMPDIFF(MONTH, dat_data_assinatura_con, data_fim_vigencia_con)) AS max_meses
        FROM tb_contrato_con
        WHERE dat_data_assinatura_con IS NOT NULL
          AND data_fim_vigencia_con IS NOT NULL
    """
    try:
        rows = query(sql)
        r = rows[0] if rows else {}
        media = r.get("media_meses")
        if media is None:
            return "Dados insuficientes para calcular vigência média."
        return (
            f"Vigência dos contratos:\n"
            f"  Média:  {float(media):.1f} meses\n"
            f"  Mínima: {int(r.get('min_meses') or 0)} meses\n"
            f"  Máxima: {int(r.get('max_meses') or 0)} meses"
        )
    except Exception as exc:
        return f"Erro ao calcular estatísticas de vigência: {exc}"


# ── Entrypoint ────────────────────────────────────────────────────────────────

def _verificar_banco() -> None:
    if check_connection():
        print(f"  \033[92m✓\033[0m MariaDB conectado: {DSN.split('@')[-1]}", file=sys.stderr, flush=True)
    else:
        print(f"  \033[91m✗\033[0m Falha ao conectar no MariaDB: {DSN.split('@')[-1]}", file=sys.stderr, flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    print(file=sys.stderr)
    print("\033[96m═══════════════════════════════════════════════════════\033[0m", file=sys.stderr)
    print("\033[96m  ETICE — Servidor MCP Contratos de Nuvem              \033[0m", file=sys.stderr)
    print("\033[96m═══════════════════════════════════════════════════════\033[0m", file=sys.stderr)
    _verificar_banco()
    print(file=sys.stderr)
    mcp.run(transport="stdio")