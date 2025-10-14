#!/usr/bin/env python3
"""
MongoDB setup script for website analysis
"""

import asyncio
import os
from database_schema import get_database

async def setup_mongodb():
    """Setup MongoDB database and collections"""
    print("Setting up MongoDB for website analysis...")
    
    try:
        # Connect to database
        db = await get_database()
        
        # Test connection
        print("✅ Connected to MongoDB successfully")
        
        # Create indexes (this is done automatically in the database class)
        print("✅ Database indexes created")
        
        # Test collections
        collections = await db.db.list_collection_names()
        print(f"✅ Available collections: {collections}")
        
        print("\n🎉 MongoDB setup completed successfully!")
        print("\nYou can now run the enhanced website analysis with:")
        print("python main_with_mongodb.py <website_url> --depth 1")
        
    except Exception as e:
        print(f"❌ MongoDB setup failed: {e}")
        print("\nPlease ensure MongoDB is running:")
        print("1. Install MongoDB: https://docs.mongodb.com/manual/installation/")
        print("2. Start MongoDB service")
        print("3. Or use MongoDB Atlas (cloud) and update MONGODB_URI in .env")

if __name__ == "__main__":
    asyncio.run(setup_mongodb())
