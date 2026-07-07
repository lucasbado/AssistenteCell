"""
agentes/agente_bem_estar.py

Responsável por gerenciar a frequência de interações com o usuário,
protegendo-o de sobrecarga cognitiva. Atua como um controlador de "orçamento de atenção".
"""
import logging
from datetime import datetime, timedelta, timezone

from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, TipoAcao, OrigemEvento
from core.kernel import kernel

logger = logging.getLogger(__name__)

# NOTA: Adicione estas categorias ao seu enum CategoriaEvento em core/tipos.py
# SISTEMA_PAUSA_INTERACOES = "SISTEMA_PAUSA_INTERACOES"
# SISTEMA_LIBERA_INTERACOES = "SISTEMA_LIBERA_INTERACOES"

class AgenteBemEstar:
    def __init__(self, cooldown_segundos: int = 90):
        self.cooldown_segundos = cooldown_segundos
        self.cooldown_ativo_ate: datetime | None = None
        self.interacoes_pausadas = False

    async def processar(self, evento: EventoCanonico):
        agora = datetime.now(timezone.utc)

        # 1. Verifica se o cooldown terminou para liberar as interações
        if self.interacoes_pausadas and self.cooldown_ativo_ate and agora >= self.cooldown_ativo_ate:
            self.interacoes_pausadas = False
            self.cooldown_ativo_ate = None
            logger.info("🧘 [Bem-Estar] Cooldown de interação terminado. Liberando interações.")
            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.SISTEMA_LIBERA_INTERACOES,
                    origem=OrigemEvento.SISTEMA,
                    payload={"motivo": "Cooldown de bem-estar expirado."}
                )
            )

        # 2. Detecta uma tentativa de interação de outro agente (como o Reflexo)
        if evento.acao == TipoAcao.INTENCAO_INTERACAO:
            if self.interacoes_pausadas:
                logger.debug(f"🧘 [Bem-Estar] Interação da categoria '{evento.categoria.value}' bloqueada devido a cooldown.")
                return

            logger.info(f"🧘 [Bem-Estar] Interação da categoria '{evento.categoria.value}' permitida. Ativando cooldown de {self.cooldown_segundos}s.")
            self.interacoes_pausadas = True
            self.cooldown_ativo_ate = agora + timedelta(seconds=self.cooldown_segundos)
            
            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.SISTEMA_PAUSA_INTERACOES,
                    origem=OrigemEvento.SISTEMA,
                    payload={"motivo": f"Interação sobre '{evento.categoria.value}' iniciou um cooldown."}
                )
            )