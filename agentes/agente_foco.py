"""
agentes/agente_foco.py

Agente especializado em processar eventos de uso de aplicativos.
Ele combina o evento atual com a memória de perfil e semântica para
gerar insights sobre hábitos, bem-estar e sugestões contextuais.
"""
import logging
import asyncio
from datetime import datetime

from core.evento import EventoCanonico
from core.tipos import PrioridadeEvento, TipoAcao, CategoriaEvento
from core.kernel import kernel
from servicos.catalogo_semantico import catalogo
from servicos.memoria_perfil import memoria_perfil
from modelos.catalogo import EntidadeSemantica
from banco.models import PerfilUsuarioDB

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

class AgenteFoco:
    async def processar(self, evento: EventoCanonico):
        pacote = evento.payload.get("pacote") or getattr(evento, "pacote", None)
        if not pacote:
            return

        # Obter dados de ambas as memórias para tomar a decisão
        entidade_app = await catalogo.obter_app(pacote)
        perfil_app = await memoria_perfil.obter_perfil_app(pacote)

        # Roda as lógicas de inferência em paralelo para maior eficiência
        await asyncio.gather(
            self._inferir_sugestao_contextual(evento, entidade_app),
            self._inferir_bem_estar(evento, entidade_app),
            self._inferir_app_favorito(evento, perfil_app)
        )

    async def _inferir_sugestao_contextual(self, evento: EventoCanonico, entidade_app: EntidadeSemantica | None):
        """Lógica de inferência cruzada: evento atual + memórias = sugestão."""
        if not entidade_app or not entidade_app.atributos:
            return

        # Exemplo de regra: Se abrir um app de navegação, sugerir a rotina musical do horário.
        categoria_app = entidade_app.atributos.get("categoria", "").lower()
        if "navegação" in categoria_app or "mapas" in categoria_app:
            horario = _get_time_slot(evento.timestamp)
            # Busca o artista mais ouvido nesse horário
            artista_rotina = await memoria_perfil.obter_item_mais_frequente_por_periodo("ARTISTA_PREFERENCIA", horario)

            if artista_rotina:
                await kernel.publicar(
                    evento.clonar(
                        acao=TipoAcao.INTENCAO_INTERACAO,
                        prioridade=PrioridadeEvento.NORMAL,
                        payload={
                            "mensagem": f"Vai sair? Que tal ouvir {artista_rotina} no caminho?",
                            "titulo": "Sugestão Musical",
                            # Contrato de Ação Dinâmica para o cliente Android
                            "acao_tipo": "OPEN_APP",
                            "acao_parametro": "com.spotify.music", # Exemplo de app de música
                            "acao_texto": "Ouvir Música"
                        },
                    )
                )

    async def _inferir_bem_estar(self, evento: EventoCanonico, entidade_app: EntidadeSemantica | None):
        """Decisão sobre bem-estar, usando dados do catálogo semântico."""
        if not entidade_app or not entidade_app.atributos: return
        stats = entidade_app.atributos.get("stats", {})
        if stats.get("tempo_foco_minutos", 0) > 20: # Supondo que a inferência calcule isso
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    prioridade=PrioridadeEvento.ALTA,
                    payload={
                        "mensagem": f"Você está focado em {entidade_app.atributos.get('nome', 'este app')} há um bom tempo. Que tal uma pausa?",
                        "titulo": "Bem-estar",
                    },
                )
            )

    async def _inferir_app_favorito(self, evento: EventoCanonico, perfil_app: PerfilUsuarioDB | None):
        """Decisão sobre app favorito, usando o perfil de usuário."""
        if perfil_app and perfil_app.confianca > 0.8:
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    prioridade=PrioridadeEvento.BAIXA,
                    payload={
                        "mensagem": f"Notei que este é um dos seus apps mais usados. Bom te ver por aqui!",
                        "titulo": "Assistente de Hábitos",
                        # Contrato de Ação Dinâmica para o cliente Android
                        "acao_tipo": "OPEN_APP",
                        "acao_parametro": evento.pacote,
                        "acao_texto": "Abrir"
                    },
                )
            )