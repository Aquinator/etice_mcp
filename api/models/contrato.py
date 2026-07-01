# api/models/contrato.py — versão final
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


def _para_str(v: Any) -> Optional[str]:
    """Converte qualquer valor (date, datetime, int, str, None) para str."""
    if v is None:
        return None
    return str(v)


class CriarContratoInput(BaseModel):
    num_numero_contrato_con: str = Field(..., max_length=50)
    dsc_empresa_contratada_con: str = Field(..., max_length=255)
    dsc_objeto_contrato_con: Optional[str] = None
    tip_modalidade_con: Optional[str] = Field(None, max_length=50)
    vlr_valor_total_contrato_con: Decimal = Field(..., ge=0, decimal_places=2)
    dat_data_assinatura_con: Optional[str] = None
    dat_prazo_vigencia_meses_con: Optional[str] = None
    data_fim_vigencia_con: Optional[str] = None
    dsc_nome_gestor_con: Optional[str] = Field(None, max_length=255)
    pk_id_emp: Optional[int] = None
    pk_id_mod: Optional[int] = None
    dsc_usuario_con: str = Field(..., max_length=100)


class EditarContratoInput(BaseModel):
    dsc_objeto_contrato_con: Optional[str] = None
    vlr_valor_total_contrato_con: Optional[Decimal] = Field(None, ge=0)
    data_fim_vigencia_con: Optional[str] = None
    dsc_nome_gestor_con: Optional[str] = Field(None, max_length=255)
    log_status_con: Optional[str] = Field(None, max_length=30)
    dsc_usuario_con: str = Field(..., max_length=100)


class ContratoOut(BaseModel):
    """
    Schema de saída. Campos de data/prazo são Optional[str] com coerção
    automática para tolerar o banco que mistura date, datetime e texto livre.
    """
    pk_id_con: int
    num_numero_contrato_con: str
    dsc_empresa_contratada_con: str
    dsc_objeto_contrato_con: Optional[str] = None
    tip_modalidade_con: Optional[str] = None
    vlr_valor_total_contrato_con: Optional[Decimal] = None
    dat_data_assinatura_con: Optional[str] = None
    dat_prazo_vigencia_meses_con: Optional[str] = None
    data_fim_vigencia_con: Optional[str] = None
    dsc_nome_gestor_con: Optional[str] = None
    log_status_con: Optional[str] = None
    pk_id_emp: Optional[int] = None
    pk_id_mod: Optional[int] = None
    dat_criado_em_con: Optional[str] = None
    dat_atualizado_em_con: Optional[str] = None
    dsc_usuario_con: Optional[str] = None

    model_config = {"from_attributes": True}

    # Coerce qualquer tipo que o banco entregue para str
    @field_validator(
        "dat_data_assinatura_con",
        "dat_prazo_vigencia_meses_con",
        "data_fim_vigencia_con",
        "dat_criado_em_con",
        "dat_atualizado_em_con",
        mode="before",
    )
    @classmethod
    def coerce_to_str(cls, v: Any) -> Optional[str]:
        return _para_str(v)