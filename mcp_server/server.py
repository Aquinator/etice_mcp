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

@mcp.tool()
@log_tool_execution
def consultar_saldo_contrato(numero_contrato: str = None, id_contrato: int = None) -> str:
    """
    Retorna o saldo disponível de um contrato: valor total menos o que já
    foi consumido em Ordens de Serviço. Use esta tool sempre que o usuário
    perguntar sobre saldo, valor restante, quanto ainda pode ser gasto,
    ou quanto já foi utilizado de um contrato.

    Args:
        numero_contrato: Número do contrato (ex: "001/2024"). Use este OU id_contrato.
        id_contrato: ID interno do contrato. Use este OU numero_contrato.
    """
    if not numero_contrato and not id_contrato:
        return "Informe o número do contrato ou o ID para consultar o saldo."

    sql = "SELECT * FROM vw_saldo_contrato WHERE "
    params = {}
    if id_contrato:
        sql += "pk_id_con = :id"
        params["id"] = id_contrato
    else:
        sql += "num_numero_contrato_con = :num"
        params["num"] = numero_contrato

    try:
        rows = query(sql, params)
        if not rows:
            return "Contrato não encontrado."

        r = rows[0]
        valor_total = float(r["valor_total_contrato"])
        consumido   = float(r["valor_total_consumido"])
        saldo       = float(r["saldo_disponivel"])
        qtd_os      = r["qtd_ordens_servico"]
        pct = (consumido / valor_total * 100) if valor_total > 0 else 0

        return (
            f"Contrato {r['num_numero_contrato_con']} — {r['dsc_empresa_contratada_con']}\n"
            f"Valor total:      R$ {valor_total:,.2f}\n"
            f"Valor consumido:  R$ {consumido:,.2f} ({pct:.1f}%)\n"
            f"Saldo disponível: R$ {saldo:,.2f}\n"
            f"Ordens de serviço vinculadas: {qtd_os}"
        )
    except Exception as exc:
        return f"Erro ao consultar saldo: {exc}"
    

