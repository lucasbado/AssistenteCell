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

logger = logging.getLogger(__name__)

class AgenteRaciocinio:
    def __init__(self):
        self.llm = ServicoLLM()

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

        # 1. Chama o LLM para classificar
        resultado = await self.llm.classificar_evento(
            categoria=evento.categoria.value,
            pacote=evento.pacote,
            payload=evento.payload,
        )

        # 2. Se o LLM indicar que é necessário agir
        if resultado.get("acao_necessaria", False):
            mensagem = resultado.get("mensagem_dinamica")
            if mensagem:
                # Publica um novo evento de INTENCAO_INTERACAO
                evento_intencao = evento.clonar(
                    acao=TipoAcao.INTENCAO_INTERACAO,
                    origem=OrigemEvento.IA,
                    payload={
                        "mensagem": mensagem,
                        "titulo": "Assistente",  # ou extraído do contexto
                        "contexto": resultado.get("contexto_extra", {})
                    }
                )
                await kernel.publicar(evento_intencao)
                logger.info(f"🧠 [Raciocínio] Gerada intenção: {mensagem[:50]}...")
        else:
            logger.debug(f"🧠 [Raciocínio] Evento ignorado (sem ação necessária).")
