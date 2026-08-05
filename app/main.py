from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import engine, Base
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria todas as tabelas no startup (em produção seria via migrations/Alembic)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}