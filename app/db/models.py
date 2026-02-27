from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey, TIMESTAMP, func, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .database import Base

class Citizen(Base):
    __tablename__ = "citizen"

    citizen_id = Column(String(50), primary_key=True)
    aadhar_number = Column(String(12), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    district = Column(String(50), nullable=False)
    annual_income = Column(Integer, nullable=False)

    documents = relationship("DocumentVault", back_populates="citizen")
    applications = relationship("Application", back_populates="citizen")

class Scheme(Base):
    __tablename__ = "scheme"

    scheme_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    income_limit = Column(Integer, nullable=True)
    district_required = Column(Boolean, default=False)

    applications = relationship("Application", back_populates="scheme")

class DocumentVault(Base):
    __tablename__ = "document_vault"

    id = Column(Integer, primary_key=True, autoincrement=True)
    citizen_id = Column(String(50), ForeignKey("citizen.citizen_id"))
    document_type = Column(String(100), nullable=False)
    issued_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    document_hash = Column(String(256), nullable=False)

    citizen = relationship("Citizen", back_populates="documents")

class Application(Base):
    __tablename__ = "application"

    application_id = Column(String(50), primary_key=True)
    citizen_id = Column(String(50), ForeignKey("citizen.citizen_id"))
    scheme_id = Column(String(50), ForeignKey("scheme.scheme_id"))
    status = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    citizen = relationship("Citizen", back_populates="applications")
    scheme = relationship("Scheme", back_populates="applications")

class PolicyDocument(Base):
    """
    RAG Vector Store Model for Policy Snippets
    """
    __tablename__ = "policy_document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(String(50), ForeignKey("scheme.scheme_id"), nullable=True)
    content = Column(Text, nullable=False)
    # Using a 384-dimensional vector assuming all-MiniLM-L6-v2 embedding model
    embedding = Column(Vector(384))
    metadata_json = Column(String(500), nullable=True)

class DocumentUpload(Base):
    __tablename__ = "document_upload"

    upload_id = Column(String(50), primary_key=True)
    citizen_id = Column(String(50), ForeignKey("citizen.citizen_id"))
    s3_key = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, failed
    ocr_text = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    citizen = relationship("Citizen")