@mcp.tool()
@log_tool_execution
def consultar_recursos_contrato(
    numero_contrato: str,
    unidade_medida: Optional[str] = None,
) -> str:
    """
    Retorna os itens da tabela de preços de um contrato com saldo calculado
    em quantidade de unidade (UST, UST-A, UST-B, LICENÇA, etc.) e em reais,
    cruzando com as Ordens de Serviço registradas.
 
    Use quando o usuário perguntar:
      - "Quantas UST restam no contrato X?"
      - "Qual o valor unitário da UST-B do contrato 29/2024?"
      - "Quantas licenças Enterprise Standard foram contratadas?"
      - "Qual o saldo em unidade do contrato da Golden?"
 
    Args:
        numero_contrato: Número exato do contrato (ex: "03/2024", "29/2024").
        unidade_medida:  Filtrar por unidade específica (ex: "UST", "UST-B",
                         "LICENÇA"). Se omitido, retorna todos os itens.
    """
    # 1. Recursos da tabela de preços
    sql_recursos = """
        SELECT
            cre.pk_id_cre,
            cre.num_seq_recurso_cre            AS seq,
            cre.dsc_especificacao_recurso_cre  AS especificacao,
            cre.dsc_chave_recurso_cre          AS chave,
            cre.dsc_unidade_medida_recurso_cre AS unidade,
            cre.qtd_quantidade_recurso_cre     AS qtd_contratada,
            cre.vlr_valor_unitario_recurso_cre AS vlr_unit,
            cre.vlr_valor_total_recurso_cre    AS vlr_total_cre,
            con.dsc_empresa_contratada_con     AS empresa
        FROM tb_contrato_recurso_cre cre
        JOIN tb_contrato_con con ON con.pk_id_con = cre.pk_id_con
        WHERE cre.num_numero_contrato_cre = :contrato
    """
    params: dict = {"contrato": numero_contrato}
    if unidade_medida:
        sql_recursos += " AND cre.dsc_unidade_medida_recurso_cre = :unidade"
        params["unidade"] = unidade_medida
    sql_recursos += " ORDER BY cre.num_seq_recurso_cre"
 
    # 2. Consumo real por recurso:
    #    - Se o recurso tem dsc_chave_recurso_cre → cruzar por LIKE na especificacao da OS
    #    - Se não tem chave → cruzar pela unidade de medida
    #    Feito em Python após buscar o consumo bruto por (unidade, especificacao).
    sql_consumo = """
        SELECT
            osi.dsc_unidade_medida_item_os_osi         AS unidade,
            osi.dsc_especificacao_item_os_osi          AS especificacao,
            COALESCE(SUM(osi.qtd_quantidade_item_os_osi), 0)  AS qtd_consumida,
            COALESCE(SUM(osi.vlr_valor_total_item_os_osi), 0) AS vlr_consumido
        FROM tb_ordem_servico_item_osi osi
        JOIN tb_ordem_servico_ord ord ON ord.pk_id_ord = osi.pk_id_ord
        JOIN tb_contrato_con con ON con.pk_id_con = ord.pk_id_con
        WHERE con.num_numero_contrato_con = :contrato
          AND COALESCE(ord.log_status_ord, 'ativo') != 'cancelado'
        GROUP BY osi.dsc_unidade_medida_item_os_osi, osi.dsc_especificacao_item_os_osi
    """
 
    recursos = query(sql_recursos, params)
    consumos = query(sql_consumo, {"contrato": numero_contrato})
 
    if not recursos:
        motivo = f"unidade '{unidade_medida}'" if unidade_medida else "nenhum item"
        return (
            f"Nenhum recurso encontrado para o contrato '{numero_contrato}' "
            f"({motivo}). Verifique se a migration 005 foi aplicada."
        )
 
    # Índice de consumo: lista de (unidade, especificacao, qtd, vlr)
    consumo_bruto = [
        {
            "unidade":     c["unidade"],
            "especificacao": (c["especificacao"] or ""),
            "qtd":         float(c["qtd_consumida"]),
            "vlr":         float(c["vlr_consumido"]),
        }
        for c in consumos
    ]
 
    def calcular_consumo(recurso: dict) -> tuple[float, float]:
        """
        Retorna (qtd_consumida, vlr_consumido) para um recurso.
        Se tem chave → soma os itens de OS cuja especificacao contenha a chave.
        Se não tem chave → soma os itens de OS com mesma unidade.
        """
        chave = recurso["chave"]
        unidade = recurso["unidade"]
        qtd_total = 0.0
        vlr_total = 0.0
        for c in consumo_bruto:
            if chave:
                # cruzamento preciso: unidade E chave dentro da especificacao da OS
                if c["unidade"] == unidade and chave in c["especificacao"]:
                    qtd_total += c["qtd"]
                    vlr_total += c["vlr"]
            else:
                # cruzamento simples: apenas unidade
                if c["unidade"] == unidade:
                    qtd_total += c["qtd"]
                    vlr_total += c["vlr"]
        return qtd_total, vlr_total
 
    empresa = recursos[0]["empresa"]
    linhas = [f"=== RECURSOS DO CONTRATO {numero_contrato} — {empresa} ==="]
 
    total_vlr_contratado = 0.0
    total_vlr_consumido  = 0.0
    total_vlr_saldo      = 0.0
 
    for r in recursos:
        qtd_c       = float(r["qtd_contratada"])
        vlr_unit    = float(r["vlr_unit"])
        vlr_total_c = float(r["vlr_total_cre"])
        qtd_cons, vlr_cons = calcular_consumo(r)
        qtd_saldo   = qtd_c - qtd_cons
        vlr_saldo   = vlr_total_c - vlr_cons
        pct         = (qtd_cons / qtd_c * 100) if qtd_c else 0.0
 
        total_vlr_contratado += vlr_total_c
        total_vlr_consumido  += vlr_cons
        total_vlr_saldo      += vlr_saldo
 
        desc = (r["especificacao"] or "")
        desc_curta = desc[:75] + "..." if len(desc) > 75 else desc
 
        linhas.append(
            f"\n[{r['seq']}] {desc_curta}\n"
            f"    Unidade:           {r['unidade']}\n"
            f"    Qtd Contratada:    {qtd_c:>12,.2f}\n"
            f"    Valor Unitário R$: {vlr_unit:>12,.2f}\n"
            f"    Qtd Consumida:     {qtd_cons:>12,.2f}\n"
            f"    Saldo Qtd:         {qtd_saldo:>12,.2f}\n"
            f"    Saldo R$:          {vlr_saldo:>16,.2f}\n"
            f"    % Uso:             {pct:.1f}%"
        )
 
    linhas.append(
        f"\n{'─'*55}\n"
        f"TOTAL: Contratado R$ {total_vlr_contratado:,.2f} | "
        f"Consumido R$ {total_vlr_consumido:,.2f} | "
        f"Saldo R$ {total_vlr_saldo:,.2f}"
    )
 
    if numero_contrato == "21/2021":
        linhas.append(
            "\n⚠ Contrato 21/2021 (ELOGROUP): tabela de preços não inserida. "
            "Execute o INSERT em tb_contrato_recurso_cre quando o PDF estiver disponível."
        )
 
    return "\n".join(linhas)


