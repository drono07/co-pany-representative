"""
Celery tasks for website analysis platform
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
from celery import current_task

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.tasks.celery_app import celery_app
from backend.core.analysis_engine import AnalysisEngine
from backend.database.database_schema import get_database
import openai
from backend.utils.config import settings
from ai.models.content_analyzer import ContentAnalyzer
from ai.models.comparison_engine import ComparisonEngine

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="celery_tasks.run_website_analysis")
def run_website_analysis(self, run_id: str, application_data: Dict[str, Any]):
    """
    Run website analysis as a Celery task
    
    Args:
        run_id: Analysis run ID
        application_data: Application configuration data
    """
    loop = None
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting analysis", "progress": 0}
        )
        
        # Run analysis in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_run_analysis_async(
                self, run_id, application_data
            ))
            return result
        except Exception as async_error:
            logger.error(f"Async analysis failed for run {run_id}: {async_error}")
            raise
        finally:
            # Clean up event loop after async function is complete
            if loop and not loop.is_closed():
                try:
                    # Give a moment for any pending database operations to complete
                    import time
                    time.sleep(0.1)
                    
                    # Cancel any remaining pending tasks
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        logger.info(f"Cancelling {len(pending)} pending tasks...")
                        for task in pending:
                            if not task.done():
                                task.cancel()
                        
                        # Wait for cancellation to complete with timeout
                        try:
                            loop.run_until_complete(asyncio.wait_for(
                                asyncio.gather(*pending, return_exceptions=True),
                                timeout=2.0
                            ))
                        except (asyncio.TimeoutError, Exception):
                            pass  # Ignore cancellation errors
                        
                        logger.info("All pending tasks cancelled")
                    
                    # Close the loop
                    loop.close()
                    logger.info("Event loop closed successfully")
                    
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {cleanup_error}")
                    try:
                        if not loop.is_closed():
                            loop.close()
                    except Exception:
                        pass
        
    except Exception as e:
        logger.error(f"Analysis task failed for run {run_id}: {e}")
        # Update task state to failure - only if loop is still available
        try:
            if loop and not loop.is_closed():
                self.update_state(
                    state="FAILURE",
                    meta={"error": str(e), "status": "Analysis failed"}
                )
        except Exception as state_error:
            logger.error(f"Error updating task state: {state_error}")
        raise
        
    # Event loop cleanup is handled in the inner try-finally block

async def _run_analysis_async(task, run_id: str, application_data: Dict[str, Any]):
    """Async analysis execution"""
    
    # Update progress
    task.update_state(
        state="PROGRESS",
        meta={"status": "Connecting to database", "progress": 10}
    )
    
    # Get database connection
    try:
        db = await get_database()
        logger.info("Database connection established successfully")
    except Exception as db_error:
        logger.error(f"Failed to connect to database: {db_error}")
        raise
    
    # Update run status to running
    await db.update_analysis_run(run_id, {
        "status": "running",
        "started_at": datetime.utcnow()
    })
    
    task.update_state(
        state="PROGRESS",
        meta={"status": "Starting website analysis", "progress": 20}
    )
    
    try:
        # Run analysis
        logger.info(f"Starting analysis for run {run_id}")
        logger.info(f"Application data received: {application_data}")
        analysis_engine = AnalysisEngine()
        logger.info(f"Analysis engine created successfully")
        
        results = await analysis_engine.analyze_website(
            website_url=application_data["website_url"],
            max_depth=application_data["max_crawl_depth"],
            max_pages_to_crawl=application_data["max_pages_to_crawl"],
            max_links_to_validate=application_data["max_links_to_validate"],
            enable_ai_evaluation=application_data["enable_ai_evaluation"],
            max_ai_evaluation_pages=application_data["max_ai_evaluation_pages"],
            extract_static=application_data.get("extract_static_links", True),
            extract_dynamic=application_data.get("extract_dynamic_links", False),
            extract_resources=application_data.get("extract_resource_links", False),
            extract_external=application_data.get("extract_external_links", False)
        )
        logger.info(f"Analysis completed successfully for run {run_id}")
        
        task.update_state(
            state="PROGRESS",
            meta={"status": "Saving results", "progress": 80}
        )
        
        # Save results to database
        logger.info(f"About to call save_results_to_db for run_id: {run_id}")
        await analysis_engine.save_results_to_db(db, run_id, results)
        logger.info(f"Completed save_results_to_db for run_id: {run_id}")
        
        # Update run status to completed
        await db.update_analysis_run(run_id, {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "total_pages_analyzed": results.get("summary", {}).get("total_pages_analyzed", 0),
            "total_links_found": results.get("summary", {}).get("total_links_found", 0),
            "broken_links_count": results.get("summary", {}).get("broken_links", 0),
            "blank_pages_count": results.get("summary", {}).get("blank_pages", 0),
            "content_pages_count": results.get("summary", {}).get("content_pages", 0),
            "overall_score": results.get("overall_score", 0)
        })
        
        task.update_state(
            state="PROGRESS",
            meta={"status": "Exporting results to JSON", "progress": 85}
        )
        
        # Export analysis results to JSON for debugging and verification
        try:
            logger.info(f"Starting automatic JSON export for run {run_id}")
            export_filepath = await db.export_analysis_results_to_json(run_id)
            logger.info(f"Analysis results exported to JSON: {export_filepath}")
        except Exception as export_error:
            logger.error(f"Failed to export JSON (non-critical): {export_error}")
            import traceback
            logger.error(f"Export error traceback: {traceback.format_exc()}")
        
        task.update_state(
            state="PROGRESS",
            meta={"status": "Sending notifications", "progress": 90}
        )
        
        # Send notification if enabled
        if application_data.get("send_notifications", False):
            send_notification.delay(
                application_data["user_email"],
                f"Analysis completed for {application_data['name']}",
                f"Analysis run {run_id} has completed successfully."
            )
        
        task.update_state(
            state="SUCCESS",
            meta={"status": "Analysis completed", "progress": 100}
        )
        
        return {
            "run_id": run_id,
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Analysis failed for run {run_id}: {e}")
        logger.error(f"Full traceback: {error_details}")
        
        # Update run status to failed
        await db.update_analysis_run(run_id, {
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error_message": f"{str(e)}\n\nTraceback:\n{error_details}"
        })
        
        # Send failure notification
        if application_data.get("send_notifications", False):
            send_notification.delay(
                application_data["user_email"],
                f"Analysis failed for {application_data['name']}",
                f"Analysis run {run_id} failed: {str(e)}"
            )
        
        raise
        
    # Note: Database connection is managed by the connection pool

@celery_app.task(name="celery_tasks.process_scheduled_analyses")
def process_scheduled_analyses():
    """
    Process scheduled analyses - runs every 5 minutes
    """
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_scheduled_analyses_async())
            return result
        except Exception as async_error:
            logger.error(f"Async scheduled analysis failed: {async_error}")
            raise
            
    except Exception as e:
        logger.error(f"Error processing scheduled analyses: {e}")
        raise
        
    finally:
        # Clean up event loop
        if loop and not loop.is_closed():
            try:
                # Cancel any pending tasks
                pending = asyncio.all_tasks(loop)
                if pending:
                    logger.info(f"Cancelling {len(pending)} pending tasks in scheduled analysis...")
                    for task in pending:
                        task.cancel()
                    
                    # Wait for cancellation to complete
                    try:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass  # Ignore cancellation errors
                    
                    logger.info("All pending tasks cancelled in scheduled analysis")
                
                # Close the loop
                loop.close()
                logger.info("Event loop closed successfully in scheduled analysis")
                
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup in scheduled analysis: {cleanup_error}")
                try:
                    if not loop.is_closed():
                        loop.close()
                except Exception:
                    pass

async def _process_scheduled_analyses_async():
    """Async processing of scheduled analyses"""
    
    db = await get_database()
    
    try:
        # Get schedules that need to run
        now = datetime.utcnow()
        schedules = await db.get_active_schedules()
        
        schedules_to_run = []
        for schedule in schedules:
            if schedule.get("next_run") and schedule["next_run"] <= now:
                schedules_to_run.append(schedule)
        
        if not schedules_to_run:
            return {"message": "No schedules to run", "count": 0}
        
        logger.info(f"Found {len(schedules_to_run)} schedules to run")
        
        # Process each schedule
        for schedule in schedules_to_run:
            try:
                # Get application details
                application = await db.get_application_by_id(schedule["application_id"])
                if not application:
                    logger.error(f"Application not found for schedule {schedule['_id']}")
                    continue
                
                # Get user details for notifications
                user = await db.get_user_by_id(application["user_id"])
                
                # Create analysis run
                run_dict = {
                    "application_id": schedule["application_id"],
                    "status": "pending",
                    "created_at": datetime.utcnow()
                }
                
                run_id = await db.create_analysis_run(run_dict)
                
                # Prepare application data for task
                app_data = {
                    "website_url": application["website_url"],
                    "max_crawl_depth": application["max_crawl_depth"],
                    "max_pages_to_crawl": application["max_pages_to_crawl"],
                    "max_links_to_validate": application["max_links_to_validate"],
                    "enable_ai_evaluation": application["enable_ai_evaluation"],
                    "max_ai_evaluation_pages": application["max_ai_evaluation_pages"],
                    "name": application["name"],
                    "user_email": user["email"] if user else None,
                    "send_notifications": True  # Enable notifications for scheduled runs
                }
                
                # Queue the analysis task
                task = run_website_analysis.delay(run_id, app_data)
                
                # Update next run time
                await _update_next_run_time(db, schedule)
                
                logger.info(f"Queued analysis task {task.id} for application {application['name']}")
                
            except Exception as e:
                logger.error(f"Error processing schedule {schedule['_id']}: {e}")
        
        return {
            "message": f"Processed {len(schedules_to_run)} schedules",
            "count": len(schedules_to_run)
        }
        
    except Exception as e:
        logger.error(f"Error in scheduled analysis: {e}")
        return {
            "message": f"Error processing schedules: {str(e)}",
            "count": 0
        }
        
    # Note: Database connection is managed by the connection pool

async def _update_next_run_time(db, schedule: Dict[str, Any]):
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
    
    await db.update_schedule_next_run(schedule["_id"], next_run.isoformat())

@celery_app.task(name="celery_tasks.send_notification")
def send_notification(email: str, subject: str, message: str):
    """
    Send notification email (placeholder for email service integration)
    
    Args:
        email: Recipient email
        subject: Email subject
        message: Email message
    """
    try:
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        logger.info(f"Notification sent to {email}: {subject}")
        
        # For now, just log the notification
        print(f"📧 NOTIFICATION")
        print(f"To: {email}")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print("-" * 50)
        
        return {"status": "sent", "email": email, "subject": subject}
        
    except Exception as e:
        logger.error(f"Failed to send notification to {email}: {e}")
        raise

@celery_app.task(name="celery_tasks.cleanup_old_data")
def cleanup_old_data():
    """
    Cleanup old analysis data - runs daily at 2 AM
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_cleanup_old_data_async())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise

