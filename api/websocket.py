"""
api/websocket.py
"""
import logging
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

    async def enviar_alerta(self, titulo: str, texto: str):
        if not self.conexoes_ativas:
            logger.warning("⚠️ Tentativa de enviar alerta, mas o telemóvel está desconectado!")
            return
        
        for conexao in self.conexoes_ativas:
            try:
                await conexao.send_json({
                    "titulo": titulo,
                    "texto": texto,
                    # Mantém a assinatura que você configurou no Kotlin
                    "origem_sistema": "OLLIE" 
                })
            except Exception as e:
                logger.error(f"❌ Erro ao enviar WS: {e}")

# Instância global para os Agentes usarem quando quiserem falar com o telemóvel
central_alertas = GerenciadorNotificacoes()

@router.websocket("/ws/alertas")
async def websocket_endpoint(websocket: WebSocket):
    await central_alertas.conectar(websocket)
    try:
        while True:
            # Mantemos a conexão aberta escutando
            data = await websocket.receive_text()
    except WebSocketDisconnect as e:
        logger.info(f"🔌 WS desconectado com código: {e.code} ({e.reason})")
        central_alertas.desconectar(websocket)
    except Exception as e:
        logger.error(f"❌ Erro interno no WS: {e}")