from fastapi import APIRouter
from app.api.v1 import questions, sessions, predict, ingest, train, analytics

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(predict.router, prefix="/predict", tags=["prediction"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(train.router, prefix="/train", tags=["training"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
