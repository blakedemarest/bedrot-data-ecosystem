"""Main FastAPI application for BEDROT Data Dashboard."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from backend.api.routers import revenue, streaming, kpis, data
from backend.utils.context_loader import get_context_var

# Configure logger
logger.add("logs/dashboard_{time}.log", rotation="1 day", retention="7 days")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting BEDROT Data Dashboard Backend...")
    yield
    logger.info("Shutting down BEDROT Data Dashboard Backend...")

# Create FastAPI app
app = FastAPI(
    title="BEDROT Data Dashboard API",
    description="Real-time analytics API for music streaming and revenue data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(revenue.router, prefix="/api/revenue", tags=["Revenue"])
app.include_router(streaming.router, prefix="/api/streaming", tags=["Streaming"])
app.include_router(kpis.router, prefix="/api/kpis", tags=["KPIs"])
app.include_router(data.router, prefix="/api/data", tags=["Data"])

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BEDROT Data Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "revenue": "/api/revenue",
            "streaming": "/api/streaming",
            "kpis": "/api/kpis",
            "data": "/api/data",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dashboard-backend"
    }

if __name__ == "__main__":
    import uvicorn
    
    host = get_context_var("BACKEND_HOST", "0.0.0.0")
    port = int(get_context_var("BACKEND_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )