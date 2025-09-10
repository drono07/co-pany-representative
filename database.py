"""
MongoDB database connection and schema for website analysis
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

class WebsiteAnalysisDB:
    """MongoDB database operations for website analysis"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI", 
            "mongodb://localhost:27017/website_analysis"
        )
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client.website_analysis
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Indexes for crawl_sessions collection
            await self.db.crawl_sessions.create_index([("website_url", ASCENDING), ("created_at", DESCENDING)])
            await self.db.crawl_sessions.create_index("session_id", unique=True)
            
            # Indexes for pages collection
            await self.db.pages.create_index([("session_id", ASCENDING), ("url", ASCENDING)])
            await self.db.pages.create_index("url")
            await self.db.pages.create_index("parent_url")
            
            # Indexes for change_detection collection
            await self.db.change_detection.create_index([("website_url", ASCENDING), ("detected_at", DESCENDING)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def save_crawl_session(self, session_data: Dict[str, Any]) -> str:
        """Save a new crawl session"""
        try:
            result = await self.db.crawl_sessions.insert_one(session_data)
            logger.info(f"Crawl session saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save crawl session: {e}")
            raise
    
    async def save_page_data(self, page_data: Dict[str, Any]) -> str:
        """Save page data with HTML structure"""
        try:
            result = await self.db.pages.insert_one(page_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save page data: {e}")
            raise
    
    async def get_previous_crawl_session(self, website_url: str) -> Optional[Dict[str, Any]]:
        """Get the most recent crawl session for a website"""
        try:
            session = await self.db.crawl_sessions.find_one(
                {"website_url": website_url},
                sort=[("created_at", DESCENDING)]
            )
            return session
        except Exception as e:
            logger.error(f"Failed to get previous crawl session: {e}")
            return None
    
    async def get_pages_from_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all pages from a specific crawl session"""
        try:
            cursor = self.db.pages.find({"session_id": session_id})
            pages = await cursor.to_list(length=None)
            return pages
        except Exception as e:
            logger.error(f"Failed to get pages from session: {e}")
            return []
    
    async def save_change_detection(self, change_data: Dict[str, Any]) -> str:
        """Save change detection results"""
        try:
            result = await self.db.change_detection.insert_one(change_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save change detection: {e}")
            raise
    
    async def get_website_history(self, website_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get crawl history for a website"""
        try:
            cursor = self.db.crawl_sessions.find(
                {"website_url": website_url},
                sort=[("created_at", DESCENDING)]
            ).limit(limit)
            sessions = await cursor.to_list(length=None)
            return sessions
        except Exception as e:
            logger.error(f"Failed to get website history: {e}")
            return []

# Global database instance
db_instance = WebsiteAnalysisDB()

async def get_database():
    """Get database instance"""
    if not db_instance.client:
        await db_instance.connect()
    return db_instance
