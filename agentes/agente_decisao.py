"""
agentes/agente_reflexo.py

Camada 2: Reflexo. Decide sobre eventos com base em regras, estatísticas e
padrões simples, sem usar a LLM. É rápido e eficiente.
"""

from datetime import datetime, timedelta
from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, PrioridadeEvento, OrigemEvento, TipoAcao
from core.kernel import kernel
from servicos.catalogo_semantico import catalogo


class AgenteReflexo:
    def __init__(self):
        self.ultimo_alerta: datetime | None = None
        self.cooldown_segundos = 60

    async def processar(self, evento: EventoCanonico):
        # O cooldown agora é verificado dentro de cada decisão,
        # pois um evento pode ser complexo mesmo em cooldown. Só processa ações normais
        atencao = evento.metadados.get("atencao", {})
        if not atencao.get("pode_interagir", True):
            return

        if evento.categoria == CategoriaEvento.MEDIA:
            await self._decidir_musica(evento)
        elif evento.categoria == CategoriaEvento.APP_FOREGROUND:
            await self._decidir_app(evento)
        elif evento.categoria == CategoriaEvento.NOTIFICACAO:
            await self._decidir_notificacao(evento)

    def _pode_agir(self) -> bool:
        if self.ultimo_alerta is None:
            return True
        return datetime.utcnow() - self.ultimo_alerta > timedelta(
            seconds=self.cooldown_segundos
        )

    async def _decidir_musica(self, evento: EventoCanonico):
        artista = evento.payload.get("artista")

        if not artista or not self._pode_agir():
            return

        entidade = await catalogo.obter_artista(artista)

        score = entidade.atributos.get("stats", {}).get("plays", 0)

        if score >= 5:
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    payload={
                        "mensagem": f"Você está ouvindo {artista} frequentemente. Bom gosto! 🎵",
                        "titulo": "Assistente",
                        "prioridade": PrioridadeEvento.NORMAL,
                    },
                )
            )

            self.ultimo_alerta = datetime.utcnow()

    async def _decidir_app(self, evento: EventoCanonico):
        pacote = evento.payload.get("pacote") or getattr(evento, "pacote", None)
        if not self._pode_agir() or not pacote:
            return

        entidade = await catalogo.obter_app(pacote)

        # 🛡️ Validação defensiva: se o fato é inédito e não está no banco/cache ainda
        if not entidade or not hasattr(entidade, "atributos"):
            return

        stats = entidade.atributos.get("stats", {})
        insights = entidade.atributos.get("insights", {})

        if stats.get("tempo_foco", 0) > 20:
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
            self.ultimo_alerta = datetime.utcnow()
        elif insights.get("app_favorito"):
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    payload={
                        "mensagem": f"Seu app favorito {pacote} em uso novamente!",
                        "titulo": "Assistente",
                        "prioridade": PrioridadeEvento.BAIXA,
                    },
                )
            )
            self.ultimo_alerta = datetime.utcnow()

    async def _decidir_notificacao(self, evento: EventoCanonico):
        remetente = evento.payload.get("titulo")
        texto = evento.payload.get("texto")
        if not remetente:
            return
            
        entidade = await catalogo.obter_contato(remetente)
        
        # 🛡️ BLINDAGEM ARQUITETURAL: Verifica se o contato é inédito ou falhou ao carregar
        if not entidade or not hasattr(entidade, "atributos"):
            # O contato não existe no banco (é novo).
            # Como o Reflexo não pensa, ele apenas delega para o Córtex se houver um texto.
            if texto:
                await kernel.publicar(
                    evento.clonar(acao=TipoAcao.EVENTO_COMPLEXO)
                )
            return # Aborta o processamento de reflexo rápido, pois não há estatísticas.

        stats = entidade.atributos.get("stats", {})
        if self._pode_agir() and stats.get("interacoes", 0) >= 5:
            await kernel.publicar(
                evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    payload={
                        "mensagem": f"Você fala bastante com {remetente}",
                        "titulo": "Assistente",
                        "prioridade": PrioridadeEvento.BAIXA,
                    },
                )
            )
            self.ultimo_alerta = datetime.utcnow()
        # Se a notificação tem texto mas não bateu em nenhuma regra simples,
        # ela é candidata a ser complexa.
        elif texto:
            await kernel.publicar(
                # Apenas muda a ação. O payload original é preservado pelo `clonar`.
                # O motivo pode ir para os metadados se necessário, mas não no payload.
                evento.clonar(acao=TipoAcao.EVENTO_COMPLEXO)
            )
