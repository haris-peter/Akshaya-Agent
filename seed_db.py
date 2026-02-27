import asyncio
import sys
from datetime import date

sys.path.append('.')
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, init_db
from app.db.models import Citizen, Scheme, DocumentVault

async def seed_database():
    print("Initializing database tables...")
    await init_db()

    print("Seeding database...")
    async with AsyncSession(engine) as session:
        # 1. Create a mock scheme
        scheme = Scheme(
            scheme_id="GHS2024",
            name="Global Health Scheme",
            income_limit=500000,
            district_required=False
        )
        session.add(scheme)

        # 2. Create a mock citizen
        citizen = Citizen(
            citizen_id="C12345",
            aadhar_number="123456789012",
            name="Rahul Sharma",
            dob=date(1990, 5, 15),
            district="Kollam",
            annual_income=450000
        )
        session.add(citizen)

        # 3. Add a mock document to the vault (Aadhar Card)
        vault_doc = DocumentVault(
            citizen_id="C12345",
            document_type="Aadhar Card",
            issued_date=date(2015, 1, 1),
            valid_until=date(2099, 12, 31),
            document_hash="mock_hash_123"
        )
        session.add(vault_doc)

        try:
            await session.commit()
            print("Successfully seeded database with mock Scheme, Citizen, and DocumentVault data.")
        except Exception as e:
            print(f"Error seeding database (might already exist): {e}")
            await session.rollback()

if __name__ == '__main__':
    asyncio.run(seed_database())
