"""
agentes/agente_gestor_interrupcoes.py

Este agente atua como um porteiro para as notificações. Sua única
responsabilidade é decidir SE uma notificação deve interromper o usuário,
baseado em sua prioridade.
"""
import logging
from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, PrioridadeEvento
from core.kernel import kernel

logger = logging.getLogger(__name__)

class AgenteGestorInterrupcoes:
    def __init__(self):
        """
        Este agente tornou-se um filtro de prioridade.
        A lógica de cooldown baseada em tempo foi removida.
        """
        pass

    async def processar(self, evento: EventoCanonico):
        # A lógica de cooldown foi desativada em favor de uma decisão baseada
        # puramente na prioridade do evento, que é definida pelos agentes
        # de raciocínio ou inferência.

        # No futuro, aqui poderá entrar uma lógica mais inteligente que considera
        # o contexto do usuário (app em uso, localização, etc.) para decidir
        # se uma interrupção é apropriada, mesmo para prioridades normais.

        # Regra atual: Notificações de prioridade BAIXA são sempre suprimidas
        # para evitar ruído excessivo e interrupções desnecessárias.
        if evento.prioridade == PrioridadeEvento.BAIXA:
            logger.info(f"🤫 Notificação de baixa prioridade suprimida: {evento.payload.get('texto', 'N/A')[:50]}...")
            return

        # Notificações de prioridade NORMAL ou ALTA são aprovadas para envio.
        logger.info(f"👍 Gestor de Interrupções aprovou notificação de prioridade {evento.prioridade.name} para envio.")
        await kernel.publicar(evento.clonar(categoria=CategoriaEvento.NOTIFICACAO_PRONTA_PARA_ENVIO))