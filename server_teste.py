from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/teste")
async def teste_ws(websocket: WebSocket):
    print("🚀 [QUARENTENA] O telemóvel bateu na porta!")
    try:
        await websocket.accept()
        print("✅ [QUARENTENA] Conexão WebSocket estabelecida com sucesso!")
        while True:
            msg = await websocket.receive_text()
            print(f"Mensagem recebida: {msg}")
    except Exception as e:
        print(f"❌ [QUARENTENA] Erro interno: {e}")