import asyncio
from datetime import datetime

# Importa os serviços existentes que serão orquestrados
from servicos.perfil_servico import servico_perfil
from servicos.servico import servico_timeline
from api.status import servico_status

# Imports para a nova estrutura de cards
from .dto import (
    HomeDTO,
    AnyCard,
    BoasVindasCard, BoasVindasContent,
    ResumoCognitivoCard, ResumoCognitivoContent,
    TimelineCard, TimelineContent,
    StatusLLMCard
)

class ServicoHome:
    """
    Orquestra múltiplos serviços para construir a resposta agregada
    para o endpoint /home, agora baseado em um sistema dinâmico de cards.
    """
    def _gerar_saudacao(self) -> str:
        """Gera uma saudação baseada no período do dia."""
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return "Bom dia!"
        elif 12 <= current_hour < 18:
            return "Boa tarde!"
        else:
            return "Boa noite!"

    async def gerar_home(self) -> HomeDTO:
        """
        Chama outros serviços em paralelo e transforma seus resultados em uma
        lista de 'cards' que compõem a tela inicial.
        """
        # 1. Executa as chamadas de serviço em paralelo para máxima eficiência
        perfil_task = servico_perfil.gerar_perfil_cognitivo()
        timeline_task = servico_timeline.gerar_timeline()
        status_task = servico_status.gerar_status_sistema()

        perfil_cognitivo, timeline, status_sistema = await asyncio.gather(
            perfil_task, timeline_task, status_task
        )

        # 2. Monta a lista de cards dinamicamente
        cards: list[AnyCard] = []

        # Card de Resumo Cognitivo
        if perfil_cognitivo and perfil_cognitivo.resumo_comportamental:
            cards.append(ResumoCognitivoCard(conteudo=ResumoCognitivoContent(texto=perfil_cognitivo.resumo_comportamental)))

        # Card de Timeline
        if timeline and timeline.eventos:
            cards.append(TimelineCard(conteudo=TimelineContent(eventos=timeline.eventos[:3])))

        # 2.1. Lógica de "Boas-Vindas" para novos usuários (cold start)
        # Se nenhum card de conteúdo principal foi gerado, mostramos uma mensagem de boas-vindas.
        if not cards:
            cards.append(
                BoasVindasCard(
                    conteudo=BoasVindasContent(
                        titulo="Bem-vindo ao Ollie!",
                        texto="Parece que estou começando a te conhecer. Use seu celular normalmente e em breve começarei a ter insights para compartilhar com você aqui."
                    )
                )
            )
        else:
            # 2.2. Adiciona cards de sistema apenas se já houver conteúdo principal
            # O card de status da LLM é útil para depuração, mas não como conteúdo principal.
            if status_sistema and status_sistema.llm:
                cards.append(StatusLLMCard(conteudo=status_sistema.llm))

        # 3. Monta o DTO final da Home
        return HomeDTO(
            saudacao=self._gerar_saudacao(),
            cards=cards
        )

servico_home = ServicoHome()