"""
agentes/agente_sumarizador_perfil.py

Agente responsável por analisar o perfil de usuário aprendido e gerar
um resumo em linguagem natural para o próprio usuário.
"""
import logging
from collections import defaultdict

from core.evento import EventoCanonico
from core.tipos import TipoAcao, OrigemEvento, CategoriaEvento
from core.kernel import kernel
from servicos.memoria_perfil import memoria_perfil
from servicos.llm import ServicoLLM

logger = logging.getLogger(__name__)

class AgenteSumarizadorPerfil:
    def __init__(self):
        self.llm = ServicoLLM()

    async def processar(self, evento: EventoCanonico):
        logger.info("🧠 [Sumarizador] Iniciando geração de resumo de perfil de usuário.")

        # 1. Coletar todos os dados do perfil com confiança mínima
        fatos_perfil = await memoria_perfil.obter_perfil_completo(confianca_minima=0.6)
        if not fatos_perfil:
            await self._publicar_resultado("Ainda não aprendi o suficiente sobre você para criar um resumo. Use mais o seu celular!", evento)
            return

        # 2. Formatar os dados para a LLM
        dados_formatados = self._formatar_fatos_para_llm(fatos_perfil)

        # 3. Chamar a LLM para gerar o resumo
        resultado_llm = await self.llm.resumir_perfil_usuario(dados_formatados)
        resumo = resultado_llm.get("resumo")

        # 4. Publicar o resultado como uma interação
        await self._publicar_resultado(resumo, evento)
        logger.info("🧠 [Sumarizador] Resumo de perfil enviado ao usuário.")

    def _formatar_fatos_para_llm(self, fatos: list) -> str:
        """Converte a lista de fatos do banco em um texto legível para a LLM."""
        dados = defaultdict(list)
        for fato in fatos:
            # Ex: ARTISTA_PREFERENCIA_MANHA -> ARTISTA_PREFERENCIA
            categoria_base = '_'.join(fato.categoria.split('_')[:-1]) if '_' in fato.categoria else fato.categoria
            dados[categoria_base].append(f"- {fato.valor} (Confiança: {fato.confianca:.0%})")

        texto_formatado = []
        if dados.get("CONTATO_INTERACAO"):
            texto_formatado.append("Contatos com quem você mais interage:")
            texto_formatado.extend(dados["CONTATO_INTERACAO"])
        
        if dados.get("APP_USO"):
            texto_formatado.append("\nAplicativos que você mais usa:")
            texto_formatado.extend(dados["APP_USO"])

        if dados.get("ARTISTA_PREFERENCIA"):
            texto_formatado.append("\nArtistas que você mais ouve:")
            texto_formatado.extend(dados["ARTISTA_PREFERENCIA"])

        return "\n".join(texto_formatado)

    async def _publicar_resultado(self, resumo: str, evento_original: EventoCanonico):
        """Envia o resumo para o usuário através de uma notificação."""
        await kernel.publicar(
            evento_original.clonar(
                categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                acao=TipoAcao.INTENCAO_INTERACAO,
                origem=OrigemEvento.IA,
                payload={
                    "titulo": "O que aprendi sobre você",
                    "texto": resumo,
                }
            )
        )