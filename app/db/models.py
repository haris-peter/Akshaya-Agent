from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP, Text, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .database import Base


class Citizen(Base):
    __tablename__ = "citizen"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aadhar_number = Column(String(12), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    district = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    tracking_records = relationship("StatusTracking", back_populates="citizen")


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(50), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    address = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    tracking_records = relationship("StatusTracking", back_populates="employee")


class DocumentType(Base):
    __tablename__ = "document_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    requirements = relationship("Requirement", back_populates="doc_type", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_type_id = Column(Integer, ForeignKey("document_type.id"), nullable=False)
    name = Column(String(100), nullable=False)
    ocr_mode = Column(String(20), default="tesseract")
    is_mandatory = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    doc_type = relationship("DocumentType", back_populates="requirements")
    documents = relationship("Document", back_populates="requirement")


class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("requirement.id"), nullable=False)
    document_name = Column(String(100), nullable=False)
    job_id = Column(String(100), unique=True, nullable=True)
    file_url = Column(String(500), nullable=True)
    status = Column(String(20), default="processing")
    ocr_summary = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    citizen = relationship("Citizen")
    requirement = relationship("Requirement", back_populates="documents")


class StatusTracking(Base):
    __tablename__ = "status_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=True)
    document_request_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    remarks = Column(Text, nullable=True)
    vault_summary = Column(Text, nullable=True)
    compliance_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    citizen = relationship("Citizen", back_populates="tracking_records")
    employee = relationship("Employee", back_populates="tracking_records")


class PolicyDocument(Base):
    __tablename__ = "policy_document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))
    metadata_json = Column(String(500), nullable=True)

class DocumentUpload(Base):
    __tablename__ = "document_upload"

    upload_id = Column(String(50), primary_key=True)
    citizen_id = Column(Integer, ForeignKey("citizen.id"), nullable=True)
    s3_key = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, failed
    ocr_text = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    citizen = relationship("Citizen")