async def _cleanup_old_data_async():
    """Async cleanup of old data"""
    
    db = await get_database()
    
    # Clean up old analysis results (older than 90 days)
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    
    # This would require implementing cleanup methods in the database manager
    # For now, just log the cleanup action
    logger.info(f"Cleaning up data older than {cutoff_date}")
    
    return {
        "message": "Cleanup completed",
        "cutoff_date": cutoff_date.isoformat()
    }

@celery_app.task(name="celery_tasks.health_check")
def health_check():
    """
    Health check task - runs every 10 minutes
    """
    loop = None
    try:
        # Check Redis connection
        from celery_app import celery_app
        celery_app.control.inspect().stats()
        
        # Check database connection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            db = loop.run_until_complete(get_database())
            # Simple database check
            loop.run_until_complete(db.get_active_schedules())
        except Exception as async_error:
            logger.error(f"Async health check failed: {async_error}")
            raise
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "redis": "connected",
            "database": "connected"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
    finally:
        # Clean up event loop
        if loop and not loop.is_closed():
            try:
                # Cancel any pending tasks
                pending = asyncio.all_tasks(loop)
                if pending:
                    logger.info(f"Cancelling {len(pending)} pending tasks in health check...")
                    for task in pending:
                        task.cancel()
                    
                    # Wait for cancellation to complete
                    try:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass  # Ignore cancellation errors
                    
                    logger.info("All pending tasks cancelled in health check")
                
                # Close the loop
                loop.close()
                logger.info("Event loop closed successfully in health check")
                
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup in health check: {cleanup_error}")
                try:
                    if not loop.is_closed():
                        loop.close()
                except Exception:
                    pass

