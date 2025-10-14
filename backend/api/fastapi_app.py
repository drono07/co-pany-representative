"""
FastAPI application for website analysis platform
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from bson import ObjectId
from urllib.parse import unquote

from .api_models import (
    UserCreate, User, ApplicationCreate, ApplicationUpdate, Application, 
    ScheduleCreate, ScheduleUpdate, Schedule, AnalysisRunCreate, AnalysisRun, 
    AnalysisRunResponse, DashboardStats, ContextComparison, Token, LoginRequest,
    SourceCodeResponse, HighlightedLink, ParentChildRelationships, AnalysisStatus
)
from ..database.database_schema import get_database, DatabaseManager
from ..tasks.celery_tasks import run_website_analysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Website Analysis Platform",
    description="A comprehensive platform for website analysis with automated scheduling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here"  # Use environment variable in production
ALGORITHM = "HS256"

# ObjectId conversion is now handled in the database layer
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = await get_database()
    user = await db.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Authentication endpoints
@app.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    db = await get_database()
    
    # Check if user already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role.value,
        "password_hash": hashed_password.decode('utf-8'),
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    user_id = await db.create_user(user_dict)
    
    return {
        "message": "User created successfully", 
        "user": {
            "id": str(user_id),
            "email": user_data.email,
            "name": user_data.name,
            "role": user_data.role.value
        }
    }

@app.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Login user and return access token"""
    db = await get_database()
    
    # Get user
    user = await db.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(
        {"sub": user["email"], "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": str(user["_id"]),  # Convert ObjectId to string
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }

# Application endpoints
@app.post("/applications", response_model=dict)
async def create_application(
    app_data: ApplicationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new application"""
    db = await get_database()
    
    app_dict = {
        "user_id": current_user["_id"],
        "name": app_data.name,
        "description": app_data.description,
        "website_url": str(app_data.website_url),
        "max_crawl_depth": app_data.max_crawl_depth,
        "max_pages_to_crawl": app_data.max_pages_to_crawl,
        "max_links_to_validate": app_data.max_links_to_validate,
        "enable_ai_evaluation": app_data.enable_ai_evaluation,
        "max_ai_evaluation_pages": app_data.max_ai_evaluation_pages,
        "extract_static_links": app_data.extract_static_links,
        "extract_dynamic_links": app_data.extract_dynamic_links,
        "extract_resource_links": app_data.extract_resource_links,
        "extract_external_links": app_data.extract_external_links,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    app_id = await db.create_application(app_dict)
    return {"message": "Application created successfully", "application_id": str(app_id)}

@app.get("/applications", response_model=List[dict])
async def get_applications(current_user: dict = Depends(get_current_user)):
    """Get user's applications"""
    db = await get_database()
    applications = await db.get_user_applications(current_user["_id"])
    return applications

@app.get("/applications/{app_id}", response_model=dict)
async def get_application(
    app_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific application"""
    db = await get_database()
    application = await db.get_application_by_id(app_id)
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return application

@app.put("/applications/{app_id}", response_model=dict)
async def update_application(
    app_id: str,
    app_data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update application"""
    db = await get_database()
    
    # Check if application exists and belongs to user
    application = await db.get_application_by_id(app_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prepare update data
    update_data = {"updated_at": datetime.utcnow()}
    for field, value in app_data.dict(exclude_unset=True).items():
        if value is not None:
            if field == "website_url":
                update_data[field] = str(value)
            else:
                update_data[field] = value
    
    success = await db.update_application(app_id, update_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update application"
        )
    
    return {"message": "Application updated successfully"}

@app.patch("/applications/{app_id}", response_model=dict)
async def partial_update_application(
    app_id: str,
    app_data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Partially update application (PATCH)"""
    try:
        db = await get_database()
        
        # Check if application exists and belongs to user
        application = await db.get_application_by_id(app_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        if application["user_id"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Prepare update data - only include fields that are provided
        update_data = {"updated_at": datetime.utcnow()}
        for field, value in app_data.dict(exclude_unset=True).items():
            if value is not None:
                if field == "website_url":
                    update_data[field] = str(value)
                else:
                    update_data[field] = value
        
        logger.info(f"Updating application {app_id} with data: {update_data}")
        
        # Update application
        updated_app = await db.update_application(app_id, update_data)
        if not updated_app:
            logger.error(f"Failed to update application {app_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update application"
            )
        
        logger.info(f"Successfully updated application {app_id}")
        return {"message": "Application updated successfully", "application": updated_app}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating application {app_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.delete("/applications/{app_id}", response_model=dict)
async def delete_application(
    app_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete application"""
    db = await get_database()
    
    # Check if application exists and belongs to user
    application = await db.get_application_by_id(app_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = await db.delete_application(app_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete application"
        )
    
    return {"message": "Application deleted successfully"}

# Analysis run endpoints
@app.post("/applications/{app_id}/runs", response_model=dict)
async def start_analysis_run(
    app_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start a new analysis run"""
    db = await get_database()
    
    # Check if application exists and belongs to user
    application = await db.get_application_by_id(app_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Create analysis run
    run_dict = {
        "application_id": app_id,
        "status": AnalysisStatus.PENDING.value,
        "created_at": datetime.utcnow()
    }
    
    run_id = await db.create_analysis_run(run_dict)
    
    # Queue analysis task with Celery
    logger.info(f"Application data for analysis: {application}")
    app_data = {
        "website_url": application["website_url"],
        "max_crawl_depth": application["max_crawl_depth"],
        "max_pages_to_crawl": application["max_pages_to_crawl"],
        "max_links_to_validate": application["max_links_to_validate"],
        "enable_ai_evaluation": application["enable_ai_evaluation"],
        "max_ai_evaluation_pages": application["max_ai_evaluation_pages"],
        "extract_static_links": application.get("extract_static_links", True),
        "extract_dynamic_links": application.get("extract_dynamic_links", False),
        "extract_resource_links": application.get("extract_resource_links", False),
        "extract_external_links": application.get("extract_external_links", False),
        "name": application["name"],
        "user_email": current_user["email"],
        "send_notifications": False
    }
    
    task = run_website_analysis.delay(run_id, app_data)
    
    return {
        "message": "Analysis started", 
        "run_id": run_id,
        "task_id": task.id
    }

@app.get("/applications/{app_id}/runs", response_model=List[dict])
async def get_analysis_runs(
    app_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get analysis runs for an application"""
    db = await get_database()
    
    # Check if application exists and belongs to user
    application = await db.get_application_by_id(app_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    runs = await db.get_analysis_runs(app_id, limit)
    return runs

@app.get("/runs", response_model=List[dict])
async def get_all_analysis_runs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get all analysis runs for the current user with application details"""
    db = await get_database()
    
    # Get all analysis runs for the user
    runs = await db.get_all_analysis_runs_for_user(str(current_user["_id"]), limit)
    
    # Enhance runs with application details
    enhanced_runs = []
    for run in runs:
        application = await db.get_application_by_id(run["application_id"])
        enhanced_run = {
            **run,
            "application_name": application.get("name", "Unknown") if application else "Unknown",
            "website_url": application.get("website_url", "") if application else ""
        }
        enhanced_runs.append(enhanced_run)
    
    return enhanced_runs

@app.get("/runs/{run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific analysis run with results"""
    db = await get_database()
    
    # Get analysis run
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )
    
    # Check if application belongs to user
    application = await db.get_application_by_id(run["application_id"])
    if not application or application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get results
    results = await db.get_analysis_results(run_id)
    link_validations = await db.get_link_validations(run_id)
    change_detection = await db.get_change_detection(run_id)
    
    return AnalysisRunResponse(
        run=run,
        results=results,
        link_validations=link_validations,
        change_detection=change_detection
    )

@app.delete("/runs/{run_id}")
async def delete_analysis_run(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an analysis run and stop any running tasks"""
    db = await get_database()
    
    # Get analysis run
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )
    
    # Check if application belongs to user
    application = await db.get_application_by_id(run["application_id"])
    if not application or application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # If task is running, try to revoke it
    if run.get("status") == "running" and run.get("task_id"):
        try:
            from celery_app import celery_app
            celery_app.control.revoke(run["task_id"], terminate=True)
        except Exception as e:
            print(f"Failed to revoke task {run['task_id']}: {e}")
    
    # Delete the run and all related data
    success = await db.delete_analysis_run(run_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis run"
        )
    
    return {"message": "Analysis run deleted successfully"}

# Dashboard endpoint
@app.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    db = await get_database()
    stats = await db.get_dashboard_stats(current_user["_id"])
    return DashboardStats(**stats)

# Schedule endpoints
@app.post("/applications/{app_id}/schedules", response_model=dict)
async def create_schedule(
    app_id: str,
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new schedule"""
    db = await get_database()
    
    # Check if application exists and belongs to user
    application = await db.get_application_by_id(app_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Create schedule
    schedule_dict = {
        "application_id": app_id,
        "frequency": schedule_data.frequency.value,
        "cron_expression": schedule_data.cron_expression,
        "is_active": schedule_data.is_active,
        "next_run": schedule_data.next_run,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    schedule_id = await db.create_schedule(schedule_dict)
    return {"message": "Schedule created successfully", "schedule_id": schedule_id}

@app.get("/applications/{app_id}/schedules", response_model=List[dict])
async def get_schedules(
    app_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get schedules for an application"""
    db = await get_database()
    
    # Check if application exists and belongs to user
    application = await db.get_application_by_id(app_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    schedules = await db.get_application_schedules(app_id)
    return schedules

# Context comparison endpoint
@app.get("/runs/{run_id}/context-comparison", response_model=ContextComparison)
async def get_context_comparison(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get context comparison for a run"""
    db = await get_database()
    
    # Get analysis run
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )
    
    # Check if application belongs to user
    application = await db.get_application_by_id(run["application_id"])
    if not application or application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get change detection
    change_detection = await db.get_change_detection(run_id)
    
    if change_detection:
        return ContextComparison(
            current_run_id=run_id,
            previous_run_id=change_detection.get("previous_run_id"),
            similarity_score=change_detection.get("similarity_score"),
            changes_detected=change_detection.get("changes_summary", {}),
            new_pages=change_detection.get("new_pages", []),
            removed_pages=change_detection.get("removed_pages", []),
            modified_pages=change_detection.get("modified_pages", [])
        )
    else:
        return ContextComparison(
            current_run_id=run_id,
            previous_run_id=None,
            similarity_score=None,
            changes_detected=[],
            new_pages=[],
            removed_pages=[],
            modified_pages=[]
        )

@app.post("/runs/{run_id}/content-analysis")
async def run_content_analysis(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Run AI-powered content analysis on a specific run"""
    db = await get_database()
    
    # Get analysis run
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )
    
    # Check if application belongs to user
    application = await db.get_application_by_id(run["application_id"])
    if not application or application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Queue content analysis task
    from celery_tasks import run_content_analysis
    task = run_content_analysis.delay(run_id)
    
    return {
        "message": "Content analysis started",
        "task_id": task.id,
        "run_id": run_id
    }

@app.get("/runs/{run_id}/content-analysis/{task_id}")
async def get_content_analysis_status(
    run_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of content analysis task"""
    db = await get_database()
    
    # Get analysis run
    run = await db.get_analysis_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found"
        )
    
    # Check if application belongs to user
    application = await db.get_application_by_id(run["application_id"])
    if not application or application["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get task status
    from celery_app import celery_app
    task = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None,
        "ready": task.ready()
    }

@app.get("/runs/{run_id}/content-comparison/{previous_run_id}")
async def get_content_comparison(
    run_id: str,
    previous_run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get AI-powered content comparison between two runs"""
    db = await get_database()
    
    # Get both analysis runs
    current_run = await db.get_analysis_run_by_id(run_id)
    previous_run = await db.get_analysis_run_by_id(previous_run_id)
    
    if not current_run or not previous_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both analysis runs not found"
        )
    
    # Check if applications belong to user
    current_app = await db.get_application_by_id(current_run["application_id"])
    previous_app = await db.get_application_by_id(previous_run["application_id"])
    
    if (not current_app or current_app["user_id"] != str(current_user["_id"]) or
        not previous_app or previous_app["user_id"] != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get content comparison data
    comparison_data = await db.get_content_comparison(run_id, previous_run_id)
    
    return {
        "current_run_id": run_id,
        "previous_run_id": previous_run_id,
        "comparison": comparison_data,
        "status": "success"
    }

# Task status endpoints
@app.get("/tasks/{task_id}/status")
async def get_task_status_endpoint(task_id: str):
    """Get status of a Celery task"""
    try:
        from celery_app import celery_app
        task = celery_app.AsyncResult(task_id)
        
        # Handle different task states with comprehensive error handling
        task_status = "UNKNOWN"
        task_result = None
        task_info = None
        is_ready = False
        is_successful = False
        is_failed = False
        
        try:
            # Get basic task status
            task_status = task.status or "UNKNOWN"
        except Exception as status_error:
            task_status = "ERROR"
            task_info = f"Status error: {str(status_error)}"
        
        try:
            is_ready = task.ready()
        except Exception as ready_error:
            is_ready = False
            task_info = f"Ready check error: {str(ready_error)}"
        
        if is_ready:
            try:
                is_successful = task.successful()
                is_failed = task.failed()
            except Exception as success_error:
                is_successful = False
                is_failed = True
                task_info = f"Success check error: {str(success_error)}"
            
            try:
                task_result = task.result
            except Exception as result_error:
                task_result = None
                task_info = f"Result access error: {str(result_error)}"
        
        # Safely get task info
        try:
            if not task_info:  # Only get info if we don't already have an error message
                task_info = task.info
        except Exception as info_error:
            if not task_info:  # Only set if we don't already have an error message
                task_info = f"Info access error: {str(info_error)}"
        
        return {
            "task_id": task_id,
            "status": task_status,
            "result": task_result,
            "info": task_info,
            "ready": is_ready,
            "successful": is_successful,
            "failed": is_failed
        }
    except Exception as e:
        # Return a more informative error response
        return {
            "task_id": task_id,
            "status": "ERROR",
            "result": None,
            "info": f"Task lookup error: {str(e)}",
            "ready": False,
            "successful": False,
            "failed": True,
            "error": str(e)
        }

@app.get("/tasks/workers/stats")
async def get_worker_stats():
    """Get Celery worker statistics"""
    try:
        from celery_tasks import get_worker_stats
        result = get_worker_stats.delay()
        stats = result.get(timeout=10)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get worker stats: {str(e)}"
        )

# User verification endpoint
@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user["_id"]),  # Convert ObjectId to string
        "email": current_user["email"],
        "name": current_user["name"],
        "role": current_user["role"]
    }

# Enhanced link analysis endpoints
@app.get("/runs/{run_id}/broken-links/details", response_model=dict)
async def get_broken_link_details(
    run_id: str,
    broken_url: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Get detailed information about a broken link including parent and source code"""
    try:
        # Decode the URL parameter (it comes URL-encoded from the frontend)
        decoded_broken_url = unquote(broken_url)
        logger.info(f"Original broken_url: {broken_url}")
        logger.info(f"Decoded broken_url: {decoded_broken_url}")
        
        # Verify the run belongs to the user
        run = await db.get_analysis_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Check if application belongs to user
        application = await db.get_application_by_id(run["application_id"])
        if not application or application["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get broken link with parent info using the decoded URL
        broken_link_info = await db.get_broken_link_with_parent_info(run_id, decoded_broken_url)
        if not broken_link_info:
            raise HTTPException(status_code=404, detail="Broken link not found")
        
        # Get parent page title if available
        if broken_link_info["parent_url"]:
            parent_page = await db.get_page_data_by_url(run_id, broken_link_info["parent_url"])
            if parent_page:
                broken_link_info["parent_title"] = parent_page.get("page_title")
        
        # Get navigation path
        relationships = await db.get_parent_child_relationships(run_id)
        navigation_path = []
        if relationships and "path_map" in relationships:
            navigation_path = relationships["path_map"].get(broken_url, [])
        
        broken_link_info["navigation_path"] = navigation_path
        
        return broken_link_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting broken link details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/runs/{run_id}/source-code", response_model=SourceCodeResponse)
async def get_page_source_code(
    run_id: str,
    page_url: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Get HTML source code for a page with highlighted links"""
    try:
        # Decode the URL parameter (it comes URL-encoded from the frontend)
        decoded_page_url = unquote(page_url)
        logger.info(f"Original page_url: {page_url}")
        logger.info(f"Decoded page_url: {decoded_page_url}")
        
        # Verify the run belongs to the user
        run = await db.get_analysis_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Check if application belongs to user
        application = await db.get_application_by_id(run["application_id"])
        if not application or application["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get source code using the decoded URL
        logger.info(f"Looking for source code for run_id: {run_id}, page_url: {decoded_page_url}")
        source_data = await db.get_page_source_code(run_id, decoded_page_url)
        
        # If source code not found, try to get it from parent page (for broken links)
        if not source_data:
            logger.warning(f"Source code not found for run_id: {run_id}, page_url: {decoded_page_url}")
            
            # Get parent-child relationships to find the parent page
            relationships = await db.get_parent_child_relationships(run_id)
            if relationships and "parent_map" in relationships:
                parent_url = relationships["parent_map"].get(decoded_page_url)
                if parent_url:
                    logger.info(f"Trying to get source code from parent page: {parent_url}")
                    source_data = await db.get_page_source_code(run_id, parent_url)
                    if source_data:
                        # Update the page_url to show the broken link URL but use parent's source code
                        source_data["page_url"] = decoded_page_url
                        source_data["parent_url"] = parent_url
                        logger.info(f"Found source code from parent page: {parent_url}")
            
            if not source_data:
                raise HTTPException(status_code=404, detail="Source code not found")
        
        # Get only broken links for this specific page to highlight them
        all_links = await db.get_link_validations(run_id)
        broken_links = [link for link in all_links if link["status"] == "broken"]
        
        # Only highlight broken links in source code
        highlighted_links = []
        source_code = source_data["source_code"]
        
        # Highlight only broken links in red
        for link in broken_links:
            url = link["url"]
            if url in source_code:
                start = 0
                while True:
                    pos = source_code.find(url, start)
                    if pos == -1:
                        break
                    highlighted_links.append({
                        "url": url,
                        "start": pos,
                        "end": pos + len(url),
                        "type": "broken",
                        "status_code": link.get("status_code"),
                        "status": link["status"]
                    })
                    start = pos + 1
        
        return SourceCodeResponse(
            page_url=decoded_page_url,
            source_code=source_code,
            parent_url=source_data.get("parent_url"),
            highlighted_links=[HighlightedLink(**link) for link in highlighted_links],
            created_at=source_data.get("created_at"),
            actual_source_page=source_data.get("actual_source_page", decoded_page_url),
            is_source_from_parent=source_data.get("actual_source_page") != decoded_page_url,
            traversal_path=source_data.get("traversal_path", [decoded_page_url]),
            hierarchy_depth=source_data.get("hierarchy_depth", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page source code: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/runs/{run_id}/parent-child-relationships", response_model=ParentChildRelationships)
async def get_parent_child_relationships(
    run_id: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Get parent-child relationships for a run"""
    try:
        # Verify the run belongs to the user
        run = await db.get_analysis_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Check if application belongs to user
        application = await db.get_application_by_id(run["application_id"])
        if not application or application["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get relationships
        relationships = await db.get_parent_child_relationships(run_id)
        if not relationships:
            return ParentChildRelationships()
        
        return ParentChildRelationships(**relationships)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parent-child relationships: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# JSON Export endpoint
@app.post("/runs/{run_id}/export-json", response_model=dict)
async def export_analysis_results_to_json(
    run_id: str,
    current_user: dict = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Export complete analysis results to JSON file for debugging and verification"""
    try:
        # Verify the run belongs to the user
        run = await db.get_analysis_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Analysis run not found")
        
        # Check if application belongs to user
        application = await db.get_application_by_id(run["application_id"])
        if not application or application["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Export to JSON
        filepath = await db.export_analysis_results_to_json(run_id)
        
        return {
            "message": "Analysis results exported successfully",
            "filepath": filepath,
            "run_id": run_id,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analysis results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation"""
    return """
    <html>
        <head>
            <title>Website Analysis Platform</title>
        </head>
        <body>
            <h1>Website Analysis Platform API</h1>
            <p>Welcome to the Website Analysis Platform API!</p>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation.</p>
            <p>Visit <a href="/redoc">/redoc</a> for alternative API documentation.</p>
        </body>
    </html>
    """

# Celery task integration is now handled in celery_tasks.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
