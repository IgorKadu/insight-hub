"""
Database connection and session management
"""
import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DisconnectionError, OperationalError

# Database connection URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# Global variables for lazy initialization
engine = None
SessionLocal = None
Base = declarative_base()

def initialize_database():
    """Initialize database connection lazily with robust SSL handling"""
    global engine, SessionLocal
    
    if engine is not None:
        try:
            # Test existing connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except (DisconnectionError, OperationalError):
            # Force recreation of engine
            engine = None
    
    if not DATABASE_URL:
        return False
    
    try:
        # Create engine with robust SSL and pool settings
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Validates connections before use
            pool_recycle=300,    # Recycle connections every 5 minutes
            connect_args={
                "sslmode": "require",
                "connect_timeout": 10,
                "application_name": "insight_hub_fleet_monitor"
            }
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        return True
    except Exception:
        return False

def get_db_session():
    """Get database session with retry logic"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        session = None
        try:
            # Ensure database is initialized
            if not initialize_database():
                raise Exception("Failed to initialize database")
            
            session = SessionLocal()
            
            # Test the connection
            session.execute(text("SELECT 1"))
            return session
            
        except (DisconnectionError, OperationalError) as e:
            if session:
                session.close()
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
                # Force engine recreation on connection errors
                global engine
                engine = None
                continue
            else:
                raise e
        except Exception as e:
            if session:
                session.close()
            raise e

def close_db_session(session):
    """Close database session safely"""
    if session:
        try:
            session.close()
        except Exception:
            pass  # Ignore errors when closing

def test_connection():
    """Test database connection health"""
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False