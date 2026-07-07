"""
api/eventos.py
"""

import logging
import json
from fastapi import APIRouter, status, Request, HTTPException
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Any, Optional
from api.websocket import central_alertas

from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, OrigemEvento
from core.motor_atencao import pipeline_atencao
from core.kernel import kernel

router = APIRouter()
logger = logging.getLogger(__name__)

class RequestEvento(BaseModel):
    categoria: str
    pacote: str
    conteudo: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def _unificar_payload(cls, data: Any) -> Any:
        """Garante compatibilidade com o cliente que envia 'atributos' em vez de 'conteudo'."""
        if isinstance(data, dict):
            # Se 'atributos' existe e 'conteudo' não, movemos o valor.
            if "atributos" in data and "conteudo" not in data:
                data["conteudo"] = data.pop("atributos")
        return data

@router.post("/eventos", status_code=status.HTTP_202_ACCEPTED)
async def receber_evento(request: Request):
    # --- DEBUGGING: Log do corpo bruto da requisição ---
    try:
        body = await request.json()
        logger.info(
            f"Recebido payload em /eventos: {json.dumps(body, indent=2, ensure_ascii=False)}"
        )
        evento = RequestEvento.model_validate(body)
    except json.JSONDecodeError:
        logger.error(
            "Erro de decodificação de JSON: o corpo da requisição não é um JSON válido."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corpo da requisição não é um JSON válido.",
        )
    except ValidationError as e:
        logger.error(f"Erro de validação Pydantic em /eventos. Detalhes: {e.errors()}")
        # Re-lança a exceção para que o FastAPI possa gerar a resposta 422 detalhada.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )

    # 1. Cria o evento oficial do Kernel
    evento_canonico = EventoCanonico(
        categoria=CategoriaEvento(evento.categoria.upper()),
        origem=OrigemEvento.ANDROID,
        pacote=evento.pacote,
        payload=evento.conteudo,  # <--- A CORREÇÃO É AQUI! Pegamos o 'conteudo' do Android e chamamos de 'payload' internamente
    )

    # 2. O Pipeline de Atenção avalia e enriquece o evento
    resultado_atencao = pipeline_atencao.avaliar(evento_canonico)
    if not resultado_atencao:
        return {"status": "ignorado_pelo_pipeline_de_atencao"}

    evento_canonico.metadados["atencao"] = resultado_atencao.model_dump()

    # 3. Entrega ao Kernel Cognitivo
    await kernel.publicar(evento_canonico)

    return {"status": "enfileirado", "id": evento_canonico.id}
