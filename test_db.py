import asyncio
import sys

sys.path.append('.')
from app.db.session import init_db

async def test_conn():
    print('Testing connection...')
    try:
        await init_db()
        print('SUCCESS: Database connection established. Tables provisioned.')
    except Exception as e:
        print(f'ERROR: SQLAlchemy connection failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(test_conn())
