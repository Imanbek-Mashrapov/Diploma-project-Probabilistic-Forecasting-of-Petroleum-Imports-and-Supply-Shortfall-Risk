"""SQLAlchemy engine from DATABASE_URL."""
import os

from sqlalchemy import create_engine


def get_engine(url=None):
    url = url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set; see .env.example")
    return create_engine(url)
