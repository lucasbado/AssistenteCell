from servicos.memoria_episodica import MemoriaEpisodica

class AgregadorTimeline:
    def __init__(self):
        self.memoria = MemoriaEpisodica()

    async def obter_eventos_recentes(self, minutos: int = 60) -> list[dict]:
        """
        Busca os eventos brutos da memória episódica.
        """
        return await self.memoria.obter_contexto_recente(minutos=minutos)

agregador_timeline = AgregadorTimeline()