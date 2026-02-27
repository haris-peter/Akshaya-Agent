from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import router as citizen_router
from app.api.documents import router as document_router
from app.departments.routes import router as department_router
from app.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Execute database table creation
    await init_db()
    yield
    # Any teardown logic goes here

app = FastAPI(
    title="SaarthiAI Core API",
    description="Autonomous Government Scheme Orchestration System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the citizen-facing routes
app.include_router(citizen_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1/documents", tags=["documents"])

# Connect the simulated department service routes
app.include_router(department_router, prefix="/api/v1/departments")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "SaarthiAI"}
