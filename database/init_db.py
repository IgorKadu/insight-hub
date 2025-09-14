"""
Initialize database schema and create all tables
"""
from database.connection import engine, Base
from database.models import (
    Client, Vehicle, TelematicsData, ProcessingHistory, 
    InsightData, AlertConfiguration
)

def create_all_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

def drop_all_tables():
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ Database tables dropped successfully!")
        return True
    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
        return False

if __name__ == "__main__":
    create_all_tables()