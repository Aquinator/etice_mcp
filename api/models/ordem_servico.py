from datetime import date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

class OSItemInput(BaseModel):
    num_seq_item_os_osi: int = Field(..., ge=1)
    dsc_especificacao_item_os_osi: Optional[str] = None
    dsc_unidade_medida_item_os_osi: Optional[str] = Field(None, max_length=30)
    qtd_quantidade_item_os_osi: Decimal = Field(default=1, ge=0, decimal_places=4)
    qtd_frequencia_item_os_osi: Optional[str] = Field(None, max_length=50)
    vlr_valor_unitario_item_os_osi: Decimal = Field(..., ge=0, decimal_places=2)
    vlr_valor_total_item_os_osi: Decimal = Field(..., ge=0, decimal_places=2)

class CriarOSInput(BaseModel):
    num_numero_os_ord: str = Field(..., max_length=50)
    num_numero_contrato_ord: str = Field(..., max_length=50)  # campo de exibição
    id_contrato: int = Field(..., ge=1)                       # FK real
    dat_emissao_os_ord: Optional[date] = None
    nom_cliente_os_ord: Optional[str] = Field(None, max_length=255)
    nom_fornecedor_os_ord: Optional[str] = Field(None, max_length=255)
    dat_inicio_vigencia_os_ord: Optional[date] = None
    dat_fim_vigencia_os_ord: Optional[date] = None
    dsc_usuario_ord: str = Field(..., max_length=100)
    itens: List[OSItemInput] = Field(default_factory=list)

class EditarOSInput(BaseModel):
    dat_inicio_vigencia_os_ord: Optional[date] = None
    dat_fim_vigencia_os_ord: Optional[date] = None
    log_status_ord: Optional[str] = Field(None, max_length=30)
    dsc_usuario_ord: str = Field(..., max_length=100)

class OSOut(BaseModel):
    pk_id_ord: int
    num_numero_os_ord: str
    num_numero_contrato_ord: str
    pk_id_con: int
    log_status_ord: Optional[str]
    dat_criado_em_ord: Optional[str]

    class Config:
        from_attributes = True