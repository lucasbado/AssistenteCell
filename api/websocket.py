"""
api/websocket.py
"""
import logging
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("WebSocket")
router = APIRouter()

class GerenciadorNotificacoes:
    def __init__(self):
        self.conexoes_ativas: list[WebSocket] = []

    async def conectar(self, websocket: WebSocket):
        await websocket.accept()
        self.conexoes_ativas.append(websocket)
        logger.info("✅ Conexão WS estabelecida com o telemóvel!")

    def desconectar(self, websocket: WebSocket):
        if websocket in self.conexoes_ativas:
            self.conexoes_ativas.remove(websocket)
        logger.warning("🔌 Telemóvel desconectado do WS.")

    async def enviar_alerta(self, payload: dict):
        if not self.conexoes_ativas:
            logger.warning("⚠️ Tentativa de enviar alerta, mas o telemóvel está desconectado!")
            return
        
        # O 'payload' recebido é o evento completo serializado.
        # Extraímos o payload de negócio dele.
        payload_negocio = payload.get("payload", {})

        # LÓGICA DE ADAPTAÇÃO (ROBUSTA):
        # 1. Copia o payload interno para não modificar o evento original e preservar todos os campos.
        dados_para_envio = payload_negocio.copy()

        # Adiciona flag de tipo para o cliente saber o que fazer
        dados_para_envio['tipo_ws'] = 'NOTIFICACAO'

        # 2. Adapta o nome da chave 'mensagem' para 'texto' para manter
        #    compatibilidade com o contrato do cliente Android.
        #    O 'pop' remove a chave antiga e retorna seu valor, evitando duplicidade.
        if 'mensagem' in dados_para_envio:
            dados_para_envio['texto'] = dados_para_envio.pop('mensagem')
        
        # 3. Garante valores padrão e a assinatura do sistema.
        dados_para_envio.setdefault("titulo", "Ollie")
        dados_para_envio["origem_sistema"] = "OLLIE"

        # 4. INCLUI O GANCHO PARA FEEDBACK: O ID de correlação é a chave para o aprendizado.
        dados_para_envio['correlacao_id'] = payload.get('correlacao_id')

        logger.info(f"🚀 Enviando alerta via WS: {json.dumps(dados_para_envio, ensure_ascii=False)}")
        await self._broadcast(dados_para_envio)

    async def enviar_evento_log(self, evento_dict: dict):
        """Envia um evento técnico/cognitivo para o log em tempo real do dispositivo."""
        if not self.conexoes_ativas:
            return

        # Prepara o DTO simplificado para a timeline do Android
        log_dto = {
            "tipo_ws": "EVENTO_LOG",
            "id": evento_dict.get("id"),
            "categoria": evento_dict.get("categoria"),
            "resumo": self._gerar_resumo_amigavel(evento_dict),
            "timestamp": evento_dict.get("timestamp"),
            "origem": evento_dict.get("origem"),
            "icone": self._mapear_icone(evento_dict.get("categoria"))
        }

        await self._broadcast(log_dto)

    async def _broadcast(self, msg: dict):
        """Auxiliar para enviar para todos os clientes conectados."""
        tarefas = []
        for conexao in self.conexoes_ativas:
            tarefas.append(conexao.send_json(msg))
        if tarefas:
            await asyncio.gather(*tarefas, return_exceptions=True)

    def _gerar_resumo_amigavel(self, ev: dict) -> str:
        cat = ev.get("categoria")
        payload = ev.get("payload", {})
        
        if cat == "APP_FOREGROUND":
            pacote = payload.get("pacote") or ev.get("pacote", "")
            app = pacote.split(".")[-1].capitalize()
            if "assistentecell" in pacote.lower(): app = "Ollie (meu app)"
            return f"Observei você abrindo o {app}"
        
        elif cat == "SENSOR_SYSTEM_CONTEXT":
            if "wifi" in payload:
                ssid = payload['wifi'].get('ssid')
                if ssid == "<unknown ssid>": return "Notei que você mudou de rede Wi-Fi"
                return f"Aprendi sobre sua conexão no Wi-Fi: {ssid}"
            return "Analisei seu contexto e localização atual"
        
        elif cat == "INTENCAO_NOTIFICACAO":
            return f"Pensei em te sugerir: {payload.get('titulo')}"
        
        elif cat == "INSIGHT_MEMORIA":
            return f"Gerei um novo insight sobre seus hábitos: {payload.get('conteudo', {}).get('title', 'Dica')}"

        elif cat == "MEDIA":
            artista = payload.get("artista", "alguém")
            return f"Vi que você começou a ouvir {artista}"
        
        return f"Processei um novo evento de {cat}"

    def _mapear_icone(self, categoria: str) -> str:
        mapeamento = {
            "APP_FOREGROUND": "eye",
            "SENSOR_SYSTEM_CONTEXT": "cog",
            "INTENCAO_NOTIFICACAO": "bell",
            "INSIGHT_MEMORIA": "psychology",
            "MEDIA": "play"
        }
        return mapeamento.get(categoria, "circle")

# Instância global para os Agentes usarem quando quiserem falar com o telemóvel
central_alertas = GerenciadorNotificacoes()

@router.websocket("/ws/alertas")
async def websocket_endpoint(websocket: WebSocket):
    await central_alertas.conectar(websocket)
    try:
        while True:
            # Mantemos a conexão aberta escutando por comandos do cliente
            data = await websocket.receive_text()
            # Adicionamos um log para depuração futura, caso o cliente envie dados.
            logger.info(f"📥 WS recebeu dados do cliente: {data}")
    except WebSocketDisconnect as e:
        logger.info(f"🔌 WS desconectado com código: {e.code} ({e.reason})")
        central_alertas.desconectar(websocket)
    except Exception as e:
        logger.error(f"❌ Erro interno no WS: {e}")