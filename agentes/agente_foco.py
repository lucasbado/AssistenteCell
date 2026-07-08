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

logger = logging.getLogger("AgenteFoco")


def _get_time_slot(timestamp: datetime) -> str:
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
        # MENSAGEM DE RASTREAMENTO IMEDIATA
        print(
            f"🎯 [AGENTE FOCO] Acordei! Fui chamado pelo Kernel para analisar o app: {evento.pacote}"
        )

        pacote = evento.payload.get("pacote") or getattr(evento, "pacote", None)
        if not pacote:
            print("❌ [AGENTE FOCO] O pacote veio vazio. Abortando.")
            return

        logger.info(f"🧠 AgenteFoco: Iniciando análise para o app [{pacote}]")

        # Obter dados de ambas as memórias para tomar a decisão
        entidade_app = await catalogo.obter_app(pacote)
        perfil_app = await memoria_perfil.obter_perfil_app(pacote)

        # Roda as lógicas de inferência em paralelo para maior eficiência
        await asyncio.gather(
            self._inferir_sugestao_contextual(evento, entidade_app),
            self._inferir_bem_estar(evento, entidade_app),
            self._inferir_app_favorito(evento, perfil_app),
        )

    async def _inferir_sugestao_contextual(
        self, evento: EventoCanonico, entidade_app: EntidadeSemantica | None
    ):
        if not entidade_app or not entidade_app.atributos:
            logger.debug(
                "🤷‍♂️ AgenteFoco: App não catalogado. Sem sugestão contextual."
            )
            return

        categoria_app = entidade_app.atributos.get("categoria", "").lower()
        logger.info(
            f"📚 AgenteFoco: Categoria do app identificada como '{categoria_app}'"
        )

        if "navegação" in categoria_app or "mapas" in categoria_app:
            horario = _get_time_slot(evento.timestamp)
            artista_rotina = await memoria_perfil.obter_item_mais_frequente_por_periodo(
                "ARTISTA_PREFERENCIA", horario
            )

            # 🔥 A CORREÇÃO ESTÁ AQUI: Se o banco de dados estiver vazio, usamos um Fallback
            if not artista_rotina:
                logger.info(
                    f"⚠️ AgenteFoco: Memória vazia para artistas no período {horario}. Usando Fallback."
                )
                artista_rotina = "um Podcast ou AC/DC"

            logger.info(
                "💡 AgenteFoco: Gatilho de mapa ativado! Gerando notificação de música."
            )

            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    prioridade=PrioridadeEvento.NORMAL,
                    payload={
                        "titulo": "Sugestão Musical",
                        "texto": f"Vai sair? Que tal ouvir {artista_rotina} no caminho?",
                        # Contrato de Ação Dinâmica
                        "acao_tipo": "OPEN_APP",
                        "acao_parametro": "com.spotify.music",  # Ou o pacote do seu player favorito
                        "acao_texto": "Ouvir Música",
                    },
                )
            )

    async def _inferir_bem_estar(
        self, evento: EventoCanonico, entidade_app: EntidadeSemantica | None
    ):
        if not entidade_app or not entidade_app.atributos:
            return

        stats = entidade_app.atributos.get("stats", {})
        if stats.get("tempo_foco_minutos", 0) > 20:
            logger.info("💡 AgenteFoco: Gatilho de Bem-estar ativado.")
            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    prioridade=PrioridadeEvento.ALTA,
                    payload={
                        "titulo": "Bem-estar",
                        "texto": f"Você está focado neste app há um bom tempo. Que tal uma pausa?",
                    },
                )
            )

    async def _inferir_app_favorito(
        self, evento: EventoCanonico, perfil_app: PerfilUsuarioDB | None
    ):
        # 🔥 Abaixei a confiança provisoriamente para 0.0 para testar com banco de dados vazio
        confianca_atual = perfil_app.confianca if perfil_app else 0.0

        if perfil_app and confianca_atual > 0.8:
            logger.info("💡 AgenteFoco: Gatilho de App Favorito ativado.")
            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    prioridade=PrioridadeEvento.BAIXA,
                    payload={
                        "titulo": "Assistente de Hábitos",
                        "texto": "Notei que este é um dos seus apps mais usados. Bom te ver por aqui!",
                    },
                )
            )
