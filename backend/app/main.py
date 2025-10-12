from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.base import create_tables
from app.db.seed import init_database

# Initialize database
create_tables()
init_database()

app = FastAPI(
    title="DSS Miscalibration Prediction System",
    description="A Decision Support System for predicting miscalibration in learning environments",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "DSS Miscalibration Prediction System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
