"""
api/memoria.py

Endpoints para visualizar a Memória Semântica do sistema.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Any, Optional
from sqlalchemy.future import select

from banco.database import AsyncSessionLocal
from banco.models import EntidadeSemanticaDB

router = APIRouter(tags=["Memória"])

class SemanticNodeDTO(BaseModel):
    id: str # Convertido para string para bater com o Android
    key: str # Chave original (ex: pacote do app) para o Android resolver ícones
    title: str
    type: str
    attributes: dict[str, Any]

class MemoryMapResponse(BaseModel):
    nodes: List[SemanticNodeDTO]

@router.get("/mapa", response_model=MemoryMapResponse)
async def obter_mapa_semantico():
    """
    Retorna todas as entidades conhecidas na Memória Semântica.
    Isso serve para construir o 'mapa mental' no frontend.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(EntidadeSemanticaDB)
        resultado = await session.execute(stmt)
        entidades = resultado.scalars().all()

        nodes = []
        for e in entidades:
            # Extrai um título amigável baseado no tipo
            dados = e.dados_json or {}
            atributos = dados.get("atributos", {})
            
            title = e.chave
            if e.tipo == "APP":
                title = atributos.get("nome", e.chave)
            elif e.tipo == "CONTATO":
                title = atributos.get("nome", e.chave)
            elif e.tipo == "ARTISTA":
                title = e.chave 

            nodes.append(SemanticNodeDTO(
                id=str(e.id),
                key=e.chave, # Enviamos a chave bruta (pacote)
                title=title, # Enviamos o nome amigável
                type=e.tipo,
                attributes=atributos
            ))

        return MemoryMapResponse(nodes=nodes)
