from __future__ import annotations
from sqlalchemy.future import select
from banco.database import AsyncSessionLocal
from banco.models import PerfilUsuarioDB

class MemoriaPerfil:
    """
    Responsável por gerenciar as estatísticas de hábitos, preferências 
    e scores normalizados do usuário de forma assíncrona.
    """

    async def incrementar_score(self, categoria: str, valor: str, incremento: int = 1) -> None:
        """
        Incrementa a frequência absoluta de um hábito e atualiza o timestamp.
        """
        async with AsyncSessionLocal() as session:
            stmt = select(PerfilUsuarioDB).where(
                PerfilUsuarioDB.categoria == categoria,
                PerfilUsuarioDB.valor == valor
            )
            resultado = await session.execute(stmt)
            registro = resultado.scalar_one_or_none()

            if registro:
                registro.score += incremento
                # A confiança pode ser recalculada aqui ou por um agente em background
            else:
                registro = PerfilUsuarioDB(
                    categoria=categoria,
                    valor=valor,
                    score=incremento,
                    confianca=0.1  # Confiança inicial arbitrária
                )
                session.add(registro)

            await session.commit()

    async def obter_perfil_categoria(self, categoria: str) -> list[dict]:
        """
        Retorna todos os registros de uma determinada categoria ordenados por relevância.
        """
        async with AsyncSessionLocal() as session:
            stmt = select(PerfilUsuarioDB).where(
                PerfilUsuarioDB.categoria == categoria
            ).order_by(PerfilUsuarioDB.score.desc())
            
            resultado = await session.execute(stmt)
            registros = resultado.scalars().all()
            
            return [
                {
                    "valor": r.valor,
                    "score": r.score,
                    "confianca": r.confianca
                } for r in registros
            ]