import asyncio

class AgenteNotificacoes:
    def __init__(self):
        self.processados = set()

    async def processar(self, evento: EventoCanonico):
        # Verifica se o evento já foi processado
        if evento.id in self.processados:
            return
        
        # Adiciona o ID do evento ao conjunto de processados
        self.processados.add(evento.id)
        
        # Agora reage a eventos de intenção de interação
        if evento.acao == TipoAcao.INTENCAO_INTERACAO:
            titulo = evento.payload.get("titulo", "Ollie")
            texto = evento.payload.get("mensagem")
            if texto:
                print(f"🔔 [AgenteNotificacoes] Disparando: {texto}")
        
        # Limpa o conjunto de processados após um intervalo (por exemplo, 1 minuto)
        await asyncio.sleep(60)
        self.processados.clear()
