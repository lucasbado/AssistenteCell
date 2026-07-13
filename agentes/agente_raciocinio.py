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
from core.tipos import PrioridadeEvento, OrigemEvento, TipoAcao, CategoriaEvento
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

        # 2. Verifica se a LLM emitiu uma Decisão Cognitiva (Automação)
        if "decisao" in resultado:
            logger.info(f"⚡ [Raciocínio] LLM emitiu uma DECISÃO: {resultado['decisao']}")
            # Publica a decisão para que outros agentes (Foco, Música, Execução) possam reagir
            await kernel.publicar(
                evento.clonar(
                    categoria=CategoriaEvento.SISTEMA_COMANDO_INTERNO,
                    acao=TipoAcao.ATUALIZAR_CONTEXTO,
                    origem=OrigemEvento.IA,
                    payload=resultado
                )
            )

        # 3. Verifica se a LLM solicitou uma pesquisa na web
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

        # 3. Se não precisa pesquisar, verifica o tipo de interação que a IA decidiu.
        tipo_interacao = resultado.get("tipo_interacao")
        if tipo_interacao == "NOTIFICAR":
            # Apenas se a IA decidir explicitamente por uma notificação, o fluxo continua.
            mensagem = resultado.get("mensagem_dinamica")
            prioridade_str = resultado.get("prioridade", "NORMAL").upper()
            try:
                prioridade = PrioridadeEvento[prioridade_str]
            except KeyError:
                logger.warning(f"LLM retornou prioridade inválida '{prioridade_str}'. Usando NORMAL.")
                prioridade = PrioridadeEvento.NORMAL

            if mensagem and mensagem.strip():
                # Prepara o payload da notificação
                payload_notificacao = {
                    "texto": mensagem,
                    "titulo": "Assistente",
                    "contexto": resultado.get("contexto_extra", {}),
                    "remetente": evento.payload.get("titulo")
                }

                # Adiciona a ação sugerida pela IA, se houver
                acao_sugerida = resultado.get("acao_sugerida")
                if acao_sugerida and isinstance(acao_sugerida, dict):
                    payload_notificacao["acao_tipo"] = acao_sugerida.get("tipo")
                    payload_notificacao["acao_parametro"] = acao_sugerida.get("parametro")
                    payload_notificacao["acao_texto"] = acao_sugerida.get("texto_botao")

                # Publica um novo evento de INTENCAO_INTERACAO
                evento_intencao = evento.clonar(
                    categoria=CategoriaEvento.INTENCAO_NOTIFICACAO,
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    origem=OrigemEvento.IA,
                    prioridade=prioridade,
                    payload=payload_notificacao
                )
                await kernel.publicar(evento_intencao)
                logger.info(f"🧠 [Raciocínio] Gerada intenção: {mensagem[:50]}...")
        else:
            # Se for ATUALIZACAO_SILENCIOSA ou IGNORAR, a ação termina aqui.
            logger.info(f"🤫 [Raciocínio] Decisão da IA: {tipo_interacao}. Contexto atualizado sem notificação.")

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
                    "texto": resultado_sintese["mensagem_dinamica"],
                    "titulo": "Assistente",
                }
            )
            await kernel.publicar(evento_final)
            logger.info(f"🧠 [Raciocínio] Síntese final gerada: {resultado_sintese['mensagem_dinamica'][:50]}...")
