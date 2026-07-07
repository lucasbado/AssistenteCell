"""
agentes/agente_inferencia.py
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from core.evento import EventoCanonico
from core.tipos import CategoriaEvento
from modelos.catalogo import EntidadeSemantica
from servicos.catalogo_semantico import catalogo
from servicos.memoria_perfil import memoria_perfil

class AgenteInferencia:
    def __init__(self):
        self.eventos_recentes: deque[EventoCanonico] = deque(maxlen=500)
        self.uso_apps: defaultdict[str, deque[datetime]] = defaultdict(lambda: deque(maxlen=20))

    async def processar(self, evento: EventoCanonico):
        self.eventos_recentes.append(evento)
        self._atualizar_frequencias(evento)
        await self._inferir_padroes(evento)

    def _atualizar_frequencias(self, evento: EventoCanonico):
        if evento.categoria == CategoriaEvento.APP_FOREGROUND:
            self.uso_apps[evento.pacote].append(evento.timestamp)

    async def _inferir_padroes(self, evento: EventoCanonico):
        await self._padrao_app_mais_usado()
        await self._inferir_contato_favorito(evento)
        await self._inferir_rotina_musical(evento)
        await self._padrao_rotina_noturna()

    async def _inferir_contato_favorito(self, evento: EventoCanonico):
        if evento.categoria != CategoriaEvento.NOTIFICACAO:
            return

        remetente = evento.payload.get("titulo")
        if not remetente:
            return

        perfil_contato = await memoria_perfil.obter_perfil_contato(remetente)
        if not perfil_contato:
            return

        # Regra de inferência: score alto e confiança alta indicam um contato favorito.
        if perfil_contato.score > 10 and perfil_contato.confianca > 0.7:
            entidade = await catalogo.obter_contato(remetente) or EntidadeSemantica(tipo="CONTATO", chave=remetente)
            entidade.atributos.setdefault("insights", {})
            if not entidade.atributos["insights"].get("contato_favorito"):
                entidade.atributos["insights"]["contato_favorito"] = True
                await catalogo.memoria.salvar(entidade)

    async def _inferir_rotina_musical(self, evento: EventoCanonico):
        if evento.categoria != CategoriaEvento.MEDIA:
            return

        artista = evento.payload.get("artista")
        if not artista:
            return

        # 1. Busca os perfis de interação com o artista em todos os horários
        perfis = await memoria_perfil.obter_perfis_artista(artista)
        if not perfis:
            return

        # 2. Encontra o horário com maior interação (maior score)
        perfil_rotina = max(perfis, key=lambda p: p.score)

        # 3. Regra de inferência: só considera uma rotina se a interação for significativa
        if perfil_rotina.score > 5:
            # Extrai o horário do nome da categoria (ex: ARTISTA_PREFERENCIA_MANHA)
            horario_rotina = perfil_rotina.categoria.split('_')[-1]

            # 4. Salva o insight na memória semântica para o AgenteReflexo usar
            entidade = await catalogo.obter_artista(artista)
            if entidade:
                entidade.atributos.setdefault("insights", {})
                # Só atualiza se for uma nova rotina ou uma rotina diferente
                if entidade.atributos["insights"].get("rotina_musical") != horario_rotina:
                    entidade.atributos["insights"]["rotina_musical"] = horario_rotina
                    await catalogo.memoria.salvar(entidade)

    async def _padrao_app_mais_usado(self):
        if not self.uso_apps:
            return

        app_scores = {}
        agora = datetime.now(timezone.utc)
        for pacote, timestamps in self.uso_apps.items():
            score = 0
            for ts in timestamps:
                # Pontua mais alto por uso recente. O score decai linearmente ao longo de 24h.
                horas_atras = (agora - ts).total_seconds() / 3600
                score += max(0, 1 - (horas_atras / 24))
            app_scores[pacote] = score

        if not app_scores:
            return

        pacote_top, score_top = max(app_scores.items(), key=lambda item: item[1])

        # Um novo limiar baseado em score, não em contagem bruta.
        # Ex: equivale a ~3 usos muito recentes ou mais usos antigos.
        if score_top < 3.0:
            return

        entidade = await catalogo.obter_app(pacote_top) or EntidadeSemantica(tipo="APP", chave=pacote_top)
        entidade.atributos.setdefault("insights", {})
        entidade.atributos["insights"]["app_favorito"] = True
        entidade.atributos["insights"]["score"] = round(score_top, 2)
        await catalogo.memoria.salvar(entidade)

    async def _padrao_rotina_noturna(self):
        agora = datetime.now(timezone.utc)
        ultimos_15min = [e for e in self.eventos_recentes if agora - e.timestamp < timedelta(minutes=15)]
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
        entidade = await catalogo.obter_app(pacote) or EntidadeSemantica(tipo="APP", chave=pacote)
        entidade.atributos.setdefault("insights", {})
        entidade.atributos["insights"]["uso_noturno"] = True
        await catalogo.memoria.salvar(entidade)