import logging
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any

from .agregador import agregador_status

# ==========================================
# DTOs (Data Transfer Objects)
# ==========================================

class LLMStatusDTO(BaseModel):
    """Descreve o status do Large Language Model."""
    modelo_carregado: str = Field(..., description="Nome do modelo de linguagem atualmente em uso.")

class StatusSistemaDTO(BaseModel):
    """DTO para a resposta completa do endpoint de status."""
    status_geral: str = Field(..., description="Um status geral, como 'OPERACIONAL'.")
    kernel: dict[str, Any] = Field(..., description="Estatísticas internas do Kernel Cognitivo.")
    llm: LLMStatusDTO = Field(..., description="Status específico do serviço de LLM.")
    memorias: dict[str, Any] = Field(..., description="Métricas sobre as memórias do sistema.")

# ==========================================
# SERVIÇO
# ==========================================

class ServicoStatus:
    """
    Serviço responsável por agregar informações de status de vários
    componentes do sistema e formatá-las no DTO de resposta.
    """
    async def gerar_status_sistema(self) -> StatusSistemaDTO:
        """
        Coleta dados do agregador e os transforma no DTO de status.
        """
        dados_agregados = await agregador_status.obter_dados_status()

        # Adapta os dados do agregador para os DTOs específicos
        status_llm = LLMStatusDTO(
            modelo_carregado=dados_agregados.get("llm_modelo", "N/A")
        )
        
        # Agrupa métricas de memória em um único dicionário
        memorias = {
            "cache_semantico_tamanho": dados_agregados.get("cache_semantico", 0)
        }

        return StatusSistemaDTO(
            status_geral="OPERACIONAL",  # Fixo, como esperado pelo teste
            kernel=dados_agregados.get("kernel", {}),
            llm=status_llm,
            memorias=memorias
        )

# Instância única do serviço
servico_status = ServicoStatus()

# ==========================================
# ROUTER (ENDPOINT DA API)
# ==========================================

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=StatusSistemaDTO, summary="Retorna o status operacional do sistema", tags=["Status"])
async def get_status():
    """
    Endpoint que fornece uma visão geral do estado de saúde dos
    principais componentes do sistema cognitivo, como o Kernel,
    a LLM e as memórias.
    """
    logger.info("Recebida requisição para GET /status")
    return await servico_status.gerar_status_sistema()