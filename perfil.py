from fastapi import APIRouter
import logging

from api.v1.dto.perfil_dto import PerfilCognitivoDTO
from api.v1.servicos.servico_perfil import servico_perfil

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/perfil",
    response_model=PerfilCognitivoDTO,
    summary="Retorna o perfil cognitivo do usuário",
    description="Agrega todas as informações aprendidas sobre os hábitos e preferências do usuário em uma única visão consolidada e narrativa."
)
async def get_perfil_cognitivo():
    """
    Endpoint que constrói e retorna o perfil cognitivo do usuário.
    """
    logger.info("Recebida requisição para GET /perfil")
    return await servico_perfil.gerar_perfil_cognitivo()