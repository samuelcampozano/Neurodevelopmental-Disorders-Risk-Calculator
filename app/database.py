"""
Database configuration and connection setup for the Neurodevelopmental Disorders Risk Calculator.
Updated to support both PostgreSQL (production) and SQLite (development).
"""

import os
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL configuration
# Prioritize PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL")

# If no DATABASE_URL is set, construct it from individual components
if not DATABASE_URL:
    # Try to construct PostgreSQL URL from components
    if os.getenv("POSTGRES_HOST"):
        DATABASE_URL = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'ndd_user')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'ndd_calculator')}"
        )
    else:
        # Fall back to SQLite for development
        DATABASE_URL = "sqlite:///./data/ndd_calculator.db"
        print("⚠️  No PostgreSQL configuration found, using SQLite for development")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=300,    # Recycle connections after 5 minutes
        pool_size=10,        # Number of connections to maintain
        max_overflow=20,     # Maximum overflow connections
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )
else:
    raise ValueError(f"Unsupported database URL: {DATABASE_URL}")

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db():
    """
    Dependency function to get database session.
    Used with FastAPI's Depends() for dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database.
    This function should be called on application startup.
    """
    # Import all models to ensure they're registered
    from app.models.evaluacion import Evaluacion
    
    # Ensure data directory exists (for SQLite)
    if DATABASE_URL.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database tables created successfully!")
    print(f"📍 Using database: {engine.url.render_as_string(hide_password=True)}")

def get_db_info():
    """
    Get database connection information for debugging.
    """
    return {
        "database_url": engine.url.render_as_string(hide_password=True),
        "engine": str(engine.url.drivername),
        "dialect": engine.dialect.name,
        "pool_size": getattr(engine.pool, 'size', 'N/A'),
        "is_sqlite": DATABASE_URL.startswith("sqlite"),
        "is_postgresql": DATABASE_URL.startswith("postgresql")
    }

def test_connection():
    """
    Test database connection.
    Returns True if successful, raises exception otherwise.
    """
    try:
        with engine.connect() as conn:
            # Simple query to test connection
            result = conn.execute("SELECT 1")
            result.fetchone()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        raise

def init_database():
    """
    Initialize database with required extensions (PostgreSQL only).
    Call this before create_tables() for PostgreSQL.
    """
    if DATABASE_URL.startswith("postgresql"):
        try:
            with engine.connect() as conn:
                # Create UUID extension if needed
                conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
                conn.commit()
            print("✅ PostgreSQL extensions initialized")
        except Exception as e:
            print(f"⚠️  Could not create extensions: {str(e)}")

# Run basic connection test on import
if __name__ == "__main__":
    print("Testing database connection...")
    test_connection()
    print("\nDatabase info:")
    for key, value in get_db_info().items():
        print(f"  {key}: {value}")