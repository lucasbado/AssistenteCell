"""
agentes/agente_reflexo.py

Camada 2: Reflexo. Decide sobre eventos com base em regras, estatísticas e
padrões simples, sem usar a LLM. É rápido e eficiente.
"""

import logging
from datetime import datetime, timedelta, timezone

from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, PrioridadeEvento, OrigemEvento, TipoAcao
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

class AgenteReflexo:
    def __init__(self):
        self.interacoes_pausadas = False

    async def processar(self, evento: EventoCanonico):
        # O AgenteBemEstar agora controla o fluxo de interações.
        # Este agente apenas obedece.
        if evento.categoria == CategoriaEvento.SISTEMA_PAUSA_INTERACOES:
            self.interacoes_pausadas = True
            return
        elif evento.categoria == CategoriaEvento.SISTEMA_LIBERA_INTERACOES:
            self.interacoes_pausadas = False
            return

        atencao = evento.metadados.get("atencao", {})
        if not atencao.get("pode_interagir", True):
            return

        if evento.categoria == CategoriaEvento.MEDIA:
            await self._decidir_musica(evento)
        elif evento.categoria == CategoriaEvento.APP_FOREGROUND:
            await self._decidir_app(evento)
        elif evento.categoria == CategoriaEvento.NOTIFICACAO:
            await self._decidir_notificacao(evento)

    async def _decidir_musica(self, evento: EventoCanonico):
        artista = evento.payload.get("artista")
        if not artista:
            return

        # Obter dados de ambas as memórias para tomar a decisão
        entidade = await catalogo.obter_artista(artista)
        perfil_artista = await memoria_perfil.obter_perfil_artista(artista) # Perfil genérico
        horario_atual = _get_time_slot(evento.timestamp)

        # Decisão 1: Rotina Musical (prioridade alta)
        if entidade and not self.interacoes_pausadas:
            insights = entidade.atributos.get("insights", {})
            horario_rotina = insights.get("rotina_musical")
            if horario_rotina and horario_rotina == horario_atual:
                await kernel.publicar(
                    evento.clonar(
                        acao=TipoAcao.INTENCAO_INTERACAO,
                        payload={
                            "mensagem": f"Começando o(a) {horario_rotina.title()} com {artista}? Boa escolha!",
                            "titulo": "Sua Rotina Musical",
                            "prioridade": PrioridadeEvento.NORMAL,
                        },
                    )
                )
                return # Ação tomada, não continuar

        # Decisão 2: Artista favorito (genérico, prioridade mais baixa)
        if perfil_artista and perfil_artista.confianca > 0.6 and not self.interacoes_pausadas:
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    payload={
                        "mensagem": f"Vejo que você curte bastante {artista}. Ótima escolha! 🎵",
                        "titulo": "Assistente Musical",
                        "prioridade": PrioridadeEvento.NORMAL,
                    },
                )
            )

    async def _decidir_app(self, evento: EventoCanonico):
        pacote = evento.payload.get("pacote") or getattr(evento, "pacote", None)
        if not pacote:
            return

        # Obter dados de ambas as memórias para tomar a decisão
        entidade = await catalogo.obter_app(pacote)
        perfil_app = await memoria_perfil.obter_perfil_app(pacote)

        # Decisão 1: Bem-estar (prioridade alta), pode usar dados do catálogo semântico
        stats = getattr(entidade, "atributos", {}).get("stats", {})
        if stats.get("tempo_foco", 0) > 20 and not self.interacoes_pausadas:
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    payload={
                        "mensagem": "Você está muito tempo nesse app. Que tal uma pausa?",
                        "titulo": "Bem-estar",
                        "prioridade": PrioridadeEvento.ALTA,
                    },
                )
            )
        # Decisão 2: App favorito (prioridade baixa), usando o novo perfil de usuário
        elif perfil_app and perfil_app.confianca > 0.8 and not self.interacoes_pausadas:
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    payload={
                        "mensagem": f"Notei que {pacote} é um dos seus apps mais usados.",
                        "titulo": "Assistente de Hábitos",
                        "prioridade": PrioridadeEvento.BAIXA,
                    },
                )
            )

    async def _decidir_notificacao(self, evento: EventoCanonico):
        remetente = evento.payload.get("titulo")
        texto = evento.payload.get("texto")

        if not remetente:
            logger.debug(f"[Reflexo] Ignorando notificação sem remetente: {evento.id[:8]}")
            return

        if texto:
            # A filosofia do sistema é clara: se um evento é complexo, ele deve
            # ser analisado pelo "córtex" (LLM). Uma notificação com texto é, por
            # definição, complexa.
            # Este agente, como um "reflexo", não deve tentar interpretá-la.
            # Sua única responsabilidade é delegar para a próxima camada.
            # Qualquer outra lógica que crie uma INTENCAO_INTERACAO aqui para
            # notificações com texto viola a arquitetura e causa as mensagens
            # "divididas" que você observa.
            logger.info(f"🚦 [Reflexo] Notificação de '{remetente}' tem texto. Delegando para raciocínio (LLM). Evento: {evento.id[:8]}")
            await kernel.publicar(
                evento.clonar(acao=TipoAcao.EVENTO_COMPLEXO)
            )
        else:
            # Se não há texto, não há o que a LLM interpretar. O agente de reflexo
            # termina sua análise aqui. Não há ação a ser tomada.
            logger.debug(f"✅ [Reflexo] Notificação de '{remetente}' sem texto. Nenhuma ação de reflexo. Evento: {evento.id[:8]}")
