"""
api/eventos.py
"""

import logging
from fastapi import APIRouter, status, Request, HTTPException
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Any, Optional
from api.websocket import central_alertas

# Imports for deduplication
import json
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, OrigemEvento
from core.motor_atencao import pipeline_atencao
from core.kernel import kernel

router = APIRouter()
logger = logging.getLogger(__name__)

DEDUPLICATION_CACHE = OrderedDict()
CACHE_TTL_SECONDS = 10  # Ignore duplicates received within 10 seconds.


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


def _is_duplicate(evento: RequestEvento) -> bool:
    """Checks if a similar event was received recently."""
    now = datetime.now(timezone.utc)

    # 1. Create a stable, hashable key for the event
    conteudo_str = json.dumps(evento.conteudo, sort_keys=True)
    event_key = (evento.categoria, evento.pacote, conteudo_str)

    # 2. Clean up old entries from the cache
    keys_to_delete = []
    for key, timestamp in DEDUPLICATION_CACHE.items():
        if now - timestamp > timedelta(seconds=CACHE_TTL_SECONDS):
            keys_to_delete.append(key)
        else:
            break
    for key in keys_to_delete:
        del DEDUPLICATION_CACHE[key]

    # 3. Check if the event is a duplicate
    if event_key in DEDUPLICATION_CACHE:
        DEDUPLICATION_CACHE.move_to_end(event_key)  # Refresh
        return True

    # 4. If not a duplicate, add it to the cache
    DEDUPLICATION_CACHE[event_key] = now
    return False


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

    # 0. Deduplication check
    if _is_duplicate(evento):
        return {"status": "ignorado_como_duplicado"}

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

    # 🔥 AQUI ESTÁ A CORREÇÃO: Disparar de volta para o telemóvel via WebSocket!
    # Criamos o payload que o seu Android espera receber (titulo e mensagem/texto)
    payload_alerta = {
        "titulo": f"Inferência: {evento_canonico.categoria.value}",
        "mensagem": f"Processado evento do pacote {evento_canonico.pacote}",
    }

    # Chama a central de alertas para empurrar o dado no canal WebSocket ativo
    await central_alertas.enviar_alerta(payload_alerta)

    return {"status": "enfileirado", "id": evento_canonico.id}
