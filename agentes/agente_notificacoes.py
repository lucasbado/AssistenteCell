"""
agentes/agente_notificacoes.py
"""
import logging
from core.evento import EventoCanonico
from core.tipos import TipoAcao
from api.websocket import central_alertas

logger = logging.getLogger(__name__)

class AgenteNotificacoes:
    
    async def processar(self, evento: EventoCanonico):
        # Agora reage a eventos de intenção de interação
        if evento.acao == TipoAcao.INTENCAO_INTERACAO:
            payload = evento.payload
            if payload and payload.get("mensagem"):
                logger.info(f"🔔 [AgenteNotificacoes] Disparando: {payload.get('mensagem')}")
                # Passa o evento inteiro como um dicionário para que o WebSocket
                # tenha acesso a todos os campos, incluindo o 'correlacao_id'.
                await central_alertas.enviar_alerta(evento.model_dump())