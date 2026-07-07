from __future__ import annotations
import asyncio
import logging
from core.evento import EventoCanonico
from core.tipos import TipoAcao, OrigemEvento
from servicos.memoria_trabalho import memoria_trabalho
from servicos.memoria_perfil import memoria_perfil

logger = logging.getLogger(__name__)

class AgenteMemoriaTrabalho:
    """
    Agente responsável por gerenciar a Memória de Trabalho, que armazena
    o contexto de conversas ativas e implementa uma mecânica de esquecimento.
    """
    def __init__(self):
        self.memoria = memoria_trabalho
        self.ciclo_esquecimento_ativo = False

    async def processar(self, evento: EventoCanonico):
        if evento.origem == OrigemEvento.IA and evento.pacote == "com.whatsapp":
            remetente = evento.payload.get("remetente")
            mensagem_resumida = evento.payload.get("mensagem")

            if not remetente or not mensagem_resumida:
                return

            perfil_contato = await memoria_perfil.obter_perfil_contato(remetente)
            incremento_relevancia = 1.0 + (perfil_contato.confianca if perfil_contato else 0.0)

            chave_conversa = f"whatsapp::{remetente.lower()}"
            
            await self.memoria.atualizar_conversa(
                chave_conversa=chave_conversa,
                nova_mensagem=mensagem_resumida,
                incremento_relevancia=incremento_relevancia
            )
            logger.info(f"🧠 [MemoriaTrabalho] Contexto da conversa com '{remetente}' atualizado.")

    async def iniciar_ciclo_esquecimento(self, intervalo_minutos: int = 60):
        if self.ciclo_esquecimento_ativo: return
        self.ciclo_esquecimento_ativo = True
        logger.info(f"⏰ [MemoriaTrabalho] Ciclo de esquecimento iniciado. Verificando a cada {intervalo_minutos} minutos.")
        while True:
            await asyncio.sleep(intervalo_minutos * 60)
            conversas_esquecidas = await self.memoria.esquecer_conversas_irrelevantes()
            if conversas_esquecidas > 0:
                logger.info(f"🗑️ [MemoriaTrabalho] {conversas_esquecidas} conversas irrelevantes foram esquecidas.")