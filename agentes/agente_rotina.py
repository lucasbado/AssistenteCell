"""
agentes/agente_rotina.py

Agente de Inteligência de Longo Prazo.
Analisa o perfil e o histórico de eventos para descobrir padrões complexos e rotinas.
"""
import logging
from datetime import datetime

from core.evento import EventoCanonico
from core.tipos import CategoriaEvento, TipoAcao, OrigemEvento, PrioridadeEvento
from core.kernel import kernel
from servicos.memoria_perfil import memoria_perfil

logger = logging.getLogger("AgenteRotina")

class AgenteRotina:
    """
    Este agente não reage a eventos imediatos, mas sim a gatilhos de 'reflexão'
    ou mudanças de contexto sistêmico (como chegar em casa).
    """
    async def processar(self, evento: EventoCanonico):
        if evento.categoria != CategoriaEvento.SISTEMA_COMANDO_INTERNO:
            return

        tipo_comando = evento.payload.get("tipo")
        
        if tipo_comando == "MUDANCA_LOCAL":
            await self._reagir_chegada_local(evento.payload.get("local"), evento)
        elif tipo_comando == "REFLEXAO_ROTINA":
            await self._analisar_padroes_gerais()

    async def _reagir_chegada_local(self, local: str, evento_origem: EventoCanonico):
        logger.info(f"🎭 AgenteRotina: Planejando ações para o local {local}")
        
        if local == "CASA":
            # Sugestão de descompressão
            await kernel.publicar(
                evento_origem.clonar(
                    id=None,
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    origem=OrigemEvento.IA,
                    payload={
                        "titulo": "Bem-vindo de volta!",
                        "texto": "Notei que você chegou em casa. Que tal uma música relaxante para descansar?",
                        "acao_tipo": "OPEN_APP",
                        "acao_parametro": "com.spotify.music",
                        "acao_texto": "Abrir Spotify"
                    }
                )
            )
        elif local == "TRABALHO":
            # Sugestão de foco
            await kernel.publicar(
                evento_origem.clonar(
                    id=None,
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    origem=OrigemEvento.IA,
                    payload={
                        "titulo": "Hora de Produzir",
                        "texto": "Você chegou no trabalho. Deseja que eu silencie as notificações não urgentes por 1 hora?",
                        "acao_tipo": "SISTEMA_COMANDO",
                        "acao_parametro": "ATIVAR_FOCO",
                        "acao_texto": "Ativar Foco"
                    }
                )
            )

    async def _analisar_padroes_gerais(self):
        """
        Lógica para ler a MemoriaPerfil e descobrir correlações.
        (Versão simplificada para MVP)
        """
        logger.info("🧠 AgenteRotina: Iniciando reflexão sobre padrões de uso...")
        top_apps = await memoria_perfil.obter_top_entidades(categoria="APP_USO", limite=3)
        # Aqui poderíamos disparar insights para a Home baseados no volume de uso
        # ou sugerir 'curas' para vícios em certos apps.
