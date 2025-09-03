#!/usr/bin/env python3
"""Script to create the simplified database with user authentication support."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import engine, Base
from schemas.simplified_schemas import UserDB, GSTR1ReturnDB

def create_simplified_database():
    """Create simplified database tables."""
    print("Creating simplified database tables...")
    
    # Drop existing tables if they exist
    Base.metadata.drop_all(bind=engine)
    
    # Create new tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Simplified database tables created successfully!")
    print(f"Database file: {engine.url}")
    
    # List all created tables
    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    create_simplified_database()
