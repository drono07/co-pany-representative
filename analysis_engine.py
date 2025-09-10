"""
Analysis engine for the FastAPI platform
Integrates with the existing website analysis system
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from main import WebsiteInsightsPlatform
from database_schema import DatabaseManager

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """Analysis engine for running website analysis"""
    
    def __init__(self):
        self.platform = WebsiteInsightsPlatform()
    
    async def analyze_website(
        self,
        website_url: str,
        max_depth: int = 2,
        max_pages_to_crawl: int = 100,
        max_links_to_validate: int = 200,
        enable_ai_evaluation: bool = False,
        max_ai_evaluation_pages: int = 10
    ) -> Dict[str, Any]:
        """Run website analysis with specified parameters"""
        
        logger.info(f"Starting analysis for {website_url}")
        
        # Generate a unique run_id for this analysis
        from bson import ObjectId
        run_id = str(ObjectId())
        logger.info(f"Generated run_id: {run_id}")
        
        # Set environment variables for the analysis
        import os
        os.environ["MAX_PAGES_TO_CRAWL"] = str(max_pages_to_crawl)
        os.environ["MAX_LINKS_TO_VALIDATE"] = str(max_links_to_validate)
        os.environ["ENABLE_AI_EVALUATION"] = str(enable_ai_evaluation).lower()
        os.environ["MAX_AI_EVALUATION_PAGES"] = str(max_ai_evaluation_pages)
        
        try:
            # Run the analysis using the existing platform
            results = await self.platform.analyze_website(
                url=website_url,
                max_depth=max_depth,
                include_screenshots=False,
                max_pages_to_crawl=max_pages_to_crawl,
                max_links_to_validate=max_links_to_validate
            )
            
            # Add run_id to results
            results["run_id"] = run_id
            logger.info(f"Analysis completed for {website_url} with run_id: {run_id}")
            
            # Save results to database
            try:
                from database_schema import DatabaseManager
                db = DatabaseManager()
                await db.connect()
                await self.save_results_to_db(db, run_id, results)
                logger.info(f"Results saved to database for run_id: {run_id}")
            except Exception as e:
                logger.error(f"Failed to save results to database: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed for {website_url}: {e}")
            raise
    
    async def save_results_to_db(
        self,
        db: DatabaseManager,
        run_id: str,
        results: Dict[str, Any]
    ):
        """Save analysis results to database"""
        
        try:
            # Save analysis results
            analysis_results = []
            for page in results.get("detailed_findings", {}).get("content_pages", []):
                analysis_results.append({
                    "run_id": run_id,
                    "page_url": page["url"],
                    "page_title": page.get("title"),
                    "word_count": page.get("word_count", 0),
                    "page_type": "content",
                    "has_header": page.get("has_header", False),
                    "has_footer": page.get("has_footer", False),
                    "has_navigation": page.get("has_navigation", False),
                    "path": page.get("path", []),
                    "crawled_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                })
            
            for page in results.get("detailed_findings", {}).get("blank_pages", []):
                analysis_results.append({
                    "run_id": run_id,
                    "page_url": page["url"],
                    "page_title": page.get("title"),
                    "word_count": page.get("word_count", 0),
                    "page_type": "blank",
                    "has_header": page.get("has_header", False),
                    "has_footer": page.get("has_footer", False),
                    "has_navigation": page.get("has_navigation", False),
                    "path": page.get("path", []),
                    "crawled_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                })
            
            for page in results.get("detailed_findings", {}).get("error_pages", []):
                analysis_results.append({
                    "run_id": run_id,
                    "page_url": page["url"],
                    "page_title": page.get("title"),
                    "word_count": page.get("word_count", 0),
                    "page_type": "error",
                    "has_header": page.get("has_header", False),
                    "has_footer": page.get("has_footer", False),
                    "has_navigation": page.get("has_navigation", False),
                    "path": page.get("path", []),
                    "crawled_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                })
            
            # Save analysis results
            if analysis_results:
                await db.save_analysis_results(analysis_results)
                logger.info(f"Saved {len(analysis_results)} analysis results")
            
            # Save link validations
            link_validations = []
            for link in results.get("detailed_findings", {}).get("broken_links", []):
                link_validations.append({
                    "run_id": run_id,
                    "url": link["url"],
                    "status_code": link.get("status_code"),
                    "status": "broken",
                    "response_time": link.get("response_time"),
                    "error_message": link.get("error"),
                    "created_at": datetime.utcnow()
                })
            
            # Add valid links (if available in results)
            for link in results.get("detailed_findings", {}).get("valid_links", []):
                link_validations.append({
                    "run_id": run_id,
                    "url": link["url"],
                    "status_code": 200,
                    "status": "valid",
                    "response_time": link.get("response_time"),
                    "created_at": datetime.utcnow()
                })
            
            # Save link validations
            if link_validations:
                await db.save_link_validations(link_validations)
                logger.info(f"Saved {len(link_validations)} link validations")
            
            # Save parent-child relationships if available
            if "path_tracking" in results and results["path_tracking"]:
                path_tracking = results["path_tracking"]
                logger.info(f"Path tracking data keys: {list(path_tracking.keys())}")
                relationships = {
                    "parent_map": path_tracking.get("parent_map", {}),
                    "children_map": path_tracking.get("children_map", {}),
                    "path_map": path_tracking.get("path_map", {})
                }
                logger.info(f"Saving relationships with {len(relationships['parent_map'])} parent mappings")
                success = await db.save_parent_child_relationships(run_id, relationships)
                if success:
                    logger.info("Successfully saved parent-child relationships")
                else:
                    logger.error("Failed to save parent-child relationships")
            else:
                logger.warning("No path_tracking data found in results")
            
            # Save page source codes for all page types
            source_codes_saved = 0
            all_pages = []
            all_pages.extend(results.get("detailed_findings", {}).get("content_pages", []))
            all_pages.extend(results.get("detailed_findings", {}).get("blank_pages", []))
            all_pages.extend(results.get("detailed_findings", {}).get("error_pages", []))
            
            # Get parent-child relationships to optimize source code storage
            relationships = await db.get_parent_child_relationships(run_id)
            parent_map = relationships.get("parent_map", {}) if relationships else {}
            children_map = relationships.get("children_map", {}) if relationships else {}
            
            # Track which pages we've already saved source code for
            saved_source_pages = set()
            
            for page in all_pages:
                html_content = page.get("html_content", "")
                page_url = page.get("url", "unknown")
                logger.info(f"Processing page: {page_url}, html_content length: {len(html_content)}")
                
                if html_content:
                    # Get parent URL from path
                    parent_url = None
                    if page.get("path") and len(page["path"]) > 1:
                        parent_url = page["path"][-2]  # Second to last in path
                    
                    # Determine if this page has children (is a parent at any depth)
                    has_children = page_url in children_map and len(children_map[page_url]) > 0
                    
                    # Only save source code for pages that have children (parent pages at any depth)
                    # Leaf pages (no children) will get their source code from their nearest parent via the API
                    if has_children and page_url not in saved_source_pages:
                        logger.info(f"Saving source code for PARENT page (has {len(children_map[page_url])} children): {page_url}, content length: {len(html_content)}")
                        success = await db.save_page_source_code(
                            run_id, 
                            page_url, 
                            html_content, 
                            parent_url
                        )
                        if success:
                            source_codes_saved += 1
                            saved_source_pages.add(page_url)
                            logger.info(f"Successfully saved source code for parent page: {page_url}")
                        else:
                            logger.error(f"Failed to save source code for parent page: {page_url}")
                    elif not has_children:
                        logger.info(f"Skipping source code save for LEAF page: {page_url} (no children - will use parent's source)")
                    else:
                        logger.info(f"Skipping duplicate source code save for parent page: {page_url}")
                else:
                    logger.warning(f"Page {page_url} has no html_content (length: {len(html_content)})")
            
            if source_codes_saved > 0:
                logger.info(f"Saved {source_codes_saved} page source codes")
            
            # Save change detection if available
            if "change_detection" in results:
                change_data = {
                    "run_id": run_id,
                    "previous_run_id": results["change_detection"].get("previous_run_id"),
                    "new_pages_count": len(results["change_detection"].get("new_pages", [])),
                    "removed_pages_count": len(results["change_detection"].get("removed_pages", [])),
                    "modified_pages_count": len(results["change_detection"].get("modified_pages", [])),
                    "unchanged_pages_count": len(results["change_detection"].get("unchanged_pages", [])),
                    "changes_summary": results["change_detection"],
                    "created_at": datetime.utcnow()
                }
                
                await db.save_change_detection(change_data)
                logger.info("Saved change detection results")
            
            logger.info(f"Successfully saved all results for run {run_id}")
            
        except Exception as e:
            logger.error(f"Failed to save results for run {run_id}: {e}")
            raise

class SchedulerEngine:
    """Scheduler engine for automated analysis runs"""
    
    def __init__(self):
        self.db = None
    
    async def initialize(self):
        """Initialize the scheduler"""
        from database_schema import get_database
        self.db = await get_database()
    
    async def get_schedules_to_run(self) -> List[Dict[str, Any]]:
        """Get schedules that need to be run"""
        if not self.db:
            await self.initialize()
        
        # Get active schedules where next_run is due
        now = datetime.utcnow()
        schedules = await self.db.get_active_schedules()
        
        schedules_to_run = []
        for schedule in schedules:
            if schedule.get("next_run") and schedule["next_run"] <= now:
                schedules_to_run.append(schedule)
        
        return schedules_to_run
    
    async def run_scheduled_analysis(self, schedule: Dict[str, Any]):
        """Run analysis for a scheduled task"""
        try:
            # Get application details
            application = await self.db.get_application_by_id(schedule["application_id"])
            if not application:
                logger.error(f"Application not found for schedule {schedule['_id']}")
                return
            
            # Create analysis run
            run_dict = {
                "application_id": schedule["application_id"],
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            run_id = await self.db.create_analysis_run(run_dict)
            
            # Run analysis
            analysis_engine = AnalysisEngine()
            results = await analysis_engine.analyze_website(
                application["website_url"],
                application["max_crawl_depth"],
                application["max_pages_to_crawl"],
                application["max_links_to_validate"],
                application["enable_ai_evaluation"],
                application["max_ai_evaluation_pages"]
            )
            
            # Save results
            await analysis_engine.save_results_to_db(self.db, run_id, results)
            
            # Update run status
            await self.db.update_analysis_run(run_id, {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "total_pages_analyzed": results.get("summary", {}).get("total_pages_analyzed", 0),
                "total_links_found": results.get("summary", {}).get("total_links_found", 0),
                "broken_links_count": results.get("summary", {}).get("broken_links", 0),
                "blank_pages_count": results.get("summary", {}).get("blank_pages", 0),
                "content_pages_count": results.get("summary", {}).get("content_pages", 0),
                "overall_score": results.get("overall_score", 0)
            })
            
            # Update next run time
            await self._update_next_run_time(schedule)
            
            logger.info(f"Scheduled analysis completed for application {application['name']}")
            
        except Exception as e:
            logger.error(f"Scheduled analysis failed for schedule {schedule['_id']}: {e}")
            
            # Update run status to failed if run was created
            if 'run_id' in locals():
                await self.db.update_analysis_run(run_id, {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error_message": str(e)
                })
    
    async def _update_next_run_time(self, schedule: Dict[str, Any]):
        """Update next run time for a schedule"""
        from datetime import timedelta
        
        frequency = schedule["frequency"]
        now = datetime.utcnow()
        
        if frequency == "daily":
            next_run = now + timedelta(days=1)
        elif frequency == "weekly":
            next_run = now + timedelta(weeks=1)
        elif frequency == "monthly":
            next_run = now + timedelta(days=30)
        else:
            # For custom schedules, you would parse the cron expression
            # For now, default to daily
            next_run = now + timedelta(days=1)
        
        await self.db.update_schedule_next_run(schedule["_id"], next_run.isoformat())
    
    async def run_scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Starting scheduler loop")
        
        while True:
            try:
                # Get schedules to run
                schedules = await self.get_schedules_to_run()
                
                if schedules:
                    logger.info(f"Found {len(schedules)} schedules to run")
                    
                    # Run each schedule
                    for schedule in schedules:
                        await self.run_scheduled_analysis(schedule)
                
                # Wait before checking again (check every minute)
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
