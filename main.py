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
from agentes.agente_reflexo import AgenteReflexo
from agentes.agente_notificacoes import AgenteNotificacoes
from agentes.agente_gestor_interrupcoes import AgenteGestorInterrupcoes
from agentes.agente_roteador_cognitivo import AgenteRoteadorCognitivo
from agentes.agente_episodico import AgenteEpisodico
from agentes.agente_raciocinio import AgenteRaciocinio
from agentes.agente_memoria_trabalho import AgenteMemoriaTrabalho
from agentes.agente_musica import AgenteMusica
from agentes.agente_pesquisa import AgentePesquisa
from agentes.agente_foco import AgenteFoco
from agentes.agente_sumarizador_perfil import AgenteSumarizadorPerfil
from agentes.agente_aprendizagem import AgenteAprendizagem
from agentes.agente_clima import AgenteClima
from agentes.agente_rotina import AgenteRotina
from agentes.agente_bem_estar import AgenteBemEstar
from servicos.agente_contexto_sistema import AgenteContextoSistema
from api.eventos import router as eventos_router
from api.websocket import router as ws_router
from api.testes import router as testes_router
from api.perfil import router as perfil_router
from api.feedback import router as feedback_router
from banco.database import inicializar_banco
from servicos.memoria_episodica import MemoriaEpisodica

# =================================================
#  LINK DE SERVIDOR (API) PARA O CLIENTE ANDROID
# =================================================
from api.perfil import router as perfil_router
from api.status import router as status_router
from api.memoria import router as memoria_router
from servicos.router import router as timeline_router
from api.router import router as home_router


