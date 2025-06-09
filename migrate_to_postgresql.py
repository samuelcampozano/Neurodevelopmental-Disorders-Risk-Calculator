#!/usr/bin/env python3
"""
Script to migrate data from SQLite to PostgreSQL.
Run this after setting up PostgreSQL to transfer existing data.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import models
from app.models.evaluacion import Evaluacion
from app.database import Base

def migrate_sqlite_to_postgresql():
    """
    Migrate data from SQLite to PostgreSQL.
    """
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    print("=" * 60)
    
    # SQLite configuration
    sqlite_url = "sqlite:///./data/ndd_calculator.db"
    
    # PostgreSQL configuration from environment
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url or postgres_url.startswith("sqlite"):
        postgres_url = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'ndd_user')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'ndd_calculator')}"
        )
    
    print(f"📂 Source: {sqlite_url}")
    print(f"🎯 Target: {postgres_url.replace(os.getenv('POSTGRES_PASSWORD', ''), '***')}")
    
    try:
        # Create engines
        sqlite_engine = create_engine(sqlite_url)
        postgres_engine = create_engine(postgres_url)
        
        # Create sessions
        SqliteSession = sessionmaker(bind=sqlite_engine)
        PostgresSession = sessionmaker(bind=postgres_engine)
        
        sqlite_session = SqliteSession()
        postgres_session = PostgresSession()
        
        # Create tables in PostgreSQL
        print("\n📊 Creating tables in PostgreSQL...")
        Base.metadata.create_all(bind=postgres_engine)
        print("✅ Tables created successfully")
        
        # Check if SQLite database exists and has data
        try:
            evaluation_count = sqlite_session.query(Evaluacion).count()
            print(f"\n📊 Found {evaluation_count} evaluations in SQLite")
            
            if evaluation_count == 0:
                print("⚠️  No data to migrate")
                return
            
            # Migrate evaluations
            print("\n🚀 Migrating evaluations...")
            evaluations = sqlite_session.query(Evaluacion).all()
            
            migrated = 0
            for eval in evaluations:
                # Create new evaluation object
                new_eval = Evaluacion(
                    sexo=eval.sexo,
                    edad=eval.edad,
                    respuestas=eval.respuestas,
                    riesgo_estimado=eval.riesgo_estimado,
                    acepto_consentimiento=eval.acepto_consentimiento,
                    fecha=eval.fecha
                )
                
                postgres_session.add(new_eval)
                migrated += 1
                
                # Show progress
                if migrated % 10 == 0:
                    print(f"   Migrated {migrated}/{evaluation_count} evaluations...")
            
            # Commit changes
            postgres_session.commit()
            print(f"\n✅ Successfully migrated {migrated} evaluations")
            
            # Verify migration
            postgres_count = postgres_session.query(Evaluacion).count()
            print(f"\n🔍 Verification: {postgres_count} evaluations in PostgreSQL")
            
            if postgres_count == evaluation_count:
                print("✅ Migration completed successfully!")
            else:
                print(f"⚠️  Warning: Count mismatch - SQLite: {evaluation_count}, PostgreSQL: {postgres_count}")
            
        except Exception as e:
            print(f"\n❌ Error reading SQLite database: {str(e)}")
            print("💡 This might be normal if you haven't used SQLite yet")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        postgres_session.rollback()
        raise
    finally:
        # Close sessions
        sqlite_session.close()
        postgres_session.close()
        print("\n🔒 Database connections closed")

def verify_postgresql_setup():
    """
    Verify PostgreSQL is properly configured and accessible.
    """
    print("\n🔍 Verifying PostgreSQL setup...")
    
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url or postgres_url.startswith("sqlite"):
        postgres_url = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'ndd_user')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'ndd_calculator')}"
        )
    
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connected successfully!")
            print(f"📊 Version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("\n💡 Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. Database 'ndd_calculator' exists")
        print("   3. User credentials are correct in .env file")
        return False

if __name__ == "__main__":
    print("🧠 NDD Risk Calculator - Database Migration Tool")
    print("=" * 60)
    
    # First verify PostgreSQL is accessible
    if verify_postgresql_setup():
        # Ask user to confirm
        print("\n⚠️  This will migrate all data from SQLite to PostgreSQL")
        response = input("Do you want to continue? (yes/no): ")
        
        if response.lower() == 'yes':
            migrate_sqlite_to_postgresql()
        else:
            print("❌ Migration cancelled")
    else:
        print("\n❌ Please fix PostgreSQL connection before migrating")