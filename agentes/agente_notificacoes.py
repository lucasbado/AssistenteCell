# agentes/agente_notificacoes.py
import logging
from datetime import datetime, timezone
from core.evento import EventoCanonico
from core.tipos import CategoriaEvento
from api.websocket import central_alertas

logger = logging.getLogger("AgenteNotificacoes")


class AgenteNotificacoes:
    def __init__(self):
        """Este agente agora é um executor puro. Ele não precisa de estado ou configuração."""
        pass

    async def processar(self, evento: EventoCanonico):
        logger.info(f"👂 [AGENTE NOTIFICACOES] Recebi evento APROVADO para envio imediato.")

        # A lógica de cooldown foi movida para o AgenteGestorInterrupcoes.
        # Este agente agora é "burro" e apenas envia o que recebe.
        await central_alertas.enviar_alerta(evento.model_dump())

        logger.info(f"🔔 Notificação enviada ao dispositivo: {evento.payload.get('titulo', 'Assistente')}")
