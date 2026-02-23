from sqlalchemy import create_engine, text
from app.db.models import Base
from app.core.config import settings

def _sqlite_has_column(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return any(row[1] == column_name for row in rows)

def _apply_sqlite_compat_migrations(engine) -> None:
    """
    Lightweight additive migrations for local SQLite dev DB.
    Keeps existing databases compatible when new nullable columns are introduced.
    """
    if not str(settings.DATABASE_URL).startswith("sqlite"):
        return

    with engine.begin() as conn:
        if not _sqlite_has_column(conn, "users", "display_name"):
            conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(120)"))

        if not _sqlite_has_column(conn, "model_registry", "friendly_name"):
            conn.execute(text("ALTER TABLE model_registry ADD COLUMN friendly_name VARCHAR(120)"))

        if not _sqlite_has_column(conn, "model_registry", "is_active"):
            conn.execute(text("ALTER TABLE model_registry ADD COLUMN is_active BOOLEAN DEFAULT 1"))

        if not _sqlite_has_column(conn, "interactions", "initial_chosen_option"):
            conn.execute(text("ALTER TABLE interactions ADD COLUMN initial_chosen_option VARCHAR(50)"))

        if not _sqlite_has_column(conn, "interactions", "initial_confidence"):
            conn.execute(text("ALTER TABLE interactions ADD COLUMN initial_confidence FLOAT"))

        if not _sqlite_has_column(conn, "interactions", "reconsidered"):
            conn.execute(text("ALTER TABLE interactions ADD COLUMN reconsidered BOOLEAN DEFAULT 0"))

        if not _sqlite_has_column(conn, "interactions", "time_to_reconsider_ms"):
            conn.execute(text("ALTER TABLE interactions ADD COLUMN time_to_reconsider_ms INTEGER"))

def create_tables():
    """Create all database tables"""
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_compat_migrations(engine)
    return engine
