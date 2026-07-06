"""
agentes/agente_inferencia.py
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta
from core.evento import EventoCanonico
from core.tipos import CategoriaEvento
from servicos.catalogo_semantico import catalogo

class AgenteInferencia:
    def __init__(self):
        self.eventos: deque[EventoCanonico] = deque(maxlen=500)
        self.freq_apps = defaultdict(int)
        self.freq_artistas = defaultdict(int)

    async def processar(self, evento: EventoCanonico):
        self.eventos.append(evento)
        self._atualizar_frequencias(evento)
        await self._inferir_padroes(evento)

    def _atualizar_frequencias(self, evento: EventoCanonico):
        if evento.categoria == CategoriaEvento.APP_FOREGROUND:
            self.freq_apps[evento.pacote] += 1
        elif evento.categoria == CategoriaEvento.MEDIA:
            artista = evento.payload.get("artista")
            if artista:
                self.freq_artistas[artista] += 1

    async def _inferir_padroes(self, evento: EventoCanonico):
        await self._padrao_app_mais_usado()
        await self._padrao_musical()
        await self._padrao_rotina_noturna()

    async def _padrao_app_mais_usado(self):
        if not self.freq_apps:
            return
        app_top = max(self.freq_apps.items(), key=lambda x: x[1])
        pacote, uso = app_top
        if uso < 5:
            return
        entidade = await catalogo.obter_app(pacote)
        entidade.atributos.setdefault("insights", {})
        entidade.atributos["insights"]["app_favorito"] = True
        entidade.atributos["insights"]["score"] = uso
        catalogo.memoria.salvar(entidade)

    async def _padrao_musical(self):
        if not self.freq_artistas:
            return

        artista_top = max(self.freq_artistas.items(), key=lambda x: x[1])
        artista, plays = artista_top

        if plays < 3:
            return

        entidade = await catalogo.obter_artista(artista)

        entidade.atributos.setdefault("insights", {})
        entidade.atributos["insights"]["artista_favorito"] = True
        entidade.atributos["insights"]["score"] = plays

        catalogo.memoria.salvar(entidade)

    async def _padrao_rotina_noturna(self):
        agora = datetime.utcnow()
        ultimos_15min = [e for e in self.eventos if agora - e.timestamp < timedelta(minutes=15)]
        apps_noturnos = defaultdict(int)
        for e in ultimos_15min:
            if e.categoria == CategoriaEvento.APP_FOREGROUND:
                apps_noturnos[e.pacote] += 1
        if not apps_noturnos:
            return
        app_top = max(apps_noturnos.items(), key=lambda x: x[1])
        pacote, uso = app_top
        if uso < 3:
            return
        entidade = await catalogo.obter_app(pacote)
        entidade.atributos.setdefault("insights", {})
        entidade.atributos["insights"]["uso_noturno"] = True
        catalogo.memoria.salvar(entidade)