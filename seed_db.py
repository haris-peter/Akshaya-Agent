import asyncio
import json
from app.db.session import async_session, engine
from app.db.models import Citizen, Employee, Requirement
from sqlalchemy import select

citizens_data = [
    {
        "aadhar_number": "123456789012",
        "name": "Priya Nair",
        "phone": "9876543210",
        "email": "priya.nair@example.com",
        "address": "14, MG Road, Trivandrum",
        "district": "Trivandrum"
    },
    {
        "aadhar_number": "987654321098",
        "name": "Rajan Menon",
        "phone": "9123456789",
        "email": "rajan.menon@example.com",
        "address": "22, Beach Road, Kollam",
        "district": "Kollam"
    }
]

employees_data = [
    {
        "employee_code": "EMP001",
        "name": "Anitha Krishnan",
        "phone": "9000000001",
        "email": "anitha.k@gov.in",
        "department": "Revenue",
        "position": "Senior Officer",
        "address": "Secretariat, Trivandrum",
        "is_active": True
    },
    {
        "employee_code": "EMP002",
        "name": "Shaiju Thomas",
        "phone": "9000000002",
        "email": "shaiju.t@gov.in",
        "department": "Health",
        "position": "Document Verifier",
        "address": "DHS Office, Ernakulam",
        "is_active": True
    }
]

requirements_data = [
    {
        "name": "Aadhar Card",
        "doc_type": "identity",
        "ocr_mode": "tesseract",
        "description": "UIDAI Aadhar card for identity verification",
        "is_mandatory": True
    },
    {
        "name": "Building Blueprint",
        "doc_type": "blueprint",
        "ocr_mode": "llm_vision",
        "description": "Architectural blueprint for building permit. AI will extract dimensions and structural details.",
        "is_mandatory": True
    },
    {
        "name": "Income Certificate",
        "doc_type": "income",
        "ocr_mode": "tesseract",
        "description": "Income certificate issued by Tahsildar",
        "is_mandatory": False
    },
    {
        "name": "Medical Certificate",
        "doc_type": "medical",
        "ocr_mode": "llm_vision",
        "description": "Doctor-issued medical certificate",
        "is_mandatory": False
    }
]

async def seed():
    async with async_session() as db:
        # Citizens
        existing = await db.execute(select(Citizen))
        if not existing.scalars().first():
            for c in citizens_data:
                db.add(Citizen(**c))
            print(f"Seeded {len(citizens_data)} citizens.")
        else:
            print("Citizens already seeded.")

        # Employees
        existing_emp = await db.execute(select(Employee))
        if not existing_emp.scalars().first():
            for e in employees_data:
                db.add(Employee(**e))
            print(f"Seeded {len(employees_data)} employees.")
        else:
            print("Employees already seeded.")

        # Requirements
        existing_req = await db.execute(select(Requirement))
        if not existing_req.scalars().first():
            for r in requirements_data:
                db.add(Requirement(**r))
            print(f"Seeded {len(requirements_data)} requirements.")
        else:
            print("Requirements already seeded.")

        await db.commit()
    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
