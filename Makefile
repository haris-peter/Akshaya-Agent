.PHONY: server ui all db-sync db-seed ingest

# Starts the FastAPI backend server
server:
	.\env\Scripts\python.exe -m uvicorn main:app --port 8000 --reload

# Starts the Streamlit frontend application
ui:
	.\env\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501

# Starts both the backend server and frontend application in separate windows (Windows specific)
all:
	start "FastAPI Server" cmd /c ".\env\Scripts\python.exe -m uvicorn main:app --port 8000 --reload"
	start "Streamlit UI" cmd /c ".\env\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501"

# Creates all database tables
db-sync:
	.\env\Scripts\python.exe -c "import asyncio; from app.db.session import init_db; asyncio.run(init_db())"

# Seeds the database with default data
db-seed:
	.\env\Scripts\python.exe seed_db.py

# Ingests policy documents for RAG
ingest:
	.\env\Scripts\python.exe ingest_policies.py
