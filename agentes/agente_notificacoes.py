"""
agentes/agente_notificacoes.py
"""
from core.evento import EventoCanonico
from core.tipos import TipoAcao
from api.websocket import central_alertas

class AgenteNotificacoes:
    
    async def processar(self, evento: EventoCanonico):
        # Agora reage a eventos de intenção de interação
        if evento.acao == TipoAcao.INTENCAO_INTERACAO:
            payload = evento.payload
            if payload.get("mensagem"):
                print(f"🔔 [AgenteNotificacoes] Disparando: {payload.get('mensagem')}")
                # Passa o payload completo, que agora pode conter 'titulo', 'mensagem' e 'acoes'.
                await central_alertas.enviar_alerta(payload)