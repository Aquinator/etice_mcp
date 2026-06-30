"""
api/routers/contratos.py — CRUD REST de Contratos
Sem LLM no caminho. Usa sac_writer.
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from api.models.contrato import CriarContratoInput, EditarContratoInput, ContratoOut
from api.db_writer import get_writer_engine
from api.services.saldo_service import obter_saldo_contrato

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.get("", response_model=list[ContratoOut])
async def listar_contratos_crud(limite: int = 20, offset: int = 0):
    engine = get_writer_engine()
    sql = text("""
        SELECT * FROM tb_contrato_con
        ORDER BY pk_id_con DESC
        LIMIT :limite OFFSET :offset
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limite": min(limite, 100), "offset": offset}).mappings().all()
    return [ContratoOut(**r) for r in rows]


@router.get("/{id}", response_model=ContratoOut)
async def obter_contrato(id: int):
    engine = get_writer_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM tb_contrato_con WHERE pk_id_con = :id"), {"id": id}
        ).mappings().first()
    if not row:
        raise HTTPException(404, "Contrato não encontrado")
    return ContratoOut(**row)


@router.get("/{id}/saldo")
async def saldo_contrato(id: int):
    """Endpoint dedicado ao SaldoCard do frontend."""
    engine = get_writer_engine()
    saldo = obter_saldo_contrato(engine, id)
    if not saldo:
        raise HTTPException(404, "Contrato não encontrado")
    return {
        "id_contrato": saldo.id_contrato,
        "numero_contrato": saldo.numero_contrato,
        "empresa": saldo.empresa,
        "valor_total": float(saldo.valor_total),
        "valor_consumido": float(saldo.valor_consumido),
        "saldo_disponivel": float(saldo.saldo_disponivel),
        "percentual_consumido": saldo.percentual_consumido,
        "criticidade": saldo.criticidade,
        "qtd_ordens_servico": saldo.qtd_ordens_servico,
    }


@router.post("", response_model=ContratoOut, status_code=status.HTTP_201_CREATED)
async def criar_contrato(dados: CriarContratoInput):
    engine = get_writer_engine()
    sql = text("""
        INSERT INTO tb_contrato_con (
            num_numero_contrato_con, dsc_empresa_contratada_con, dsc_objeto_contrato_con,
            tip_modalidade_con, vlr_valor_total_contrato_con, dat_data_assinatura_con,
            dat_prazo_vigencia_meses_con, data_fim_vigencia_con, dsc_nome_gestor_con,
            pk_id_emp, pk_id_mod, log_status_con, dsc_usuario_con
        ) VALUES (
            :numero, :empresa, :objeto, :modalidade, :valor, :assinatura,
            :prazo, :fim_vigencia, :gestor, :id_emp, :id_mod, 'ativo', :usuario
        )
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "numero": dados.num_numero_contrato_con,
            "empresa": dados.dsc_empresa_contratada_con,
            "objeto": dados.dsc_objeto_contrato_con,
            "modalidade": dados.tip_modalidade_con,
            "valor": dados.vlr_valor_total_contrato_con,
            "assinatura": dados.dat_data_assinatura_con,
            "prazo": dados.dat_prazo_vigencia_meses_con,
            "fim_vigencia": dados.data_fim_vigencia_con,
            "gestor": dados.dsc_nome_gestor_con,
            "id_emp": dados.pk_id_emp,
            "id_mod": dados.pk_id_mod,
            "usuario": dados.dsc_usuario_con,
        })
        novo_id = result.lastrowid
    return await obter_contrato(novo_id)


@router.put("/{id}", response_model=ContratoOut)
async def editar_contrato(id: int, dados: EditarContratoInput):
    engine = get_writer_engine()
    sql = text("""
        UPDATE tb_contrato_con SET
            dsc_objeto_contrato_con   = COALESCE(:objeto, dsc_objeto_contrato_con),
            vlr_valor_total_contrato_con = COALESCE(:valor, vlr_valor_total_contrato_con),
            data_fim_vigencia_con     = COALESCE(:fim_vigencia, data_fim_vigencia_con),
            dsc_nome_gestor_con       = COALESCE(:gestor, dsc_nome_gestor_con),
            log_status_con            = COALESCE(:status_con, log_status_con),
            dsc_usuario_con           = :usuario
        WHERE pk_id_con = :id
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "objeto": dados.dsc_objeto_contrato_con,
            "valor": dados.vlr_valor_total_contrato_con,
            "fim_vigencia": dados.data_fim_vigencia_con,
            "gestor": dados.dsc_nome_gestor_con,
            "status_con": dados.log_status_con,
            "usuario": dados.dsc_usuario_con,
            "id": id,
        })
    if result.rowcount == 0:
        raise HTTPException(404, "Contrato não encontrado")
    return await obter_contrato(id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_contrato(id: int):
    """
    ATENÇÃO: ON DELETE RESTRICT nas OSs bloqueia a exclusão se houver
    Ordens de Serviço vinculadas. A API retorna 409 com mensagem clara.
    """
    engine = get_writer_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM tb_contrato_con WHERE pk_id_con = :id"), {"id": id}
            )
        if result.rowcount == 0:
            raise HTTPException(404, "Contrato não encontrado")
    except Exception as exc:
        if "foreign key constraint" in str(exc).lower():
            raise HTTPException(
                409,
                "Não é possível excluir: existem Ordens de Serviço vinculadas a este contrato. "
                "Exclua as OSs primeiro."
            )
        raise