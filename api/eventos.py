"""
api/eventos.py
"""
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Any, Optional

from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, OrigemEvento
from core.motor_atencao import pipeline_atencao
from core.kernel import kernel

router = APIRouter()

class RequestEvento(BaseModel):
    categoria: str
    pacote: str
    conteudo: dict[str, Any]

@router.post("/eventos", status_code=status.HTTP_202_ACCEPTED)
async def receber_evento(evento: RequestEvento):
    # 1. Cria o evento oficial do Kernel
    evento_canonico = EventoCanonico(
        categoria=CategoriaEvento(evento.categoria.upper()),
        origem=OrigemEvento.ANDROID,
        pacote=evento.pacote,
        payload=evento.conteudo  # <--- A CORREÇÃO É AQUI! Pegamos o 'conteudo' do Android e chamamos de 'payload' internamente
    )

    # 2. O Pipeline de Atenção avalia e enriquece o evento
    resultado_atencao = pipeline_atencao.avaliar(evento_canonico)
    if not resultado_atencao:
        return {"status": "ignorado_pelo_pipeline_de_atencao"}
    
    evento_canonico.metadados["atencao"] = resultado_atencao.model_dump()

    # 3. Entrega ao Kernel Cognitivo (Event Bus)
    await kernel.publicar(evento_canonico)

    return {"status": "enfileirado", "id": evento_canonico.id}