#!/usr/bin/env python3
"""
Check what analysis runs are available in the database
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import DatabaseManager

async def check_available_runs():
    """Check what analysis runs are available"""
    
    print("🔍 Checking Available Analysis Runs")
    print("=" * 50)
    
    db = DatabaseManager()
    await db.connect()
    
    # Get all runs
    runs_collection = db.db.analysis_runs
    all_runs = await runs_collection.find().sort("created_at", -1).to_list(10)
    
    print(f"📋 Found {len(all_runs)} analysis runs:")
    
    for i, run in enumerate(all_runs):
        run_id = str(run['_id'])
        created_at = run.get('created_at', 'Unknown')
        status = run.get('status', 'Unknown')
        website_url = run.get('website_url', 'Unknown')
        
        print(f"\n{i+1}. Run ID: {run_id}")
        print(f"   Created: {created_at}")
        print(f"   Status: {status}")
        print(f"   Website: {website_url}")
        
        # Check if this run has source codes
        source_count = await db.db.page_source_codes.count_documents({"run_id": run_id})
        print(f"   Source codes: {source_count}")
        
        # Check if this run has parent-child relationships
        relationships = await db.get_parent_child_relationships(run_id)
        if relationships:
            parent_count = len(relationships.get('parent_map', {}))
            print(f"   Parent relationships: {parent_count}")
        else:
            print(f"   Parent relationships: 0")
        
        # Check if this run has broken links
        link_validations = await db.get_link_validations(run_id)
        broken_count = len([link for link in link_validations if link.get('status_code', 200) >= 400])
        print(f"   Broken links: {broken_count}")
    
    await db.disconnect()
    
    print(f"\n💡 Use the run ID with the most data for testing!")

if __name__ == "__main__":
    asyncio.run(check_available_runs())
