"""
Database schema for FastAPI website analysis platform
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel
from bson import ObjectId
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def convert_objectid_to_str(obj):
    """Convert ObjectId fields to strings recursively"""
    if isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

class DatabaseManager:
    """Manages database connections and schema"""
    
    def __init__(self, connection_string: str = None):
        import os
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI", 
            "mongodb://localhost:27017/website_analysis_platform"
        )
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            # Create client with connection pooling and better settings
            self.client = AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000
            )
            self.db = self.client.website_analysis_platform
            
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
            # Users collection indexes
            await self.db.users.create_indexes([
                IndexModel([("email", ASCENDING)], unique=True),
                IndexModel([("created_at", DESCENDING)])
            ])
            
            # Applications collection indexes
            await self.db.applications.create_indexes([
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("website_url", ASCENDING)]),
                IndexModel([("is_active", ASCENDING)])
            ])
            
            # Schedules collection indexes
            await self.db.schedules.create_indexes([
                IndexModel([("application_id", ASCENDING)]),
                IndexModel([("is_active", ASCENDING), ("next_run", ASCENDING)]),
                IndexModel([("frequency", ASCENDING)])
            ])
            
            # Analysis runs collection indexes
            await self.db.analysis_runs.create_indexes([
                IndexModel([("application_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("started_at", DESCENDING)])
            ])
            
            # Analysis results collection indexes
            await self.db.analysis_results.create_indexes([
                IndexModel([("run_id", ASCENDING)]),
                IndexModel([("page_url", ASCENDING)]),
                IndexModel([("page_type", ASCENDING)]),
                IndexModel([("crawled_at", DESCENDING)])
            ])
            
            # Link validations collection indexes
            await self.db.link_validations.create_indexes([
                IndexModel([("run_id", ASCENDING)]),
                IndexModel([("url", ASCENDING)]),
                IndexModel([("status", ASCENDING)])
            ])
            
            # Change detections collection indexes
            await self.db.change_detections.create_indexes([
                IndexModel([("run_id", ASCENDING)]),
                IndexModel([("previous_run_id", ASCENDING)])
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    # User operations
    async def create_user(self, user_data: dict) -> str:
        """Create a new user"""
        result = await self.db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        return await self.db.users.find_one({"email": email})
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        return await self.db.users.find_one({"_id": user_id})
    
    # Application operations
    async def create_application(self, app_data: dict) -> str:
        """Create a new application"""
        result = await self.db.applications.insert_one(app_data)
        return str(result.inserted_id)
    
    async def get_user_applications(self, user_id: str) -> list:
        """Get all applications for a user"""
        # Convert string user_id to ObjectId for query
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        cursor = self.db.applications.find({"user_id": user_id, "is_active": True})
        applications = await cursor.to_list(length=None)
        return convert_objectid_to_str(applications)
    
    async def get_application_by_id(self, app_id: str) -> Optional[dict]:
        """Get application by ID"""
        # Convert string app_id to ObjectId for query
        if isinstance(app_id, str):
            app_id = ObjectId(app_id)
        application = await self.db.applications.find_one({"_id": app_id})
        return convert_objectid_to_str(application) if application else None
    
    async def update_application(self, app_id: str, update_data: dict) -> Optional[dict]:
        """Update application and return updated document"""
        try:
            # Convert string app_id to ObjectId for query
            if isinstance(app_id, str):
                app_id = ObjectId(app_id)
            
            result = await self.db.applications.update_one(
                {"_id": app_id}, 
                {"$set": update_data}
            )
            if result.modified_count > 0:
                # Return the updated application
                updated_app = await self.db.applications.find_one({"_id": app_id})
                if updated_app:
                    return convert_objectid_to_str(updated_app)
                return None
            return None
        except Exception as e:
            logger.error(f"Error updating application: {e}")
            return None
    
    async def delete_application(self, app_id: str) -> bool:
        """Soft delete application"""
        result = await self.db.applications.update_one(
            {"_id": app_id}, 
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    # Schedule operations
    async def create_schedule(self, schedule_data: dict) -> str:
        """Create a new schedule"""
        result = await self.db.schedules.insert_one(schedule_data)
        return str(result.inserted_id)
    
    async def get_active_schedules(self) -> list:
        """Get all active schedules"""
        cursor = self.db.schedules.find({"is_active": True})
        return await cursor.to_list(length=None)
    
    async def get_application_schedules(self, app_id: str) -> list:
        """Get schedules for an application"""
        cursor = self.db.schedules.find({"application_id": app_id})
        return await cursor.to_list(length=None)
    
    async def update_schedule_next_run(self, schedule_id: str, next_run: str) -> bool:
        """Update schedule next run time"""
        result = await self.db.schedules.update_one(
            {"_id": schedule_id}, 
            {"$set": {"next_run": next_run}}
        )
        return result.modified_count > 0
    
    # Analysis run operations
    async def create_analysis_run(self, run_data: dict) -> str:
        """Create a new analysis run"""
        result = await self.db.analysis_runs.insert_one(run_data)
        return str(result.inserted_id)
    
    async def get_analysis_runs(self, app_id: str, limit: int = 10) -> list:
        """Get analysis runs for an application"""
        # Query for both string and ObjectId formats to handle data inconsistency
        cursor = self.db.analysis_runs.find({
            "$or": [
                {"application_id": app_id},  # String format
                {"application_id": ObjectId(app_id)}  # ObjectId format
            ]
        }).sort("created_at", DESCENDING).limit(limit)
        runs = await cursor.to_list(length=None)
        
        # Convert _id to id for consistency with other endpoints
        for run in runs:
            if "_id" in run:
                run["id"] = str(run["_id"])
                del run["_id"]
        
        return convert_objectid_to_str(runs)
    
    async def get_all_analysis_runs_for_user(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get all analysis runs for a user across all applications"""
        # Get user's applications
        applications = await self.get_user_applications(user_id)
        app_ids = [app["_id"] for app in applications]
        
        # Get analysis runs for all applications
        cursor = self.db.analysis_runs.find(
            {"application_id": {"$in": app_ids}}
        ).sort("started_at", DESCENDING).limit(limit)
        runs = await cursor.to_list(length=limit)
        
        # Convert _id to id for consistency with other endpoints
        for run in runs:
            if "_id" in run:
                run["id"] = str(run["_id"])
                del run["_id"]
        
        return convert_objectid_to_str(runs)
    
    async def get_analysis_run_by_id(self, run_id: str) -> Optional[dict]:
        """Get analysis run by ID"""
        # Convert string run_id to ObjectId for query
        if isinstance(run_id, str):
            run_id = ObjectId(run_id)
        run = await self.db.analysis_runs.find_one({"_id": run_id})
        if run:
            # Convert _id to id for consistency
            if "_id" in run:
                run["id"] = str(run["_id"])
                del run["_id"]
            return convert_objectid_to_str(run)
        return None
    
    async def update_analysis_run(self, run_id: str, update_data: dict) -> bool:
        """Update analysis run"""
        # Convert string run_id to ObjectId for query
        if isinstance(run_id, str):
            run_id = ObjectId(run_id)
        result = await self.db.analysis_runs.update_one(
            {"_id": run_id}, 
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_analysis_run(self, run_id: str) -> bool:
        """Delete an analysis run and all related data"""
        try:
            # Convert string run_id to ObjectId for query
            if isinstance(run_id, str):
                run_id = ObjectId(run_id)
            
            # Delete all related data
            await self.db.analysis_results.delete_many({"run_id": str(run_id)})
            await self.db.link_validations.delete_many({"run_id": str(run_id)})
            await self.db.change_detections.delete_many({"run_id": str(run_id)})
            await self.db.crawl_sessions.delete_many({"run_id": str(run_id)})
            
            # Delete the run itself
            result = await self.db.analysis_runs.delete_one({"_id": run_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting analysis run {run_id}: {e}")
            return False
    
    # Analysis results operations
    async def save_analysis_results(self, results: list) -> int:
        """Save analysis results"""
        if results:
            result = await self.db.analysis_results.insert_many(results)
            return len(result.inserted_ids)
        return 0
    
    async def get_analysis_results(self, run_id: str) -> list:
        """Get analysis results for a run"""
        cursor = self.db.analysis_results.find({"run_id": run_id})
        results = await cursor.to_list(length=None)
        
        # Convert _id to id for consistency
        for result in results:
            if "_id" in result:
                result["id"] = str(result["_id"])
                del result["_id"]
        
        return convert_objectid_to_str(results)
    
    # Link validation operations
    async def save_link_validations(self, validations: list) -> int:
        """Save link validations"""
        if validations:
            result = await self.db.link_validations.insert_many(validations)
            return len(result.inserted_ids)
        return 0
    
    async def get_link_validations(self, run_id: str) -> list:
        """Get link validations for a run"""
        cursor = self.db.link_validations.find({"run_id": run_id})
        validations = await cursor.to_list(length=None)
        
        # Convert _id to id for consistency
        for validation in validations:
            if "_id" in validation:
                validation["id"] = str(validation["_id"])
                del validation["_id"]
        
        return convert_objectid_to_str(validations)
    
    # Change detection operations
    async def save_change_detection(self, change_data: dict) -> str:
        """Save change detection results"""
        result = await self.db.change_detections.insert_one(change_data)
        return str(result.inserted_id)
    
    async def get_change_detection(self, run_id: str) -> Optional[dict]:
        """Get change detection for a run"""
        return await self.db.change_detections.find_one({"run_id": run_id})
    
    # Dashboard operations
    async def get_dashboard_stats(self, user_id: str) -> dict:
        """Get dashboard statistics for a user"""
        # Get user's applications
        applications = await self.get_user_applications(user_id)
        app_ids = [app["_id"] for app in applications]
        
        # Count total runs
        total_runs = await self.db.analysis_runs.count_documents(
            {"application_id": {"$in": app_ids}}
        )
        
        # Count active schedules
        active_schedules = await self.db.schedules.count_documents(
            {"application_id": {"$in": app_ids}, "is_active": True}
        )
        
        # Get recent runs
        recent_runs_cursor = self.db.analysis_runs.find(
            {"application_id": {"$in": app_ids}}
        ).sort("created_at", DESCENDING).limit(5)
        recent_runs = await recent_runs_cursor.to_list(length=None)
        
        # Convert _id to id for Pydantic model compatibility
        for run in recent_runs:
            if "_id" in run:
                run["id"] = str(run["_id"])
                del run["_id"]
        
        # Get top issues (broken links, blank pages)
        broken_links = await self.db.link_validations.count_documents(
            {"run_id": {"$in": [run["id"] for run in recent_runs]}, "status": "broken"}
        )
        
        blank_pages = await self.db.analysis_results.count_documents(
            {"run_id": {"$in": [run["id"] for run in recent_runs]}, "page_type": "blank"}
        )
        
        return {
            "total_applications": len(applications),
            "total_runs": total_runs,
            "active_schedules": active_schedules,
            "recent_runs": convert_objectid_to_str(recent_runs),
            "top_issues": {
                "broken_links": broken_links,
                "blank_pages": blank_pages
            }
        }
    
    # Content analysis operations
    async def save_page_data(self, page_data: dict) -> str:
        """Save page data to MongoDB with enhanced content storage"""
        # Ensure we have proper content structure for comparison
        enhanced_page_data = {
            **page_data,
            "html_content": page_data.get("html_content", ""),
            "text_content": page_data.get("text_content", ""),
            "html_structure": page_data.get("html_structure", {}),
            "content_chunks": page_data.get("content_chunks", []),
            "page_url": page_data.get("page_url", ""),
            "page_title": page_data.get("page_title", ""),
            "word_count": page_data.get("word_count", 0),
            "page_type": page_data.get("page_type", "unknown"),
            "saved_at": datetime.utcnow().isoformat()
        }
        result = await self.db.pages.insert_one(enhanced_page_data)
        return str(result.inserted_id)
    
    async def get_page_content_by_url(self, url: str) -> Optional[dict]:
        """Get page content by URL"""
        return await self.db.pages.find_one({"page_url": url})
    
    async def save_content_analysis(self, analysis_data: dict) -> str:
        """Save content analysis results"""
        result = await self.db.content_analyses.insert_one(analysis_data)
        return str(result.inserted_id)
    
    async def get_content_analysis(self, run_id: str) -> Optional[dict]:
        """Get content analysis for a run"""
        return await self.db.content_analyses.find_one({"run_id": run_id})
    
    async def get_content_comparison(self, current_run_id: str, previous_run_id: str) -> dict:
        """Get AI-powered content comparison between two runs"""
        current_analysis = await self.get_content_analysis(current_run_id)
        previous_analysis = await self.get_content_analysis(previous_run_id)
        
        if not current_analysis or not previous_analysis:
            return {"error": "One or both content analyses not found"}
        
        # Perform AI-powered comparison
        comparison = await self._perform_ai_content_comparison(
            current_analysis, previous_analysis
        )
        
        return comparison
    
    async def _perform_ai_content_comparison(self, current_analysis: dict, previous_analysis: dict) -> dict:
        """Perform AI-powered content comparison using the AI module"""
        try:
            # Import here to avoid circular imports
            from ai import ComparisonEngine
            
            # Initialize comparison engine
            comparison_engine = ComparisonEngine()
            
            # Perform AI-powered comparison
            comparison_result = await comparison_engine.compare_analysis_runs(
                current_analysis, previous_analysis
            )
            
            # Convert to dict format
            return comparison_result.dict()
            
        except Exception as e:
            logger.error(f"Error in AI content comparison: {e}")
            
            # Fallback to basic comparison
            current_results = current_analysis.get("analysis_results", [])
            previous_results = previous_analysis.get("analysis_results", [])
            
            # Create URL maps for comparison
            current_pages = {page["page_url"]: page for page in current_results}
            previous_pages = {page["page_url"]: page for page in previous_results}
            
            # Find changes
            new_pages = [url for url in current_pages.keys() if url not in previous_pages]
            removed_pages = [url for url in previous_pages.keys() if url not in current_pages]
            modified_pages = []
            
            for url in current_pages.keys():
                if url in previous_pages:
                    current_page = current_pages[url]
                    previous_page = previous_pages[url]
                    
                    # Compare word counts and content
                    if (current_page.get("word_count", 0) != previous_page.get("word_count", 0) or
                        current_page.get("ai_analysis") != previous_page.get("ai_analysis")):
                        modified_pages.append({
                            "url": url,
                            "title": current_page.get("page_title", ""),
                            "word_count_change": current_page.get("word_count", 0) - previous_page.get("word_count", 0),
                            "content_changed": True
                        })
            
            return {
                "comparison_timestamp": datetime.utcnow().isoformat(),
                "current_run_id": current_analysis.get("run_id"),
                "previous_run_id": previous_analysis.get("run_id"),
                "new_pages": new_pages,
                "removed_pages": removed_pages,
                "modified_pages": modified_pages,
                "total_pages_compared": len(current_pages),
                "changes_summary": {
                    "new_pages_count": len(new_pages),
                    "removed_pages_count": len(removed_pages),
                    "modified_pages_count": len(modified_pages)
                },
                "overall_change_assessment": f"Basic comparison completed (AI analysis failed: {str(e)})",
                "impact_analysis": "Unable to generate AI insights due to technical error",
                "recommendations": ["Fix technical issues and retry comparison"]
            }

    # Parent-child relationship operations
    async def save_parent_child_relationships(self, run_id: str, relationships: dict) -> bool:
        """Save parent-child relationships for a run"""
        try:
            logger.info(f"Saving parent-child relationships for run_id: {run_id}")
            logger.info(f"Relationships data keys: {list(relationships.keys())}")
            
            relationship_data = {
                "run_id": run_id,
                "start_url": relationships.get("start_url"),
                "parent_map": relationships.get("parent_map", {}),
                "children_map": {k: list(v) for k, v in relationships.get("children_map", {}).items()},
                "path_map": relationships.get("path_map", {}),
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"Relationship data to save with {len(relationship_data['parent_map'])} parent mappings")
            
            # Upsert the relationships
            result = await self.db.parent_child_relationships.replace_one(
                {"run_id": run_id},
                relationship_data,
                upsert=True
            )
            
            logger.info(f"Database operation result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error saving parent-child relationships: {e}")
            return False
    
    async def get_parent_child_relationships(self, run_id: str) -> Optional[dict]:
        """Get parent-child relationships for a run"""
        try:
            logger.info(f"Getting parent-child relationships for run_id: {run_id}")
            result = await self.db.parent_child_relationships.find_one({"run_id": run_id})
            if result:
                logger.info(f"Found parent-child relationships: {result}")
                # Convert children_map back to sets
                if "children_map" in result:
                    result["children_map"] = {k: set(v) for k, v in result["children_map"].items()}
                return result
            else:
                logger.warning(f"No parent-child relationships found for run_id: {run_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting parent-child relationships: {e}")
            return None
    
    # Source code storage operations
    async def save_page_source_code(self, run_id: str, page_url: str, source_code: str, parent_url: str = None) -> bool:
        """Save HTML source code for a page"""
        try:
            logger.info(f"Saving source code: run_id={run_id}, page_url={page_url}, content_length={len(source_code)}, parent_url={parent_url}")
            
            source_data = {
                "run_id": run_id,
                "page_url": page_url,
                "source_code": source_code,
                "parent_url": parent_url,
                "created_at": datetime.utcnow()
            }
            
            # Upsert the source code
            result = await self.db.page_source_codes.replace_one(
                {"run_id": run_id, "page_url": page_url},
                source_data,
                upsert=True
            )
            
            logger.info(f"Source code save result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error saving page source code: {e}")
            return False
    
    async def get_page_source_code(self, run_id: str, page_url: str) -> Optional[dict]:
        """Get HTML source code for a page - optimized with hierarchical parent traversal"""
        try:
            logger.info(f"Getting source code: run_id={run_id}, page_url={page_url}")
            
            # First, try to get source code directly for this page
            result = await self.db.page_source_codes.find_one({
                "run_id": run_id,
                "page_url": page_url
            })
            
            if result:
                logger.info(f"Found direct source code for {page_url}, content length: {len(result.get('source_code', ''))}")
                return result
            
            # If not found, traverse up the parent hierarchy to find the nearest parent with source code
            try:
                relationships = await self.get_parent_child_relationships(run_id)
                if relationships and "parent_map" in relationships:
                    parent_map = relationships["parent_map"]
                    current_url = page_url
                    traversal_path = [current_url]
                    max_depth = 10  # Prevent infinite loops
                    depth = 0
                    
                    # Traverse up the parent hierarchy
                    while current_url in parent_map and depth < max_depth:
                        parent_url = parent_map[current_url]
                        traversal_path.append(parent_url)
                        depth += 1
                        logger.info(f"Traversing up hierarchy (depth {depth}): {current_url} -> {parent_url}")
                        
                        # Check if this parent has source code stored
                        parent_result = await self.db.page_source_codes.find_one({
                            "run_id": run_id,
                            "page_url": parent_url
                        })
                        
                        if parent_result:
                            logger.info(f"Found source code for {page_url} via hierarchical traversal to parent {parent_url}, content length: {len(parent_result.get('source_code', ''))}")
                            logger.info(f"Traversal path: {' -> '.join(traversal_path)}")
                            # Return parent's source code but with the requested page_url
                            return {
                                **parent_result,
                                "page_url": page_url,  # Override with the requested page URL
                                "actual_source_page": parent_url,  # Track which page actually has the source
                                "traversal_path": traversal_path,  # Show the path taken to find source
                                "hierarchy_depth": len(traversal_path) - 1  # How many levels up we went
                            }
                        
                        # Move up to the next parent
                        current_url = parent_url
                    
                    if depth >= max_depth:
                        logger.warning(f"Max traversal depth reached for {page_url}: {' -> '.join(traversal_path)}")
                    else:
                        logger.warning(f"No source code found for {page_url} after traversing entire hierarchy: {' -> '.join(traversal_path)}")
                else:
                    logger.warning(f"No parent-child relationships found for run {run_id}")
            except Exception as traversal_error:
                logger.error(f"Error during hierarchical traversal for {page_url}: {traversal_error}")
                # Continue to return None if traversal fails
            
            logger.warning(f"No source code found for {page_url} (direct or via hierarchy)")
            return None
        except Exception as e:
            logger.error(f"Error getting page source code: {e}")
            return None
    
    async def get_broken_link_with_parent_info(self, run_id: str, broken_url: str) -> Optional[dict]:
        """Get broken link with parent information and source code"""
        try:
            logger.info(f"Getting broken link info for run_id: {run_id}, broken_url: {broken_url}")
            
            # Get the broken link validation
            link_validation = await self.db.link_validations.find_one({
                "run_id": run_id,
                "url": broken_url,
                "status": "broken"
            })
            
            if not link_validation:
                logger.warning(f"Broken link validation not found for: {broken_url}")
                return None
            
            logger.info(f"Found broken link validation: {link_validation}")
            
            # Get parent-child relationships
            relationships = await self.get_parent_child_relationships(run_id)
            parent_url = None
            if relationships and "parent_map" in relationships:
                parent_url = relationships["parent_map"].get(broken_url)
                logger.info(f"Found parent URL: {parent_url} for broken URL: {broken_url}")
            else:
                logger.warning(f"No parent-child relationships found for run_id: {run_id}")
            
            # Get source code of parent page
            source_code = None
            if parent_url:
                source_data = await self.get_page_source_code(run_id, parent_url)
                if source_data:
                    source_code = source_data.get("source_code")
                    logger.info(f"Found source code for parent: {parent_url}")
                else:
                    logger.warning(f"No source code found for parent: {parent_url}")
            
            return {
                "link_validation": link_validation,
                "parent_url": parent_url,
                "source_code": source_code,
                "parent_title": None  # Will be filled from page data if available
            }
        except Exception as e:
            logger.error(f"Error getting broken link with parent info: {e}")
            return None
    
    async def get_page_data_by_url(self, run_id: str, page_url: str) -> Optional[dict]:
        """Get page data by URL for a specific run"""
        try:
            return await self.db.analysis_results.find_one({
                "run_id": run_id,
                "page_url": page_url
            })
        except Exception as e:
            logger.error(f"Error getting page data by URL: {e}")
            return None
    
    # JSON Export operations
    async def export_analysis_results_to_json(self, run_id: str) -> str:
        """Export complete analysis results to JSON file for debugging and verification"""
        try:
            import json
            import os
            from datetime import datetime
            
            logger.info(f"Exporting analysis results to JSON for run_id: {run_id}")
            
            # Get all analysis data
            run = await self.get_analysis_run_by_id(run_id)
            logger.info(f"Got run data: {run is not None}")
            
            results = await self.get_analysis_results(run_id)
            logger.info(f"Got analysis results: {len(results) if results else 0} pages")
            
            link_validations = await self.get_link_validations(run_id)
            logger.info(f"Got link validations: {len(link_validations) if link_validations else 0} links")
            
            relationships = await self.get_parent_child_relationships(run_id)
            logger.info(f"Got relationships: {relationships is not None}")
            
            change_detection = await self.get_change_detection(run_id)
            logger.info(f"Got change detection: {change_detection is not None}")
            
            # Get HTML source codes for all pages (optimized - only parent pages have source)
            source_codes = []
            logger.info(f"Starting source code collection for {len(results) if results else 0} pages")
            if results:
                for page in results:
                    page_url = page.get('page_url')
                    if page_url:
                        try:
                            source_data = await self.get_page_source_code(run_id, page_url)
                            if source_data:
                                source_codes.append({
                                    "page_url": page_url,
                                    "source_code": source_data.get("source_code", ""),
                                    "parent_url": source_data.get("parent_url"),
                                    "source_length": len(source_data.get("source_code", "")),
                                    "created_at": source_data.get("created_at"),
                                    "actual_source_page": source_data.get("actual_source_page", page_url),
                                    "is_source_from_parent": source_data.get("actual_source_page") != page_url,
                                    "traversal_path": source_data.get("traversal_path", [page_url]),
                                    "hierarchy_depth": source_data.get("hierarchy_depth", 0),
                                    "optimization_note": "Source code is stored only for pages with children to avoid duplication. Leaf pages get source from nearest parent via hierarchical traversal."
                                })
                        except Exception as source_error:
                            logger.error(f"Error getting source code for {page_url}: {source_error}")
                            # Continue with other pages even if one fails
            
            logger.info(f"Collected {len(source_codes)} source codes")
            
            # Get application details
            application = None
            if run and run.get("application_id"):
                application = await self.get_application_by_id(run["application_id"])
            
            # Create comprehensive export data
            export_data = {
                "export_info": {
                    "run_id": run_id,
                    "exported_at": datetime.utcnow().isoformat(),
                    "export_version": "1.0",
                    "description": "Complete analysis results export for debugging and verification"
                },
                "analysis_run": run,
                "application": application,
                "analysis_results": {
                    "total_pages": len(results) if results else 0,
                    "pages": results or []
                },
                "link_validations": {
                    "total_links": len(link_validations) if link_validations else 0,
                    "broken_links_count": len([link for link in (link_validations or []) if link.get('status') == 'broken']),
                    "valid_links_count": len([link for link in (link_validations or []) if link.get('status') == 'valid']),
                    "links": link_validations or []
                },
                "parent_child_relationships": relationships,
                "change_detection": change_detection,
                "statistics": {
                    "total_pages_analyzed": run.get("total_pages_analyzed", 0) if run else 0,
                    "total_links_found": run.get("total_links_found", 0) if run else 0,
                    "broken_links_count": run.get("broken_links_count", 0) if run else 0,
                    "blank_pages_count": run.get("blank_pages_count", 0) if run else 0,
                    "content_pages_count": run.get("content_pages_count", 0) if run else 0,
                    "overall_score": run.get("overall_score", 0) if run else 0
                },
                "page_types_breakdown": {
                    "content_pages": [page for page in (results or []) if page.get('page_type') == 'content'],
                    "blank_pages": [page for page in (results or []) if page.get('page_type') == 'blank'],
                    "error_pages": [page for page in (results or []) if page.get('page_type') == 'error'],
                    "redirect_pages": [page for page in (results or []) if page.get('page_type') == 'redirect']
                },
                "link_status_breakdown": {
                    "valid_links": [link for link in (link_validations or []) if link.get('status') == 'valid'],
                    "broken_links": [link for link in (link_validations or []) if link.get('status') == 'broken'],
                    "redirect_links": [link for link in (link_validations or []) if link.get('status') == 'redirect'],
                    "timeout_links": [link for link in (link_validations or []) if link.get('status') == 'timeout'],
                    "rate_limited_links": [link for link in (link_validations or []) if link.get('status') == 'rate_limited'],
                    "unknown_links": [link for link in (link_validations or []) if link.get('status') == 'unknown']
                },
                "html_source_codes": {
                    "total_pages_with_source": len(source_codes),
                    "total_source_size": sum(code.get("source_length", 0) for code in source_codes),
                    "source_codes": source_codes
                }
            }
            
            # Create filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_export_{run_id}_{timestamp}.json"
            filepath = os.path.join("analysis_exports", filename)
            
            # Ensure directory exists
            os.makedirs("analysis_exports", exist_ok=True)
            
            # Write JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Analysis results exported to: {filepath}")
            logger.info(f"Export contains: {len(results or [])} pages, {len(link_validations or [])} links, {len(source_codes)} source codes")
            logger.info(f"Total source code size: {sum(code.get('source_length', 0) for code in source_codes):,} characters")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting analysis results to JSON: {e}")
            raise

# Global database instance
db_manager = DatabaseManager()

async def get_database():
    """Get database manager instance"""
    try:
        if not db_manager.client:
            await db_manager.connect()
        else:
            # Test if connection is still alive
            try:
                await db_manager.client.admin.command('ping')
            except Exception:
                # Connection is dead, reconnect
                logger.warning("Database connection lost, reconnecting...")
                await db_manager.connect()
        return db_manager
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        raise
