"""Database configuration and connection setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas import Base
import os
from pathlib import Path

# Database configuration
DATABASE_URL = "sqlite:///./gstr1.db"

# Create database directory if it doesn't exist
db_path = Path("./gstr1.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables."""
    create_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