@celery_app.task(name="celery_tasks.get_task_status")
def get_task_status(task_id: str):
    """
    Get status of a Celery task
    
    Args:
        task_id: Celery task ID
    """
    try:
        from celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "info": result.info
        }
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": str(e)
        }

# Task monitoring and management
@celery_app.task(name="celery_tasks.get_worker_stats")
def get_worker_stats():
    """
    Get worker statistics
    """
    try:
        from celery_app import celery_app
        inspect = celery_app.control.inspect()
        
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        
        return {
            "workers": stats,
            "active_tasks": active,
            "scheduled_tasks": scheduled,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        return {"error": str(e)}

@celery_app.task(bind=True, name="celery_tasks.run_content_analysis")
def run_content_analysis(self, run_id: str):
    """
    Run AI-powered content analysis on a specific run
    """
    logger.info(f"Starting content analysis for run {run_id}")
    
    # Run analysis in async context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_run_content_analysis_async(
            self, run_id
        ))
        return result
    except Exception as e:
        logger.error(f"Content analysis task failed for run {run_id}: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Content analysis failed"}
        )
        raise
    finally:
        # Ensure all tasks are completed before closing the loop
        try:
            pending = asyncio.all_tasks(loop)
            if pending:
                logger.info(f"Waiting for {len(pending)} pending tasks to complete...")
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                logger.info("All pending tasks completed")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        finally:
            try:
                loop.close()
                logger.info("Event loop closed successfully")
            except Exception as close_error:
                logger.error(f"Error closing event loop: {close_error}")

