from sqlalchemy import create_engine
from app.db.models import Base
from app.core.config import settings

def create_tables():
    """Create all database tables"""
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine
