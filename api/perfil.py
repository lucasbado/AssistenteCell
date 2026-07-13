"""
api/perfil.py

Endpoints para interagir com o perfil do usuário.
"""
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import APIRouter, Request

from core.kernel import kernel
from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, OrigemEvento, TipoAcao, PrioridadeEvento
from servicos.memoria_perfil import memoria_perfil
from servicos.perfil_servico import servico_perfil

router = APIRouter(tags=["Perfil"])

# --- Modelo de dados para o clima, correspondendo ao DTO Kotlin ClimaInfo ---
class ClimaInfo(BaseModel):
    temperatura: str
    condicao: str
    icon_url: Optional[str] = None
    atualizado_em: Optional[str] = None

# --- Modelos de Resposta para o endpoint analítico ---

class ItemPerfil(BaseModel):
    item: str = Field(..., description="O valor do item, ex: com.whatsapp ou 'Staind'")
    confianca: float = Field(..., description="Confiança do sistema neste fato (0.0 a 1.0)")
    score: int = Field(..., description="Score bruto de interações, indicando frequência")

class RotinaMusical(ItemPerfil):
    periodo: str = Field(..., description="Período do dia da rotina (MANHA, TARDE, NOITE, MADRUGADA)")

class PerfilAnaliticoResponse(BaseModel):
    apps_mais_usados: List[ItemPerfil]
    contatos_mais_frequentes: List[ItemPerfil]
    rotinas_musicais: List[RotinaMusical]
    clima: Optional[ClimaInfo] = None

@router.get("/", summary="Retorna o perfil cognitivo do usuário", description="Agrega todas as informações aprendidas sobre os hábitos e preferências do usuário em uma única visão consolidada e narrativa.")
async def get_perfil_cognitivo():
    """
    Endpoint que constrói e retorna o perfil cognitivo do usuário.
    Este é o endpoint principal para a tela de perfil.
    """
    # O servico_perfil é responsável por orquestrar a geração do DTO
    # a partir de várias fontes de memória.
    return await servico_perfil.gerar_perfil_cognitivo()


@router.post("/resumo", status_code=status.HTTP_202_ACCEPTED)
async def solicitar_resumo_perfil():
    """
    Dispara um evento para que o sistema gere um resumo do perfil do usuário
    e o envie como uma notificação.
    """
    evento_comando = EventoCanonico(
        categoria=CategoriaEvento.SISTEMA_COMANDO_USUARIO,
        acao=TipoAcao.GERAR_RESUMO_PERFIL,
        origem=OrigemEvento.USUARIO,
        pacote="br.com.ollie.interface",
        prioridade=PrioridadeEvento.ALTA,
    )
    await kernel.publicar(evento_comando)
    return {"status": "solicitacao_de_resumo_enfileirada", "id": evento_comando.id}

@router.get("/analitico", response_model=PerfilAnaliticoResponse)
async def obter_perfil_analitico(request: Request): # <-- Adicionado request
    """
    Retorna uma visão analítica e estruturada do perfil do usuário.
    """
    fatos_perfil = await memoria_perfil.obter_perfil_completo(confianca_minima=0.2)

    apps = []
    contatos = []
    musica = []

    for fato in fatos_perfil:
        if fato.categoria == "APP_USO":
            apps.append(ItemPerfil(item=fato.valor, confianca=fato.confianca, score=fato.score))
        elif fato.categoria == "CONTATO_INTERACAO":
            contatos.append(ItemPerfil(item=fato.valor, confianca=fato.confianca, score=fato.score))
        elif fato.categoria.startswith("ARTISTA_PREFERENCIA_"):
            periodo = fato.categoria.split('_')[-1]
            musica.append(RotinaMusical(item=fato.valor, confianca=fato.confianca, score=fato.score, periodo=periodo))

    # --- INJEÇÃO DE CONTEXTO CLIMÁTICO ---
    # Vai à instância global da Memória de Trabalho procurar se o AgenteClima já depositou lá os dados
    memoria_trabalho = request.app.state.agente_memoria_trabalho
    dados_clima_interno = getattr(memoria_trabalho, 'contexto_atual', None)

    clima_dto = None
    if dados_clima_interno:
        icon_code = dados_clima_interno.get("icon_code")
        # O frontend espera uma URL, então construímos uma URL de placeholder.
        # Em um sistema real, estes ícones estariam em um CDN.
        icon_url = f"https://cdn.example.com/weather_icons/v1/{icon_code}.svg" if icon_code else None
        clima_dto = ClimaInfo(
            temperatura=dados_clima_interno.get("temperatura", "--"),
            condicao=dados_clima_interno.get("condicao", "N/A"),
            icon_url=icon_url,
            atualizado_em=dados_clima_interno.get("atualizado_em")
        )

    return PerfilAnaliticoResponse(
        apps_mais_usados=sorted(apps, key=lambda x: x.score, reverse=True),
        contatos_mais_frequentes=sorted(contatos, key=lambda x: x.score, reverse=True),
        rotinas_musicais=sorted(musica, key=lambda x: x.score, reverse=True),
        clima=clima_dto
    )