async def _run_content_analysis_async(task, run_id: str):
    """Async content analysis execution"""
    
    # Update progress
    task.update_state(
        state="PROGRESS",
        meta={"status": "Loading analysis data", "progress": 10}
    )
    
    # Get database connection
    db = await get_database()
    
    # Get analysis run and results
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        raise Exception(f"Analysis run {run_id} not found")
    
    results = await db.get_analysis_results(run_id)
    if not results:
        raise Exception(f"No analysis results found for run {run_id}")
    
    task.update_state(
        state="PROGRESS",
        meta={"status": "Analyzing content with AI", "progress": 30}
    )
    
    # Initialize AI content analyzer
    if not settings.openai_api_key:
        raise Exception("OpenAI API key not configured")
    
    analyzer = ContentAnalyzer()
    
    # Prepare page data for analysis
    pages_data = []
    for page in results:
        page_content = await db.get_page_content_by_url(page["page_url"])
        if page_content:
            # Combine page data with content
            page_data = {
                "page_url": page["page_url"],
                "page_title": page.get("page_title", ""),
                "word_count": page.get("word_count", 0),
                "page_type": page.get("page_type", "unknown"),
                "text_content": page_content.get("text_content", ""),
                "html_structure": page_content.get("html_structure", {})
            }
            pages_data.append(page_data)
    
    task.update_state(
        state="PROGRESS",
        meta={"status": f"Analyzing {len(pages_data)} pages with AI", "progress": 30}
    )
    
    # Analyze all pages with AI
    content_analysis_results = await analyzer.analyze_multiple_pages(pages_data)
    
    # Convert to dict format for storage
    analysis_results = [result.dict() for result in content_analysis_results]
    
    task.update_state(
        state="PROGRESS",
        meta={"status": "Saving analysis results", "progress": 90}
    )
    
    # Save content analysis results
    analysis_id = await db.save_content_analysis({
        "run_id": run_id,
        "analysis_results": analysis_results,
        "total_pages_analyzed": len(analysis_results),
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "ai_model": "gpt-3.5-turbo"
    })
    
    task.update_state(
        state="SUCCESS",
        meta={"status": "Content analysis completed", "progress": 100}
    )
    
    logger.info(f"Content analysis completed for run {run_id}")
    
    return {
        "analysis_id": analysis_id,
        "total_pages_analyzed": len(analysis_results),
        "status": "completed"
    }

# AI analysis functionality moved to ai/content_analyzer.py
