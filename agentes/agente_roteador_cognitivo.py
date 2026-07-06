"""
agentes/agente_roteador_cognitivo.py

Este agente atua como um intermediário entre o reflexo e a cognição profunda.
Ele escuta por eventos que foram marcados como "complexos" pelas camadas
inferiores e decide qual recurso cognitivo (LLM, busca na web, etc.) deve ser
acionado.

Por enquanto, sua lógica é simples: qualquer evento complexo merece a atenção da LLM.
"""
import logging
from core.evento import EventoCanonico
from core.tipos import TipoAcao
from core.kernel import kernel

logger = logging.getLogger(__name__)

class AgenteRoteadorCognitivo:
    async def processar(self, evento: EventoCanonico):
        # O filtro do Kernel já garante que só recebemos a ação correta,
        # mas uma verificação explícita não faz mal.
        if evento.acao != TipoAcao.EVENTO_COMPLEXO:
            return

        logger.info(f"🚦 Evento complexo {evento.id[:8]} recebido. Roteando para raciocínio (LLM)...")

        # Por enquanto, apenas repassa para a LLM. Futuramente, pode ter mais lógica.
        # Repassamos o payload original para que o AgenteRaciocinio tenha o contexto completo.
        # Apenas clonamos mudando a ação. O payload e outros dados são mantidos.
        evento_raciocinio = evento.clonar(acao=TipoAcao.INTENCAO_RACIOCINIO)
        await kernel.publicar(evento_raciocinio)