from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy import delete
from banco.database import AsyncSessionLocal
from banco.models import MemoriaTrabalhoDB

# A relevância de uma conversa decai 1.0 ponto a cada 24 horas.
# Uma conversa com relevância 7.0 será esquecida em 7 dias se não houver interação.
DECAY_RATE_PER_HOUR = 1.0 / 24.0

class MemoriaDeTrabalho:

    async def atualizar_conversa(self, chave_conversa: str, nova_mensagem: str, incremento_relevancia: float = 1.0):
        """
        Atualiza uma conversa na memória de trabalho, adicionando uma nova mensagem
        e aumentando sua relevância.
        """
        async with AsyncSessionLocal() as session:
            stmt = select(MemoriaTrabalhoDB).where(MemoriaTrabalhoDB.chave_conversa == chave_conversa)
            resultado = await session.execute(stmt)
            conversa = resultado.scalars().first()

            now = datetime.now(timezone.utc)

            if conversa:
                # Conversa existente: atualiza
                contexto_atual = conversa.resumo_contexto if isinstance(conversa.resumo_contexto, list) else []
                contexto_atual.append(nova_mensagem)
                # Mantém apenas as últimas 10 mensagens para não sobrecarregar
                conversa.resumo_contexto = contexto_atual[-10:]
                
                conversa.relevancia += incremento_relevancia
                conversa.ultima_interacao = now
            else:
                # Nova conversa: cria
                conversa = MemoriaTrabalhoDB(
                    chave_conversa=chave_conversa,
                    resumo_contexto=[nova_mensagem],
                    relevancia=incremento_relevancia,
                    ultima_interacao=now
                )
                session.add(conversa)
            
            await session.commit()

    async def esquecer_conversas_irrelevantes(self) -> int:
        """
        Implementa a mecânica de esquecimento.
        Calcula um 'score de sobrevivência' para cada conversa e remove as que
        caem abaixo de zero. Retorna o número de conversas esquecidas.
        """
        async with AsyncSessionLocal() as session:
            agora = datetime.now(timezone.utc)
            
            # Subquery para encontrar IDs a serem deletados
            expired_conversations_stmt = select(MemoriaTrabalhoDB.id).where(
                (MemoriaTrabalhoDB.relevancia - (( (julianday(agora) - julianday(MemoriaTrabalhoDB.ultima_interacao)) * 24) * DECAY_RATE_PER_HOUR)) < 0
            )
            
            delete_stmt = delete(MemoriaTrabalhoDB).where(MemoriaTrabalhoDB.id.in_(expired_conversations_stmt.scalar_subquery()))
            result = await session.execute(delete_stmt)
            await session.commit()
            
            return result.rowcount

memoria_trabalho = MemoriaDeTrabalho()