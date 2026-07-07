"""
agentes/agente_reflexo.py

Camada 2: Reflexo de Notificações.

Este agente tem uma única responsabilidade: analisar eventos de NOTIFICACAO
e decidir se eles são simples o suficiente para serem descartados ou se são
complexos (contêm texto) e devem ser escalados para a camada de Raciocínio (LLM).
"""

import logging

from core.evento import EventoCanonico
from core.tipos import TipoAcao
from core.kernel import kernel

logger = logging.getLogger(__name__)

class AgenteReflexo:
    async def processar(self, evento: EventoCanonico):
        # O filtro do Kernel já garante que este agente só recebe eventos de NOTIFICACAO.
        remetente = evento.payload.get("titulo")
        texto = evento.payload.get("texto")

        if not remetente:
            logger.debug(f"[Reflexo] Ignorando notificação sem remetente: {evento.id[:8]}")
            return

        # A filosofia do sistema é clara: se um evento é complexo, ele deve
        # ser analisado pelo "córtex" (LLM). Uma notificação com texto é, por
        # definição, complexa. Este agente, como um "reflexo", não deve tentar
        # interpretá-la. Sua única responsabilidade é delegar para a próxima camada.
        if texto:
            logger.info(f"🚦 [Reflexo] Notificação de '{remetente}' tem texto. Delegando para raciocínio (LLM). Evento: {evento.id[:8]}")
            await kernel.publicar(
                evento.clonar(acao=TipoAcao.EVENTO_COMPLEXO)
            )
        else:
            # Se não há texto, não há o que a LLM interpretar. O agente de reflexo
            # termina sua análise aqui. Não há ação a ser tomada.
            logger.debug(f"✅ [Reflexo] Notificação de '{remetente}' sem texto. Nenhuma ação de reflexo. Evento: {evento.id[:8]}")
