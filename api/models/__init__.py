# api/models/__init__.py
# Re-exporta os schemas originais para não quebrar imports existentes
from api.models.chat import (
    SessaoCriada, SessaoInfo, ChatRequest,
    MensagemHistorico, HistoricoResponse, HealthResponse
)
from api.models.contrato import CriarContratoInput, EditarContratoInput, ContratoOut
from api.models.ordem_servico import CriarOSInput, EditarOSInput, OSOut, OSItemInput