from fastapi import APIRouter
import logging
from .dto import TimelineDTO
from .servico import servico_timeline

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/timeline",
    response_model=TimelineDTO,
    summary="Retorna a linha do tempo inteligente de eventos",
    tags=["Timeline"]
)
async def get_timeline():
    """
    Endpoint que retorna uma lista de eventos recentes processados pelo
    sistema, já transformados em uma narrativa para exibição no cliente.
    """
    logger.info("Recebida requisição para GET /timeline")
    return await servico_timeline.gerar_timeline()