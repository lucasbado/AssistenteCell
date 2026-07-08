"""
agentes/agente_musica.py

Agente especializado em processar eventos de mídia e gerar interações
relacionadas a música, como rotinas e artistas favoritos.
"""
import logging
from datetime import datetime

from core.evento import EventoCanonico
from core.tipos import PrioridadeEvento, TipoAcao, CategoriaEvento
from core.kernel import kernel
from servicos.catalogo_semantico import catalogo
from servicos.memoria_perfil import memoria_perfil

logger = logging.getLogger(__name__)

def _get_time_slot(timestamp: datetime) -> str:
    """Determina o período do dia com base no timestamp."""
    hour = timestamp.hour
    if 6 <= hour < 12:
        return "MANHA"
    if 12 <= hour < 18:
        return "TARDE"
    if 18 <= hour < 24:
        return "NOITE"
    return "MADRUGADA"

class AgenteMusica:
    async def processar(self, evento: EventoCanonico):
        artista = evento.payload.get("artista")
        if not artista:
            return

        # Obter dados de ambas as memórias para tomar a decisão
        entidade = await catalogo.obter_artista(artista)
        perfil_artista = await memoria_perfil.obter_perfil_artista(artista) # Perfil genérico
        horario_atual = _get_time_slot(evento.timestamp)

        # Decisão 1: Rotina Musical (prioridade alta)
        if entidade:
            insights = entidade.atributos.get("insights", {})
            horario_rotina = insights.get("rotina_musical")
            if horario_rotina and horario_rotina == horario_atual:
                await kernel.publicar(
                    evento.clonar(
                        categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                        acao=TipoAcao.INTENCAO_INTERACAO,
                        prioridade=PrioridadeEvento.NORMAL,
                        payload={
                            "texto": f"Começando o(a) {horario_rotina.title()} com {artista}? Boa escolha!",
                            "titulo": "Sua Rotina Musical",
                        },
                    )
                )
                return # Ação tomada, não continuar

        # Decisão 2: Artista favorito (genérico, prioridade mais baixa)
        if perfil_artista and perfil_artista.confianca > 0.6:
            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    prioridade=PrioridadeEvento.NORMAL,
                    payload={
                        "texto": f"Vejo que você curte bastante {artista}. Ótima escolha! 🎵",
                        "titulo": "Assistente Musical",
                    },
                )
            )