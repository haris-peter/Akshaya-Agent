from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date, datetime

class Citizen(SQLModel, table=True):
    citizen_id: str = Field(default=None, primary_key=True)
    aadhar_number: str = Field(unique=True, index=True)
    name: str
    dob: date
    district: str
    annual_income: int
    
    applications: List["Application"] = Relationship(back_populates="citizen")
    documents: List["DocumentVault"] = Relationship(back_populates="citizen")


class Scheme(SQLModel, table=True):
    scheme_id: str = Field(default=None, primary_key=True)
    name: str
    income_limit: Optional[int] = None
    district_required: bool = False
    
    applications: List["Application"] = Relationship(back_populates="scheme")


class DocumentVault(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    citizen_id: str = Field(foreign_key="citizen.citizen_id")
    document_type: str
    issued_date: date
    valid_until: date
    document_hash: str
    
    citizen: Citizen = Relationship(back_populates="documents")


class Application(SQLModel, table=True):
    application_id: str = Field(default=None, primary_key=True)
    citizen_id: str = Field(foreign_key="citizen.citizen_id")
    scheme_id: str = Field(foreign_key="scheme.scheme_id")
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    citizen: Citizen = Relationship(back_populates="applications")
    scheme: Scheme = Relationship(back_populates="applications")
