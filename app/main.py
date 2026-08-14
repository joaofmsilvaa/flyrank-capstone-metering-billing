from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import engine, Base
from app.core.config import settings
from app.api.routers import meter, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.include_router(meter.router)
app.include_router(webhooks.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}