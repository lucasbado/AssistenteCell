"""
core/kernel.py

Kernel Cognitivo

Responsável por:

- Receber eventos
- Enfileirar
- Distribuir para especialistas
- Controlar prioridade
- Manter métricas simples
"""

from __future__ import annotations

import asyncio
import logging

from typing import Awaitable, Callable

from core.evento import EventoCanonico
from core.tipos import EstadoEvento, TipoAcao

logger = logging.getLogger("Kernel")


Callback = Callable[[EventoCanonico], Awaitable[None]]
Filtro = Callable[[EventoCanonico], bool]

class KernelCognitivo:

    def __init__(self):

        # Lista de tuplas (filtro, callback)
        self._listeners: list[tuple[Filtro, Callback]] = []

        # Fila de prioridade
        self._fila = asyncio.PriorityQueue()

        # Métricas
        self.eventos_recebidos = 0
        self.eventos_processados = 0

        self._contador = 0

    # ----------------------------------------------------
    # Registro de especialistas
    # ----------------------------------------------------

    def registrar(
        self,
        filtro: Filtro,
        callback: Callback,
    ):
        """Registra um callback que será acionado se o filtro retornar True para um evento."""
        self._listeners.append((filtro, callback))
        # O nome da função pode ser útil para debugging
        logger.info(f"[Kernel] Listener registrado com filtro para: {callback.__qualname__}")

    # ----------------------------------------------------
    # Publicação
    # ----------------------------------------------------

    async def publicar(
        self,
        evento: EventoCanonico,
    ):

        self.eventos_recebidos += 1

        self._contador += 1

        prioridade = -evento.prioridade.value

        await self._fila.put(
            (
                prioridade,
                self._contador,
                evento,
            )
        )

        logger.info(
            f"[Kernel] Evento publicado "
            f"{evento.categoria.value}/{evento.acao.value} "
            f"({evento.id[:8]})"
        )

    # ----------------------------------------------------
    # Loop Principal
    # ----------------------------------------------------

    async def iniciar(self):

        logger.info("Kernel iniciado.")

        while True:

            _, _, evento = await self._fila.get()

            evento.estado = EstadoEvento.EM_PROCESSAMENTO

            try: # O try/except garante que o Kernel nunca pare, mesmo que um agente falhe
                await self._despachar(evento)
                self.eventos_processados += 1
            except Exception as e:
                # Loga o erro, mas o Kernel continua seu trabalho.
                # A rastreabilidade do evento com falha pode ser feita na camada de observabilidade.
                logger.exception(f"Erro irrecuperável ao despachar evento {evento.id[:8]}: {e}")
            finally: # Garante que a tarefa seja marcada como concluída na fila
                self._fila.task_done()

    # ----------------------------------------------------
    # Distribuição
    # ----------------------------------------------------

    async def _despachar(self, evento: EventoCanonico):
        # Filtra os agentes interessados
        tarefas = []
        for filtro, callback in self._listeners:
            if filtro(evento):
                tarefas.append(callback(evento))
        
        if tarefas:
            try:
                # Executa todos os agentes inscritos em paralelo
                await asyncio.gather(*tarefas)
            except Exception as e:
                # Apenas logamos a falha. O sistema não tenta chamar evento.erro()
                print(f"[Kernel] Erro catastrófico ao processar evento {evento.id}: {e}")

    # ----------------------------------------------------
    # Utilidades
    # ----------------------------------------------------

    def estatisticas(self):

        return {

            "fila": self._fila.qsize(),

            "recebidos": self.eventos_recebidos,

            "processados": self.eventos_processados,

            "listeners_registrados": len(self._listeners),
        }


kernel = KernelCognitivo()