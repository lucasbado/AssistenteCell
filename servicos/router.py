from fastapi import APIRouter
import logging
from .dto import TimelineDTO
from .servico import servico_timeline

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/",
    response_model=TimelineDTO,
    summary="Retorna o histórico recente de eventos",
    tags=["Timeline"]
)
async def get_timeline():
    """
    Endpoint que retorna a timeline de eventos processados,
    formatados como conhecimento para o usuário.
    """
    logger.info("Recebida requisição para GET /timeline")
    return await servico_timeline.gerar_timeline()
