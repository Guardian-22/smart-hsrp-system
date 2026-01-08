from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from config.settings import settings

# Load DB URL from settings
DB_URL = settings.DATABASE_URL  # fallback to SQLite

# Create engine
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
