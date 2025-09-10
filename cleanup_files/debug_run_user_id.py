#!/usr/bin/env python3
"""
Debug the user_id field in the run document
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import DatabaseManager

async def debug_run_user_id():
    """Debug the user_id field in the run document"""
    
    print("🔍 Debugging Run User ID Field")
    print("=" * 50)
    
    # Use the run ID that's failing
    run_id = "68c03b5c28928e715251b910"
    
    db = DatabaseManager()
    await db.connect()
    
    print(f"📋 Run ID: {run_id}")
    
    # Get the raw run document
    print(f"\n1️⃣ Getting raw run document...")
    run = await db.db.analysis_runs.find_one({"_id": ObjectId(run_id)})
    if not run:
        print("❌ Run not found")
        return
    
    print(f"✅ Run found!")
    print(f"   Run fields: {list(run.keys())}")
    print(f"   user_id field: {run.get('user_id', 'NOT_FOUND')}")
    print(f"   user_id type: {type(run.get('user_id', None))}")
    print(f"   application_id: {run.get('application_id', 'NOT_FOUND')}")
    
    # Check if there's an application_id and get the application
    if run.get('application_id'):
        print(f"\n2️⃣ Checking application...")
        app_id = run.get('application_id')
        app = await db.db.applications.find_one({"_id": ObjectId(app_id)})
        if app:
            print(f"   Application found!")
            print(f"   App user_id: {app.get('user_id', 'NOT_FOUND')}")
            print(f"   App user_id type: {type(app.get('user_id', None))}")
        else:
            print(f"   ❌ Application not found")
    
    # Check what users exist
    print(f"\n3️⃣ Checking users in database...")
    users = await db.db.users.find().to_list(5)
    print(f"   Total users: {len(users)}")
    
    if users:
        print(f"   Sample users:")
        for i, user in enumerate(users[:3]):
            print(f"     {i+1}. ID: {user.get('_id')}, Email: {user.get('email', 'Unknown')}")
    
    await db.disconnect()
    
    print(f"\n💡 The issue might be:")
    print(f"   1. Run doesn't have user_id field")
    print(f"   2. user_id field has wrong format")
    print(f"   3. Authentication is not working")

if __name__ == "__main__":
    from bson import ObjectId
    asyncio.run(debug_run_user_id())