# ==========================================
# 1. GERENCIADOR DE CICLO DE VIDA (BOOT)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("[Kernel] Verificando e inicializando estruturas de memória (SQLite)...")
    await inicializar_banco()
    print("[Kernel] Estruturas neurais prontas!")

    # --- INSTANCIAÇÃO E REGISTRO DOS AGENTES ---
    # Esta lógica agora executa apenas uma vez no boot, evitando duplicatas.
    print("[Kernel] Instanciando e registrando agentes cognitivos...")
    agente_perfil = AgentePerfil()
    agente_inferencia = AgenteInferencia()
    agente_reflexo = AgenteReflexo()
    agente_notificacoes = AgenteNotificacoes()
    agente_gestor_interrupcoes = AgenteGestorInterrupcoes()
    agente_roteador_cognitivo = AgenteRoteadorCognitivo()
    agente_episodico = AgenteEpisodico()
    agente_raciocinio = AgenteRaciocinio()
    agente_memoria_trabalho = AgenteMemoriaTrabalho()
    agente_musica = AgenteMusica()
    agente_pesquisa = AgentePesquisa()
    agente_foco = AgenteFoco()
    agente_sumarizador_perfil = AgenteSumarizadorPerfil()
    agente_aprendizagem = AgenteAprendizagem()
    agente_contexto_sistema = AgenteContextoSistema()
    agente_clima = AgenteClima(memoria_trabalho=agente_memoria_trabalho)
    agente_rotina = AgenteRotina()
    agente_bem_estar = AgenteBemEstar()

    # Disponibiliza agentes para o ciclo de vida da app, se necessário
    app.state.agente_memoria_trabalho = agente_memoria_trabalho

    # --- REGISTRO DOS AGENTES NO KERNEL ---
    # Pipeline Principal (Eventos brutos com acao=NORMAL)
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL, callback=agente_perfil.processar
    )
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL, callback=agente_inferencia.processar
    )

    # Agentes de Reflexo especializados por categoria
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL
        and e.categoria == CategoriaEvento.NOTIFICACAO,
        callback=agente_reflexo.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL
        and e.categoria == CategoriaEvento.MEDIA,
        callback=agente_musica.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL
        and e.categoria == CategoriaEvento.APP_FOREGROUND,
        callback=agente_foco.processar,
    )
    # Agente de Foco também ouve mudanças de local
    kernel.registrar(
        filtro=lambda e: e.categoria == CategoriaEvento.SISTEMA_COMANDO_INTERNO 
        and e.payload.get("tipo") == "MUDANCA_LOCAL",
        callback=agente_foco.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL
        and e.categoria == CategoriaEvento.SENSOR_SYSTEM_CONTEXT,
        callback=agente_contexto_sistema.processar,
    )

    # Agentes de Rotina e Contexto Complexo
    kernel.registrar(
        filtro=lambda e: e.categoria == CategoriaEvento.SISTEMA_COMANDO_INTERNO,
        callback=agente_rotina.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.categoria == CategoriaEvento.APP_FOREGROUND,
        callback=agente_bem_estar.processar,
    )

    # Pipeline de Saída de Notificações (com gestão de interrupções)
    kernel.registrar(
        filtro=lambda e: e.categoria == CategoriaEvento.INTENCAO_NOTIFICACAO,
        callback=agente_gestor_interrupcoes.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.categoria == CategoriaEvento.NOTIFICACAO_PRONTA_PARA_ENVIO,
        callback=agente_notificacoes.processar,
    )

    # Pipeline Cognitivo (Eventos gerados pelos reflexos)
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.EVENTO_COMPLEXO,
        callback=agente_roteador_cognitivo.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.INTENCAO_RACIOCINIO,
        callback=agente_raciocinio.processar,
    )
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.INTENCAO_PESQUISA,
        callback=agente_pesquisa.processar,
    )

    # Pipeline de Saída e Memória (Agentes terminais ou passivos)
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.RESULTADO_PESQUISA,
        callback=agente_raciocinio.sintetizar_com_pesquisa,
    )
    kernel.registrar(filtro=lambda e: True, callback=agente_episodico.processar)

    # Pipeline de Comandos do Sistema
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.GERAR_RESUMO_PERFIL,
        callback=agente_sumarizador_perfil.processar,
    )

    # Pipeline de Aprendizado (Feedback do usuário)
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.FEEDBACK_USUARIO,
        callback=agente_aprendizagem.processar,
    )

    # Pipeline de Agrupamento de Contexto (Memória de Trabalho)
    kernel.registrar(
        filtro=lambda e: e.acao == TipoAcao.NORMAL
        and e.categoria == CategoriaEvento.NOTIFICACAO,
        callback=agente_memoria_trabalho.processar,
    )

    # Pipeline de Contexto Clima (Corrigido para ouvir o comando do ciclo)
    kernel.registrar(
        filtro=lambda e: e.categoria == CategoriaEvento.SISTEMA_COMANDO_INTERNO and e.acao == TipoAcao.ATUALIZAR_CONTEXTO,
        callback=agente_clima.processar,
    )

    async def ciclo_meteorologico():
        """Gera um evento de sistema a cada 30 minutos para atualizar o clima."""
        while True:
            evento_clima = EventoCanonico(
                categoria=CategoriaEvento.SISTEMA_COMANDO_INTERNO,
                acao=TipoAcao.ATUALIZAR_CONTEXTO,
                origem=OrigemEvento.SISTEMA,
                pacote="sistema.interno",
                payload={"alvo": "clima"},
            )
            await kernel.publicar(evento_clima)
            await asyncio.sleep(1800)  # Dorme por 30 minutos

    async def ciclo_reflexao_rotina():
        """Gera um gatilho para o Agente de Rotina a cada 1 hora."""
        while True:
            await asyncio.sleep(3600)
            evento_reflexao = EventoCanonico(
                categoria=CategoriaEvento.SISTEMA_COMANDO_INTERNO,
                acao=TipoAcao.NORMAL,
                origem=OrigemEvento.SISTEMA,
                pacote="sistema.interno",
                payload={"tipo": "REFLEXAO_ROTINA"},
            )
            await kernel.publicar(evento_reflexao)

    # --- INÍCIO DOS PROCESSOS EM BACKGROUND (ANTES DO YIELD!) ---
    tarefa_clima = asyncio.create_task(ciclo_meteorologico())
    tarefa_rotina = asyncio.create_task(ciclo_reflexao_rotina())
    asyncio.create_task(kernel.iniciar())
    print("🚀 Kernel Cognitivo e Sensores Ambientais iniciados.")

    yield  # <-- ÚNICO YIELD PERMITIDO NO FASTAPI! A API FICA A RODAR AQUI.

    # --- SHUTDOWN (DESLIGAMENTO) ---
    print("[Kernel] Desligando sistema cognitivo...")
    tarefa_clima.cancel() # Para o relógio do clima
    tarefa_rotina.cancel()
    
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
app.include_router(testes_router)
app.include_router(feedback_router)
app.include_router(home_router, prefix="/api/v1/home", tags=["Home"])
app.include_router(perfil_router, prefix="/api/v1/perfil", tags=["Perfil"])
app.include_router(status_router, prefix="/api/v1/status", tags=["Status"])
app.include_router(memoria_router, prefix="/api/v1/memory", tags=["Memória"])
app.include_router(timeline_router, prefix="/api/v1/timeline", tags=["Timeline"])
