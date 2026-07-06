"""
agentes/agente_perfil.py
"""
from __future__ import annotations
from core.evento import EventoCanonico
from servicos.catalogo_semantico import catalogo
from servicos.memoria_perfil import MemoriaPerfil

class AgentePerfil:

    async def processar(self, evento: EventoCanonico):
        if evento.categoria == "MEDIA":
            await self._processar_midia(evento)
        elif evento.categoria == "APP_FOREGROUND":
            await self._processar_app(evento)

    async def _processar_midia(self, evento: EventoCanonico):
        artista_nome = evento.payload.get("artista")
        if not artista_nome:
            return

        # 1. Consulta o mundo (Semântica) via Ollama/Cache
        entidade_artista = catalogo.obter_artista(artista_nome)
        genero = entidade_artista.atributos.get("genero")

        # 2. Atualiza o usuário (Perfil)
        perfil.incrementar("ARTISTA_FAVORITO", artista_nome)
        if genero:
            perfil.incrementar("GENERO_MUSICAL", genero)

    async def _processar_app(self, evento: EventoCanonico):
        pacote = evento.pacote
        
        # 1. Consulta o que é esse app
        entidade_app = await catalogo.obter_app(pacote)
        categoria_app = entidade_app.atributos.get("categoria")

        # 2. Atualiza o hábito do usuário
        perfil.incrementar("USO_APP", pacote)
        if categoria_app:
            perfil.incrementar("USO_CATEGORIA_APP", categoria_app)
