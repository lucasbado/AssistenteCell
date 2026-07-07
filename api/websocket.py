"""
api/websocket.py
"""
import logging
import json
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
        for conexao in self.conexoes_ativas:
            try:
                await conexao.send_json(dados_para_envio)
            except Exception as e:
                logger.error(f"❌ Erro ao enviar WS: {e}")

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