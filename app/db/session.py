from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base
from app.core.config import settings

# For async postgres connections we use asyncpg
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# Generate an AsyncSession creator
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Initializes standard SQL tables based off SQLAlchemy metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency injector for getting an active async transactional session."""
    async with async_session() as session:
        yield session
