from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

# We are using sqlite to bypass the IPv4 limitations on the Supabase free tier connection pooler.
SQLLITE_URL = "sqlite+aiosqlite:///./saarthi_local.db"

engine = create_async_engine(SQLLITE_URL, echo=False, future=True)

# Generate an AsyncSession creator
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Initializes standard SQL tables based off SQLModel metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency injector for getting an active async transactional session."""
    async with async_session() as session:
        yield session
