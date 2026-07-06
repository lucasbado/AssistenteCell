"""
core/pipeline_atencao.py

Pipeline de Atenção Cognitiva.

Responsável por processar eventos brutos e decidir se merecem
a atenção do sistema. Ele enriquece o evento com um score de atenção
e metadados para guiar os agentes subsequentes.

Fluxo:
1. Normalização e extração de características.
2. Avaliação por um conjunto de regras (blacklist, duplicatas, spam).
3. Cálculo de um "Score de Atenção".
4. Geração de um `ResultadoAtencao` com o score e os motivos.

Eventos com score abaixo de um limiar são descartados.
"""

from __future__ import annotations

import time
import hashlib
import logging
from pydantic import BaseModel, Field

from core.evento import EventoCanonico
from core.tipos import (
    CategoriaEvento,
    PrioridadeEvento,
)

logger = logging.getLogger(__name__)

class ResultadoAtencao(BaseModel):
    score: int = 0
    motivos: list[str] = Field(default_factory=list)
    pode_interagir: bool = True

class PipelineAtencao:

    def __init__(self):

        # assinatura -> timestamp
        self._historico = {}

        # pacote -> timestamp
        self._ultimo_evento_app = {}

        # pacotes ignorados
        self._blacklist = {

            "android",

            "com.android.systemui",

            "com.android.launcher",

            "com.android.providers.downloads",

            "com.google.android.permissioncontroller",

            "system",

            "sistema"

        }

        # apps que geram spam
        self._apps_midia = {

            "com.spotify.music",

            "com.google.android.youtube",

            "com.google.android.apps.youtube.music",

            "com.netflix.mediaclient"

        }

        # janelas

        self.janela_deduplicacao = 45

        self.janela_midia = 15

    # ==========================================================
    # API
    # ==========================================================

    def avaliar(self, evento: EventoCanonico) -> ResultadoAtencao | None:
        """
        Avalia um evento e retorna um ResultadoAtencao se ele for digno de
        processamento, ou None se for descartado.
        """
        resultado = ResultadoAtencao()

        if self._blacklist_evento(evento):
            logger.debug(f"🚮 Evento {evento.id[:8]} descartado por blacklist.")
            return None

        if self._evento_duplicado(evento):
            logger.debug(f"🔁 Evento {evento.id[:8]} descartado por duplicidade.")
            return None

        if self._spam_de_midia(evento):
            resultado.pode_interagir = False
            resultado.motivos.append("SPAM_DE_MIDIA")

        self._atualizar_memoria(evento)
        self._calcular_score(evento, resultado)

        if resultado.score < 10: # Limiar mínimo de atenção
            logger.debug(f"📉 Evento {evento.id[:8]} descartado por score baixo ({resultado.score}).")
            return None

        return resultado

    # ==========================================================
    # BLACKLIST
    # ==========================================================

    def _blacklist_evento(
        self,
        evento: EventoCanonico,
    ) -> bool:

        pacote = evento.pacote.lower()

        return pacote in self._blacklist

    # ==========================================================
    # DEDUPLICAÇÃO
    # ==========================================================

    def _evento_duplicado(
        self,
        evento: EventoCanonico,
    ) -> bool:

        agora = time.time()

        assinatura = self._gerar_assinatura(evento)

        if assinatura not in self._historico:
            return False

        ultimo = self._historico[assinatura]

        return (agora - ultimo) < self.janela_deduplicacao

    # ==========================================================
    # SPAM DE MÍDIA
    # ==========================================================

    def _spam_de_midia(
        self,
        evento: EventoCanonico,
    ) -> bool:

        pacote = evento.pacote.lower()

        if pacote not in self._apps_midia:
            return False

        agora = time.time()

        ultimo = self._ultimo_evento_app.get(pacote)

        if ultimo is None:
            return False

        return (agora - ultimo) < self.janela_midia

    # ==========================================================
    # MEMÓRIA CURTA
    # ==========================================================

    def _atualizar_memoria(
        self,
        evento: EventoCanonico,
    ):

        agora = time.time()

        assinatura = self._gerar_assinatura(evento)

        self._historico[assinatura] = agora

        self._ultimo_evento_app[evento.pacote.lower()] = agora

    # ==========================================================
    # SCORING
    # ==========================================================

    def _calcular_score(self, evento: EventoCanonico, resultado: ResultadoAtencao):
        """Calcula o score de atenção inicial para um evento."""
        match evento.categoria:
            case CategoriaEvento.NOTIFICACAO:
                resultado.score += 50
                resultado.motivos.append("TIPO_NOTIFICACAO")
            case CategoriaEvento.MEDIA:
                resultado.score += 20
                resultado.motivos.append("TIPO_MEDIA")
            case CategoriaEvento.APP_FOREGROUND:
                resultado.score += 30
                resultado.motivos.append("TIPO_APP_FOREGROUND")
            case _:
                resultado.score += 10
                resultado.motivos.append("TIPO_GENERICO")

    # ==========================================================
    # HASH
    # ==========================================================

    def _gerar_assinatura(
        self,
        evento: EventoCanonico,
    ) -> str:

        texto = (
            f"{evento.categoria}|"
            f"{evento.pacote}|"
            f"{evento.payload}"
        )

        return hashlib.sha1(
            texto.encode()
        ).hexdigest()


pipeline_atencao = PipelineAtencao()