@mcp.tool()
@log_tool_execution
def listar_ordens_servico_contrato(
    numero_contrato: str,
    incluir_itens: bool = True,
) -> str:
    """
    Lista todas as Ordens de Serviço (OS) emitidas para um contrato específico,
    com seus itens e valores. Use quando o usuário perguntar:
      - "Quais ordens de serviço o contrato 03/2024 tem?"
      - "Liste as OS do contrato da PORTFOLIO"
      - "Quais os itens da OS 12/2026?"
      - "Quantas OS foram emitidas para o contrato 21/2021?"

    Args:
        numero_contrato: Número exato do contrato (ex: "03/2024", "29/2024").
        incluir_itens:   Se True (padrão), detalha os itens de cada OS.
                         Se False, retorna apenas o resumo das OS (mais rápido
                         para contratos com muitas OS).
    """
    sql_os = """
        SELECT
            ord.pk_id_ord,
            ord.num_numero_os_ord,
            ord.dat_emissao_os_ord,
            ord.nom_cliente_os_ord,
            ord.nom_fornecedor_os_ord,
            ord.log_status_ord,
            con.dsc_empresa_contratada_con AS empresa
        FROM tb_ordem_servico_ord ord
        JOIN tb_contrato_con con ON con.pk_id_con = ord.pk_id_con
        WHERE con.num_numero_contrato_con = :contrato
        ORDER BY ord.pk_id_ord
    """
    ordens = query(sql_os, {"contrato": numero_contrato})

    if not ordens:
        return (
            f"Nenhuma Ordem de Serviço encontrada para o contrato '{numero_contrato}'. "
            f"Verifique se o número do contrato está correto ou se já existem OS cadastradas."
        )

    empresa = ordens[0]["empresa"]
    ids_ord = [str(o["pk_id_ord"]) for o in ordens]

    itens_por_os: dict[int, list] = {}
    if incluir_itens:
        sql_itens = f"""
            SELECT
                osi.pk_id_ord,
                osi.num_seq_item_os_osi,
                osi.dsc_especificacao_item_os_osi,
                osi.dsc_unidade_medida_item_os_osi,
                osi.qtd_quantidade_item_os_osi,
                osi.vlr_valor_unitario_item_os_osi,
                osi.vlr_valor_total_item_os_osi
            FROM tb_ordem_servico_item_osi osi
            WHERE osi.pk_id_ord IN ({','.join(ids_ord)})
            ORDER BY osi.pk_id_ord, osi.num_seq_item_os_osi
        """
        itens = query(sql_itens, {})
        for it in itens:
            itens_por_os.setdefault(it["pk_id_ord"], []).append(it)

    linhas = [f"=== ORDENS DE SERVIÇO DO CONTRATO {numero_contrato} — {empresa} ==="]
    total_geral = 0.0

    for o in ordens:
        itens_desta_os = itens_por_os.get(o["pk_id_ord"], [])
        total_os = sum(float(i["vlr_valor_total_item_os_osi"]) for i in itens_desta_os)
        total_geral += total_os

        emissao = o["dat_emissao_os_ord"] or "não informada"
        status = o["log_status_ord"] or "ativo"

        linhas.append(
            f"\nOS {o['num_numero_os_ord']} (id={o['pk_id_ord']}) | "
            f"Status: {status} | Emissão: {emissao} | Total: R$ {total_os:,.2f}"
        )

        if incluir_itens:
            if itens_desta_os:
                for it in itens_desta_os:
                    desc = (it["dsc_especificacao_item_os_osi"] or "")
                    desc_curta = desc[:70] + "..." if len(desc) > 70 else desc
                    linhas.append(
                        f"    [{it['num_seq_item_os_osi']}] {desc_curta}\n"
                        f"        {it['dsc_unidade_medida_item_os_osi']} × "
                        f"{float(it['qtd_quantidade_item_os_osi']):,.2f} × "
                        f"R$ {float(it['vlr_valor_unitario_item_os_osi']):,.2f} = "
                        f"R$ {float(it['vlr_valor_total_item_os_osi']):,.2f}"
                    )
            else:
                linhas.append("    (sem itens cadastrados)")

    linhas.append(
        f"\n{'─'*55}\n"
        f"Total de OS: {len(ordens)} | Valor total consumido: R$ {total_geral:,.2f}"
    )

    return "\n".join(linhas)


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