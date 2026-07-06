from __future__ import annotations
from core.evento import EventoCanonico
from servicos.memoria_episodica import MemoriaEpisodica

class AgenteEpisodico:
    """
    Um agente passivo que atua como a sub-rotina do hipocampo.
    Ele escuta TODOS os eventos que sobrevivem ao Filtro de Atenção do Kernel.
    """
    def __init__(self):
        self.memoria = MemoriaEpisodica()

    async def processar(self, evento: EventoCanonico):
        # Fire-and-forget: delega para o serviço de banco assíncrono
        # Como o Kernel usa asyncio.gather(), isto roda em paralelo e não atrasa os reflexos!
        await self.memoria.arquivar_evento(evento)