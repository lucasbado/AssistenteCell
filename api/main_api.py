from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.perfil import router as perfil_router
from api.status import router as status_router
from servicos.router import router as timeline_router
from api.router import router as home_router

def criar_app_api():
    """
    Cria e configura a instância principal da aplicação FastAPI para a API externa.
    """
    app = FastAPI(
        title="AssistenteCell - Camada de Consulta Cognitiva",
        description="API para servir conhecimento processado ao cliente Android.",
        version="1.0.0"
    )

    # Adiciona o middleware de CORS para permitir requisições do frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, restrinja para o domínio do seu frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # O endpoint /home é o principal e mais importante
    app.include_router(home_router, prefix="/api/v1/home", tags=["Home"])

    # Os demais endpoints servem as telas específicas
    app.include_router(perfil_router, prefix="/api/v1/perfil", tags=["Perfil"])
    app.include_router(status_router, prefix="/api/v1/status", tags=["Status"])
    app.include_router(timeline_router, prefix="/api/v1/timeline", tags=["Timeline"])

    return app

app_api = criar_app_api()