# main.py
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uuid
from core.evento import EventoCanonico


from core.kernel import kernel
from core.tipos import CategoriaEvento, TipoAcao, OrigemEvento
from agentes.agente_perfil import AgentePerfil
from agentes.agente_inferencia import AgenteInferencia
from agentes.agente_decisao import AgenteReflexo
from agentes.agente_notificacoes import AgenteNotificacoes
from agentes.agente_roteador_cognitivo import AgenteRoteadorCognitivo
from agentes.agente_episodico import AgenteEpisodico
from agentes.agente_raciocinio import AgenteRaciocinio
from api.eventos import router as eventos_router
from api.websocket import router as ws_router
from banco.database import inicializar_banco
from servicos.memoria_episodica import MemoriaEpisodica


# ==========================================
# 1. GERENCIADOR DE CICLO DE VIDA (BOOT)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Kernel] Verificando e inicializando estruturas de memória (SQLite)...")
    await inicializar_banco()
    print("[Kernel] Estruturas neurais prontas!")

    # Inicia o KERNEL de forma assíncrona
    asyncio.create_task(kernel.iniciar())
    print("🚀 Kernel Cognitivo iniciado.")

    yield  # A API fica rodando neste ponto

    print("[Kernel] Desligando sistema cognitivo...")
    from banco.database import async_engine

    await async_engine.dispose()


# ==========================================
# 2. CRIAÇÃO ÚNICA DO CÉREBRO (APP)
# ==========================================
app = FastAPI(lifespan=lifespan)

# ==========================================
# 3. MIDDLEWARES E SEGURANÇA
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 4. MAPEAMENTO DE SENSORES E SAÍDAS (ROTAS)
# ==========================================
app.include_router(eventos_router)
app.include_router(ws_router)

# ==========================================
# 5. INSTANCIAÇÃO E REGISTRO DOS AGENTES
# ==========================================
agente_perfil = AgentePerfil()
agente_inferencia = AgenteInferencia()
agente_reflexo = AgenteReflexo()
agente_notificacoes = AgenteNotificacoes()
agente_roteador_cognitivo = AgenteRoteadorCognitivo()
agente_raciocinio = AgenteRaciocinio()
agente_episodico = AgenteEpisodico()

kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL, callback=agente_perfil.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL, callback=agente_inferencia.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL, callback=agente_reflexo.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.EVENTO_COMPLEXO,
    callback=agente_roteador_cognitivo.processar,
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.INTENCAO_RACIOCINIO,
    callback=agente_raciocinio.processar,
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.INTENCAO_INTERACAO,
    callback=agente_notificacoes.processar,
)
kernel.registrar(filtro=lambda e: True, callback=agente_episodico.processar)


@app.get("/estatisticas")
async def estatisticas():
    return kernel.estatisticas()


@app.get("/debug/forcar-episodio")
async def forcar_memoria_episodica():
    meu_id = str(uuid.uuid4())

    # 🌟 CORREÇÃO: Usar um valor que pertence ao Enum 'OrigemEvento'
    # Ajuste para "SISTEMA" ou "IA" conforme definido no seu core.tipos
    evento_sintetico = EventoCanonico(
        id=meu_id,
        correlacao_id=meu_id,
        origem="SISTEMA",
        categoria=CategoriaEvento.NOTIFICACAO,
        acao=TipoAcao.NORMAL,
        pacote="com.example.system.debug",
        payload={
            "titulo": "Memória Injetada",
            "texto": "Teste de injeção sintética concluído.",
            "metadados_extras": {"ambiente": "Desenvolvimento"},
        },
    )

    await kernel.publicar(evento_sintetico)
    return {"status": "Memória injetada!", "evento_id": meu_id}


memoria_episodica_servico = MemoriaEpisodica()


@app.get("/debug/lembrancas")
async def ver_lembrancas():
    """Retorna os últimos 5 minutos de eventos gravados."""
    # O método obter_contexto_recente foi desenhado na nossa arquitetura anterior
    eventos = await memoria_episodica_servico.obter_contexto_recente(minutos=10)
    return {"historico": eventos}
