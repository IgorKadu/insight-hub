"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# Global variables for lazy initialization
engine = None
SessionLocal = None
Base = declarative_base()

def initialize_database():
    """Initialize database connection lazily"""
    global engine, SessionLocal
    
    if engine is not None:
        return True
    
    if not DATABASE_URL:
        return False
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        return True
    except Exception:
        return False

def get_db_session():
    """Get database session"""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise

def close_db_session(session):
    """Close database session safely"""
    if session:
        session.close()