from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class CriarContratoInput(BaseModel):
    num_numero_contrato_con: str = Field(..., max_length=50)
    dsc_empresa_contratada_con: str = Field(..., max_length=255)
    dsc_objeto_contrato_con: Optional[str] = None
    tip_modalidade_con: Optional[str] = Field(None, max_length=50)
    vlr_valor_total_contrato_con: Decimal = Field(..., ge=0, decimal_places=2)
    dat_data_assinatura_con: Optional[date] = None
    dat_prazo_vigencia_meses_con: Optional[int] = Field(None, ge=1, le=600)
    data_fim_vigencia_con: Optional[date] = None
    dsc_nome_gestor_con: Optional[str] = Field(None, max_length=255)
    pk_id_emp: Optional[int] = None
    pk_id_mod: Optional[int] = None
    dsc_usuario_con: str = Field(..., max_length=100)

class EditarContratoInput(BaseModel):
    dsc_objeto_contrato_con: Optional[str] = None
    vlr_valor_total_contrato_con: Optional[Decimal] = Field(None, ge=0)
    data_fim_vigencia_con: Optional[date] = None
    dsc_nome_gestor_con: Optional[str] = Field(None, max_length=255)
    log_status_con: Optional[str] = Field(None, max_length=30)
    dsc_usuario_con: str = Field(..., max_length=100)

class ContratoOut(BaseModel):
    pk_id_con: int
    num_numero_contrato_con: str
    dsc_empresa_contratada_con: str
    vlr_valor_total_contrato_con: Decimal
    log_status_con: Optional[str]
    dat_criado_em_con: Optional[str]
    dat_atualizado_em_con: Optional[str]

    class Config:
        from_attributes = True