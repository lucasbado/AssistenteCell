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

import logging
from typing import Optional

from modelos.catalogo import EntidadeSemantica
from servicos.memoria_semantica import MemoriaSemantica
from servicos.llm import ServicoLLM

logger = logging.getLogger(__name__)

# servicos/catalogo_semantico.py

class CatalogoSemantico:
    def __init__(self):
        # Importações adiadas para evitar dependências circulares durante a inicialização.
        from servicos.memoria_semantica import MemoriaSemantica
        from servicos.llm import ServicoLLM
        self.memoria = MemoriaSemantica()
        self.llm = ServicoLLM()

    async def obter_artista(self, artista: str) -> Optional[EntidadeSemantica]:
        """
        Obtém uma entidade de artista. Se não existir, usa a LLM para classificar,
        salva no banco e retorna.
        """
        # 🌟 CRUCIAL: O 'await' garante que o Pydantic / Dicionário seja resolvido aqui
        entidade = await self.memoria.buscar("ARTISTA", artista)
        if not entidade:
            try:
                # A LLM é acionada como último recurso para enriquecer o conhecimento do sistema.
                logger.info(f"Artista '{artista}' não encontrado no catálogo. Classificando com LLM...")
                entidade = await self.llm.classificar_artista(artista)
                await self.memoria.salvar(entidade)
                logger.info(f"Artista '{artista}' classificado e salvo na Memória Semântica.")
            except Exception as e:
                logger.error(f"Erro ao classificar artista '{artista}' com LLM: {e}")
                return None # Retorna None para não quebrar o agente consumidor.
        return entidade

    async def obter_app(self, pacote: str) -> Optional[EntidadeSemantica]:
        """
        Obtém uma entidade de app. Se não existir, usa a LLM para classificar,
        salva no banco e retorna.
        """
        # 🌟 CRUCIAL: Garante o desempacotamento assíncrono do modelo do banco
        entidade = await self.memoria.buscar("APP", pacote)
        if not entidade:
            try:
                logger.info(f"App '{pacote}' não encontrado no catálogo. Classificando com LLM...")
                entidade = await self.llm.classificar_app(pacote)
                await self.memoria.salvar(entidade)
                logger.info(f"App '{pacote}' classificado e salvo na Memória Semântica.")
            except Exception as e:
                logger.error(f"Erro ao classificar app '{pacote}' com LLM: {e}")
                return None
        return entidade

    async def obter_contato(self, contato_nome: str) -> Optional[EntidadeSemantica]:
        # 🌟 CRUCIAL
        entidade = await self.memoria.buscar("CONTATO", contato_nome)
        if not entidade:
            # O método classificar_contato não usa LLM, é seguro, rápido e não precisa de try/except.
            entidade = await self.llm.classificar_contato(contato_nome)
            await self.memoria.salvar(entidade)
        return entidade


catalogo = CatalogoSemantico()