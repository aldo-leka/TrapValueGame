from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import game_router, admin_router
from services.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Trap Or Value API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:5001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router, prefix="/game", tags=["Game"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "healthy"}
