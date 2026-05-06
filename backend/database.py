from contextlib import contextmanager

from sqlalchemy import inspect, text
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import config

DATABASE_URL = config.SQLALCHEMY_DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    apply_lightweight_migrations()


def apply_lightweight_migrations():
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "expenses" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("expenses")}
        with engine.begin() as connection:
            if "source" not in columns:
                connection.execute(text("ALTER TABLE expenses ADD COLUMN source VARCHAR DEFAULT 'telegram' NOT NULL"))
            if "created_at" not in columns:
                connection.execute(text("ALTER TABLE expenses ADD COLUMN created_at DATETIME"))


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
