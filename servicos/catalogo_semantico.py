"""
servicos/catalogo_semantico.py

Responsável por fornecer conhecimento semântico aos agentes.

Fluxo:

RAM
 ↓
SQLite
 ↓
LLM
 ↓
Persistência
"""

from __future__ import annotations

from typing import Optional

from modelos.catalogo import EntidadeSemantica
from servicos.memoria_semantica import MemoriaSemantica
from servicos.llm import ServicoLLM


# servicos/catalogo_semantico.py

class CatalogoSemantico:
    def __init__(self):
        from servicos.memoria_semantica import MemoriaSemantica
        self.memoria = MemoriaSemantica()

    async def obter_artista(self, artista: str):
        # 🌟 CRUCIAL: O 'await' garante que o Pydantic / Dicionário seja resolvido aqui
        entidade = await self.memoria.buscar("ARTISTA", artista)
        return entidade

    async def obter_app(self, pacote: str):
        # 🌟 CRUCIAL: Garante o desempacotamento assíncrono do modelo do banco
        entidade = await self.memoria.buscar("APP", pacote)
        return entidade

    async def obter_contato(self, contato_nome: str):
        # 🌟 CRUCIAL
        entidade = await self.memoria.buscar("CONTATO", contato_nome)
        return entidade


catalogo = CatalogoSemantico()