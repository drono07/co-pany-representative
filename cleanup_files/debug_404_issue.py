#!/usr/bin/env python3
"""
Debug the 404 issue with source code API
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import DatabaseManager

async def debug_404_issue():
    """Debug the 404 issue with source code API"""
    
    print("🔍 Debugging 404 Issue with Source Code API")
    print("=" * 50)
    
    # Use the run ID that's failing
    run_id = "68c040b41740fadabcea71a9"
    failing_url = "https://thegoodbug.com/pages/blockbuster-sale"
    
    print(f"📋 Run ID: {run_id}")
    print(f"🔗 Failing URL: {failing_url}")
    
    db = DatabaseManager()
    await db.connect()
    
    # Check if the run exists
    print(f"\n1️⃣ Checking if run exists...")
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        print("❌ Run not found")
        return
    print(f"✅ Run exists: {run.get('status', 'Unknown')}")
    
    # Check if source code exists for this specific URL
    print(f"\n2️⃣ Checking if source code exists for the failing URL...")
    source_data = await db.get_page_source_code(run_id, failing_url)
    if source_data:
        print(f"✅ Source code found in database!")
        print(f"   Content length: {len(source_data.get('source_code', ''))}")
        print(f"   Page URL: {source_data.get('page_url', 'Unknown')}")
        print(f"   Parent URL: {source_data.get('parent_url', 'None')}")
    else:
        print(f"❌ Source code NOT found in database for this URL")
        
        # Check what source codes do exist
        print(f"\n3️⃣ Checking what source codes exist for this run...")
        all_sources = await db.db.page_source_codes.find({"run_id": run_id}).to_list(10)
        print(f"   Total source codes: {len(all_sources)}")
        
        if all_sources:
            print(f"   Available URLs:")
            for i, source in enumerate(all_sources[:5]):
                print(f"     {i+1}. {source.get('page_url', 'Unknown')}")
        
        # Check if the URL exists with slight variations
        print(f"\n4️⃣ Checking for URL variations...")
        variations = [
            failing_url,
            failing_url + "/",
            failing_url.replace("https://", "http://"),
            failing_url.replace("www.", ""),
            failing_url.replace("thegoodbug.com", "www.thegoodbug.com")
        ]
        
        for variation in variations:
            source_data = await db.get_page_source_code(run_id, variation)
            if source_data:
                print(f"✅ Found with variation: {variation}")
                break
        else:
            print(f"❌ No variations found")
    
    # Check the API endpoint logic
    print(f"\n5️⃣ Checking API endpoint logic...")
    
    # Simulate what the API endpoint does
    try:
        # Check if run belongs to user (this would be the first check)
        print(f"   Step 1: Run exists ✅")
        
        # Check if source code exists
        source_data = await db.get_page_source_code(run_id, failing_url)
        if source_data:
            print(f"   Step 2: Source code exists ✅")
            print(f"   Step 3: Should return 200 OK ✅")
        else:
            print(f"   Step 2: Source code NOT found ❌")
            print(f"   Step 3: API returns 404 Not Found ❌")
            
            # This is the issue - the source code doesn't exist for this specific URL
            print(f"\n💡 ISSUE FOUND: The source code doesn't exist for this specific URL")
            print(f"   The frontend is trying to get source code for a URL that wasn't crawled")
            print(f"   or the URL format doesn't match what's stored in the database")
    
    except Exception as e:
        print(f"   ❌ Error in API logic: {e}")
    
    await db.disconnect()
    
    print(f"\n🎯 CONCLUSION:")
    print(f"   The 404 error means the source code doesn't exist for this specific URL")
    print(f"   This could be because:")
    print(f"   1. The URL wasn't crawled in this run")
    print(f"   2. The URL format doesn't match what's stored")
    print(f"   3. The frontend is requesting the wrong URL")

if __name__ == "__main__":
    asyncio.run(debug_404_issue())
