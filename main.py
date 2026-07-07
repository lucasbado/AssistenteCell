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
from agentes.agente_roteador_cognitivo import AgenteRoteadorCognitivo
from agentes.agente_episodico import AgenteEpisodico
from agentes.agente_raciocinio import AgenteRaciocinio
from agentes.agente_prioridade import AgentePrioridade  # Importe o novo agente
from agentes.agente_memoria_trabalho import AgenteMemoriaTrabalho
from agentes.agente_musica import AgenteMusica
from agentes.agente_pesquisa import AgentePesquisa
from agentes.agente_foco import AgenteFoco
from agentes.agente_sumarizador_perfil import AgenteSumarizadorPerfil
from api.eventos import router as eventos_router
from api.websocket import router as ws_router
from api.testes import router as testes_router
from api.perfil import router as perfil_router
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

    # Inicia ciclos de manutenção dos agentes que precisam
    agente_memoria_trabalho = app.state.agente_memoria_trabalho
    asyncio.create_task(agente_memoria_trabalho.iniciar_ciclo_esquecimento())

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
app.include_router(testes_router)
app.include_router(perfil_router)

# ==========================================
# 5. INSTANCIAÇÃO E REGISTRO DOS AGENTES
# ==========================================

agente_perfil = AgentePerfil()
agente_inferencia = AgenteInferencia()
agente_reflexo = AgenteReflexo()
agente_notificacoes = AgenteNotificacoes()
agente_roteador_cognitivo = AgenteRoteadorCognitivo()
agente_episodico = AgenteEpisodico()
agente_raciocinio = AgenteRaciocinio()
agente_prioridade = AgentePrioridade()  # Instancie o novo agente
agente_memoria_trabalho = AgenteMemoriaTrabalho()
agente_musica = AgenteMusica()
agente_pesquisa = AgentePesquisa()
agente_foco = AgenteFoco()
agente_sumarizador_perfil = AgenteSumarizadorPerfil()

# Registre os agentes no Kernel

# =================================================================
# Pipeline Principal (Eventos brutos com acao=NORMAL)
# =================================================================
# 1. Agentes que analisam e enriquecem o evento inicial
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL,
    callback=agente_perfil.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL,
    callback=agente_prioridade.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL,
    callback=agente_inferencia.processar
)
# 2. Agentes de Reflexo especializados por categoria
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL and e.categoria == CategoriaEvento.NOTIFICACAO,
    callback=agente_reflexo.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL and e.categoria == CategoriaEvento.MEDIA,
    callback=agente_musica.processar
)
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.NORMAL and e.categoria == CategoriaEvento.APP_FOREGROUND,
    callback=agente_foco.processar
)

# =================================================================
# Pipeline Cognitivo (Eventos gerados pelos reflexos)
# =================================================================
# 2. Roteador para eventos complexos
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.EVENTO_COMPLEXO,
    callback=agente_roteador_cognitivo.processar
)
# 3. Agente de raciocínio que usa a LLM
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.INTENCAO_RACIOCINIO,
    callback=agente_raciocinio.processar
)
# 3.5 Agente de Pesquisa que é ativado pela intenção de pesquisar
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.INTENCAO_PESQUISA,
    callback=agente_pesquisa.processar
)

# =================================================================
# Pipeline de Saída e Memória (Agentes terminais ou passivos)
# =================================================================
# 4. Agente de notificação que interage com o usuário
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.INTENCAO_INTERACAO,
    callback=agente_notificacoes.processar
)
# 4.5. O Agente de Raciocínio também escuta os resultados da pesquisa para sintetizar uma resposta
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.RESULTADO_PESQUISA,
    callback=agente_raciocinio.sintetizar_com_pesquisa
)
# 5. Agente de memória que arquiva tudo
kernel.registrar(
    filtro=lambda e: True,
    callback=agente_episodico.processar
)
# 6. Agente de Memória de Trabalho que observa os resultados da IA
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.INTENCAO_INTERACAO,
    callback=agente_memoria_trabalho.processar
)

# =================================================================
# Pipeline de Comandos do Sistema
# =================================================================
kernel.registrar(
    filtro=lambda e: e.acao == TipoAcao.GERAR_RESUMO_PERFIL,
    callback=agente_sumarizador_perfil.processar
)

# Disponibiliza agentes para o ciclo de vida da app, se necessário
app.state.agente_memoria_trabalho = agente_memoria_trabalho
