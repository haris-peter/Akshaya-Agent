# `/docs/DATA_MODEL_SPEC.md`

## 1. Core Entities

### 1.1 Citizen
```sql
CREATE TABLE citizen (
    citizen_id VARCHAR(50) PRIMARY KEY,
    aadhar_number VARCHAR(12) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    district VARCHAR(50) NOT NULL,
    annual_income INTEGER NOT NULL
);
```

### 1.2 Scheme
```sql
CREATE TABLE scheme (
    scheme_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    income_limit INTEGER,
    district_required BOOLEAN DEFAULT FALSE
);
```

### 1.3 Document Vault
```sql
CREATE TABLE document_vault (
    id SERIAL PRIMARY KEY,
    citizen_id VARCHAR(50) REFERENCES citizen(citizen_id),
    document_type VARCHAR(100) NOT NULL,
    issued_date DATE NOT NULL,
    valid_until DATE NOT NULL,
    document_hash VARCHAR(256) NOT NULL
);
```

### 1.4 Application
```sql
CREATE TABLE application (
    application_id VARCHAR(50) PRIMARY KEY,
    citizen_id VARCHAR(50) REFERENCES citizen(citizen_id),
    scheme_id VARCHAR(50) REFERENCES scheme(scheme_id),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.5 Department Records
Separate simulated datastores for:
- IncomeRecords
- CasteRecords
- TaxRecords
- LandOwnership

## 2. Responsibilities
- Maintain referential integrity
- Enforce constraints
- Support audit logging

Business logic must not be embedded inside database models.
