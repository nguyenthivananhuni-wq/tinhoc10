import os
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, create_engine

# ---------------------------------------------------------------------------
# Cấu hình DB:
#   - Production (Render): đặt biến môi trường DATABASE_URL trỏ tới Postgres.
#   - Local dev: không có DATABASE_URL → fallback về SQLite file data/app.db.
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app.db"

_RAW_URL = os.environ.get("DATABASE_URL", "").strip()


def _normalize_db_url(url: str) -> str:
    """Render cấp URL dạng `postgres://...`; SQLAlchemy 2.x cần `postgresql+psycopg2://`."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


if _RAW_URL:
    DATABASE_URL = _normalize_db_url(_RAW_URL)
    IS_SQLITE = False
else:
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    IS_SQLITE = True


if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # pool_pre_ping: Postgres free của Render đóng connection khi idle → ping trước khi dùng.
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )


@event.listens_for(Engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    # Chỉ áp dụng PRAGMA cho SQLite; Postgres bật foreign key mặc định.
    if not IS_SQLITE:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
