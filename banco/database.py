from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Alterado para engine assíncrona com aiosqlite para não bloquear a CPU
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./agente_local.db"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False # Mude para True se precisar debugar queries geradas pelos agentes
)

# Fábrica de Sessões assíncronas
AsyncSessionLocal = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False
)

async def obter_sessao_banco():
    """Dependency injection ou context manager para os agentes operarem no banco assincronamente."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            
            
async def inicializar_banco():
    """
    Constrói a estrutura do banco de dados assíncrono caso ela não exista.
    Importação tardia (lazy import) de Base para evitar dependência circular.
    """
    from banco.models import Base
    async with async_engine.begin() as conn:
        # run_sync é usado para executar a rotina síncrona de DDL do SQLAlchemy
        # sem bloquear o Event Loop.
        await conn.run_sync(Base.metadata.create_all)