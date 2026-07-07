"""
agentes/agente_raciocinio.py

Camada 4: Cognição.

Agente responsável por invocar a LLM (o "córtex") quando um evento é
considerado complexo ou ambíguo o suficiente pelas camadas inferiores.
Ele escuta a intenção de raciocinar e, se necessário, gera uma intenção de interação.
"""

from __future__ import annotations
import json

import logging

from core.evento import EventoCanonico
from core.tipos import PrioridadeEvento, OrigemEvento, TipoAcao
from core.kernel import kernel
from servicos.llm import ServicoLLM
from servicos.memoria_episodica import MemoriaEpisodica

logger = logging.getLogger(__name__)

class AgenteRaciocinio:
    def __init__(self):
        self.llm = ServicoLLM()
        self.memoria_episodica = MemoriaEpisodica()

    async def processar(self, evento: EventoCanonico):
        # Este agente só deve ser ativado por uma INTENCAO_RACIOCINIO
        if evento.acao != TipoAcao.INTENCAO_RACIOCINIO:
            return
        logger.info(f"🧠 [Raciocínio] Recebido evento para análise profunda: {evento.id[:8]}")

        # Log de diagnóstico para verificar o payload antes de chamar a LLM
        log_payload = {
            "categoria": evento.categoria.value,
            "pacote": evento.pacote,
            "payload": evento.payload
        }
        logger.info(f"Payload enviado para LLM: {json.dumps(log_payload, ensure_ascii=False, indent=2)}")

        # 1. Chama a LLM para uma primeira análise do evento
        resultado = await self.llm.classificar_evento(
            categoria=evento.categoria.value,
            pacote=evento.pacote,
            payload=evento.payload,
        )

        # 2. Verifica se a LLM solicitou uma pesquisa na web
        if resultado.get("contexto_extra", {}).get("precisa_pesquisar"):
            query = resultado.get("contexto_extra", {}).get("query")
            if query:
                logger.info(f"🧠 [Raciocínio] LLM solicitou pesquisa por '{query}'. Delegando ao AgentePesquisa.")
                await kernel.publicar(
                    evento.clonar(
                        acao=TipoAcao.INTENCAO_PESQUISA,
                        payload={"query": query}
                    )
                )
                return # O fluxo para aqui e será retomado quando o resultado da pesquisa chegar.

        # 3. Se não precisa pesquisar, verifica se é necessário agir
        elif resultado.get("acao_necessaria", False):
            mensagem = resultado.get("mensagem_dinamica")
            if mensagem:
                # Publica um novo evento de INTENCAO_INTERACAO
                evento_intencao = evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    origem=OrigemEvento.IA,
                    payload={
                        "mensagem": mensagem,
                        "titulo": "Assistente",  # ou extraído do contexto
                        "contexto": resultado.get("contexto_extra", {}),
                        "remetente": evento.payload.get("titulo") # Passa o remetente original
                    }
                )
                await kernel.publicar(evento_intencao)
                logger.info(f"🧠 [Raciocínio] Gerada intenção: {mensagem[:50]}...")
        else:
            logger.debug(f"🧠 [Raciocínio] Evento ignorado (sem ação necessária).")

    async def sintetizar_com_pesquisa(self, evento_resultado: EventoCanonico):
        """
        Processa o resultado de uma pesquisa na web, combina com o contexto original
        e gera uma resposta final.
        """
        logger.info(f"🧠 [Raciocínio] Recebido resultado de pesquisa ({evento_resultado.id[:8]}). Sintetizando resposta.")

        # 1. Recupera o evento original que disparou a cadeia de raciocínio
        evento_original_dict = await self.memoria_episodica.obter_evento_original_por_correlacao(evento_resultado.correlacao_id)
        if not evento_original_dict:
            logger.error(f"Não foi possível encontrar o evento original com ID de correlação {evento_resultado.correlacao_id}")
            return

        # 2. Prepara o payload para a LLM com o contexto original + resultados da pesquisa
        payload_sintese = {
            "evento_original": evento_original_dict,
            "resultado_pesquisa": evento_resultado.payload
        }

        # 3. Chama a LLM para gerar a resposta final
        resultado_sintese = await self.llm.classificar_evento(
            categoria="SINTESE_PESQUISA", # Categoria especial para a LLM entender o contexto
            pacote="br.com.ollie.kernel",
            payload=payload_sintese
        )

        # 4. Publica a interação final
        if resultado_sintese.get("acao_necessaria") and resultado_sintese.get("mensagem_dinamica"):
            evento_final = evento_resultado.clonar(
                acao=TipoAcao.INTENCAO_INTERACAO,
                origem=OrigemEvento.IA,
                payload={
                    "mensagem": resultado_sintese["mensagem_dinamica"],
                    "titulo": "Assistente",
                }
            )
            await kernel.publicar(evento_final)
            logger.info(f"🧠 [Raciocínio] Síntese final gerada: {resultado_sintese['mensagem_dinamica'][:50]}...")
