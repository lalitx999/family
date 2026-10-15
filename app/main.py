import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.health import router as health_router
from app.api.v1.webhook import router as webhook_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("family_butler")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Auto-create DB tables if they don't exist
    logger.info("Starting up Family AI Butler... Initializing database tables.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down Family AI Butler...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Family AI Butler: Personal PM, Anti-Procrastination & Household Finance Assistant",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(webhook_router, prefix="/api/v1/webhook", tags=["Webhook"])


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }
