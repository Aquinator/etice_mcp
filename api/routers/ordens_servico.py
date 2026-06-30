"""
api/routers/ordens_servico.py — CRUD REST de Ordens de Serviço

Este router NUNCA é tocado pelo agente LangGraph. Conecta ao banco
via db_writer.py (usuário sac_writer). Todo payload é validado por
Pydantic antes de chegar ao SQL.
"""

from fastapi import APIRouter, HTTPException, status
from api.models.ordem_servico import CriarOSInput, EditarOSInput, OSOut
from api.db_writer import get_writer_engine
from sqlalchemy import text

router = APIRouter(prefix="/ordens-servico", tags=["ordens-servico"])


@router.get("", response_model=list[OSOut])
async def listar_os(id_contrato: int | None = None, limite: int = 20, offset: int = 0):
    engine = get_writer_engine()
    sql = "SELECT * FROM tb_ordem_servico_ord"
    params: dict = {"limite": min(limite, 100), "offset": offset}
    if id_contrato:
        sql += " WHERE pk_id_con = :id_con"
        params["id_con"] = id_contrato
    sql += " ORDER BY pk_id_ord DESC LIMIT :limite OFFSET :offset"
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [OSOut(**r) for r in rows]


@router.get("/{id}", response_model=OSOut)
async def obter_os(id: int):
    engine = get_writer_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM tb_ordem_servico_ord WHERE pk_id_ord = :id"), {"id": id}
        ).mappings().first()
    if not row:
        raise HTTPException(404, "Ordem de Serviço não encontrada")
    return OSOut(**row)


@router.post("", response_model=OSOut, status_code=status.HTTP_201_CREATED)
async def criar_os(dados: CriarOSInput):
    engine = get_writer_engine()
    sql_os = text("""
        INSERT INTO tb_ordem_servico_ord (
            num_numero_os_ord, num_numero_contrato_ord, dat_emissao_os_ord,
            nom_cliente_os_ord, nom_fornecedor_os_ord,
            dat_inicio_vigencia_os_ord, dat_fim_vigencia_os_ord,
            pk_id_con, dsc_usuario_ord
        ) VALUES (
            :numero, :numero_contrato, :emissao, :cliente, :fornecedor,
            :inicio, :fim, :id_con, :usuario
        )
    """)
    sql_item = text("""
        INSERT INTO tb_ordem_servico_item_osi (
            num_seq_item_os_osi, dsc_especificacao_item_os_osi,
            dsc_unidade_medida_item_os_osi, qtd_quantidade_item_os_osi,
            qtd_frequencia_item_os_osi, vlr_valor_unitario_item_os_osi,
            vlr_valor_total_item_os_osi, pk_id_ord, dsc_usuario_osi
        ) VALUES (
            :seq, :especificacao, :unidade, :qtd, :frequencia,
            :vlr_unit, :vlr_total, :id_ord, :usuario
        )
    """)
    with engine.begin() as conn:
        result = conn.execute(sql_os, {
            "numero": dados.num_numero_os_ord,
            "numero_contrato": dados.num_numero_contrato_ord,
            "emissao": dados.dat_emissao_os_ord,
            "cliente": dados.nom_cliente_os_ord,
            "fornecedor": dados.nom_fornecedor_os_ord,
            "inicio": dados.dat_inicio_vigencia_os_ord,
            "fim": dados.dat_fim_vigencia_os_ord,
            "id_con": dados.id_contrato,
            "usuario": dados.dsc_usuario_ord,
        })
        novo_id = result.lastrowid
        for item in dados.itens:
            conn.execute(sql_item, {
                "seq": item.num_seq_item_os_osi,
                "especificacao": item.dsc_especificacao_item_os_osi,
                "unidade": item.dsc_unidade_medida_item_os_osi,
                "qtd": item.qtd_quantidade_item_os_osi,
                "frequencia": item.qtd_frequencia_item_os_osi,
                "vlr_unit": item.vlr_valor_unitario_item_os_osi,
                "vlr_total": item.vlr_valor_total_item_os_osi,
                "id_ord": novo_id,
                "usuario": dados.dsc_usuario_ord,
            })
    return await obter_os(novo_id)


@router.put("/{id}", response_model=OSOut)
async def editar_os(id: int, dados: EditarOSInput):
    engine = get_writer_engine()
    sql = text("""
        UPDATE tb_ordem_servico_ord SET
            dat_inicio_vigencia_os_ord = COALESCE(:inicio, dat_inicio_vigencia_os_ord),
            dat_fim_vigencia_os_ord    = COALESCE(:fim, dat_fim_vigencia_os_ord),
            log_status_ord             = COALESCE(:status_ord, log_status_ord),
            dsc_usuario_ord            = :usuario
        WHERE pk_id_ord = :id
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "inicio": dados.dat_inicio_vigencia_os_ord,
            "fim": dados.dat_fim_vigencia_os_ord,
            "status_ord": dados.log_status_ord,
            "usuario": dados.dsc_usuario_ord,
            "id": id,
        })
    if result.rowcount == 0:
        raise HTTPException(404, "Ordem de Serviço não encontrada")
    return await obter_os(id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_os(id: int):
    """Os itens são excluídos em cascata (ON DELETE CASCADE na FK)."""
    engine = get_writer_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM tb_ordem_servico_ord WHERE pk_id_ord = :id"), {"id": id}
        )
    if result.rowcount == 0:
        raise HTTPException(404, "Ordem de Serviço não encontrada")