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
            titulo = evento.payload.get("titulo", "Ollie")
            texto = evento.payload.get("mensagem")
            if texto:
                print(f"🔔 [AgenteNotificacoes] Disparando: {texto}")
                await central_alertas.enviar_alerta(titulo, texto)