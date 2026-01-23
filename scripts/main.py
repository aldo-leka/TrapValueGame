import os
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

# CORS - configure for production domain via ALLOWED_ORIGINS env var
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5000,http://localhost:5001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router, prefix="/game", tags=["Game"])

# Only include admin routes if seeding is enabled (disabled in production)
if os.getenv("DISABLE_SEEDING", "false").lower() != "true":
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "healthy"}
