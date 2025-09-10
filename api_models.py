"""
Pydantic models for FastAPI website analysis platform
"""

from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

# User Models
class UserBase(BaseModel):
    email: str
    name: str
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True

# Application Models
class ApplicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    website_url: HttpUrl
    max_crawl_depth: int = Field(default=1, ge=1, le=5)  # Default: 1 for performance
    max_pages_to_crawl: int = Field(default=500, ge=10, le=1000)  # Default: 500 pages
    max_links_to_validate: int = Field(default=1500, ge=10, le=2000)  # Default: 1500 links (3x pages)
    enable_ai_evaluation: bool = False
    max_ai_evaluation_pages: int = Field(default=10, ge=1, le=50)
    
    # Link extraction configuration
    extract_static_links: bool = Field(default=True, description="Extract links from static HTML (a, link, area tags)")
    extract_dynamic_links: bool = Field(default=False, description="Extract links from JavaScript (onclick, data attributes, script content)")
    extract_resource_links: bool = Field(default=False, description="Extract resource links (images, CSS, JS files)")
    extract_external_links: bool = Field(default=False, description="Extract links to external domains")
    
    @field_validator('max_links_to_validate')
    @classmethod
    def validate_links_to_pages_ratio(cls, v, info):
        """Validate that max_links_to_validate is 2-3x max_pages_to_crawl"""
        if info.data and 'max_pages_to_crawl' in info.data:
            pages = info.data['max_pages_to_crawl']
            if v < pages * 2:
                raise ValueError(f'max_links_to_validate ({v}) should be at least 2x max_pages_to_crawl ({pages})')
            if v > pages * 5:
                raise ValueError(f'max_links_to_validate ({v}) should not exceed 5x max_pages_to_crawl ({pages})')
        return v

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    max_crawl_depth: Optional[int] = Field(None, ge=1, le=5)
    max_pages_to_crawl: Optional[int] = Field(None, ge=10, le=1000)
    max_links_to_validate: Optional[int] = Field(None, ge=10, le=2000)
    enable_ai_evaluation: Optional[bool] = None
    max_ai_evaluation_pages: Optional[int] = Field(None, ge=1, le=50)

class Application(ApplicationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True

# Schedule Models
class ScheduleBase(BaseModel):
    application_id: str
    frequency: ScheduleFrequency
    cron_expression: Optional[str] = None  # For custom schedules
    is_active: bool = True
    next_run: Optional[datetime] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    frequency: Optional[ScheduleFrequency] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    next_run: Optional[datetime] = None

class Schedule(ScheduleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Analysis Run Models
class AnalysisRunBase(BaseModel):
    application_id: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class AnalysisRunCreate(AnalysisRunBase):
    pass

class AnalysisRun(AnalysisRunBase):
    id: str
    created_at: datetime
    
    # Analysis results
    total_pages_analyzed: Optional[int] = None
    total_links_found: Optional[int] = None
    broken_links_count: Optional[int] = None
    blank_pages_count: Optional[int] = None
    content_pages_count: Optional[int] = None
    overall_score: Optional[float] = None
    
    class Config:
        from_attributes = True

# Analysis Result Models
class AnalysisResultBase(BaseModel):
    run_id: str
    page_url: str
    page_title: Optional[str] = None
    word_count: int
    page_type: str  # content, blank, error, redirect
    has_header: bool = False
    has_footer: bool = False
    has_navigation: bool = False
    html_structure: Optional[Dict[str, Any]] = None
    path: List[str] = []
    crawled_at: Optional[datetime] = None

class AnalysisResult(AnalysisResultBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Link Validation Models
class LinkValidationBase(BaseModel):
    run_id: str
    url: str
    status_code: Optional[int] = None
    status: str  # valid, broken, redirect, timeout, rate_limited, unknown
    response_time: Optional[float] = None
    error_message: Optional[str] = None

class LinkValidation(LinkValidationBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Change Detection Models
class ChangeDetectionBase(BaseModel):
    run_id: str
    previous_run_id: Optional[str] = None
    new_pages_count: int = 0
    removed_pages_count: int = 0
    modified_pages_count: int = 0
    unchanged_pages_count: int = 0
    changes_summary: Dict[str, Any] = {}

class ChangeDetection(ChangeDetectionBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# API Response Models
class AnalysisRunResponse(BaseModel):
    run: AnalysisRun
    results: List[AnalysisResult]
    link_validations: List[LinkValidation]
    change_detection: Optional[ChangeDetection] = None

class DashboardStats(BaseModel):
    total_applications: int
    total_runs: int
    active_schedules: int
    recent_runs: List[AnalysisRun]
    top_issues: Dict[str, int]

class ContextComparison(BaseModel):
    current_run_id: str
    previous_run_id: Optional[str] = None
    similarity_score: Optional[float] = None
    changes_detected: List[Dict[str, Any]]
    new_pages: List[str]
    removed_pages: List[str]
    modified_pages: List[str]

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[dict] = None

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# Source Code Models
class HighlightedLink(BaseModel):
    url: str
    start: int
    end: int
    type: str  # "broken", "valid", etc.
    status_code: Optional[int] = None
    status: str

class SourceCodeResponse(BaseModel):
    page_url: str
    source_code: str
    parent_url: Optional[str] = None
    highlighted_links: List[HighlightedLink] = []
    created_at: Optional[datetime] = None
    actual_source_page: str  # Which page actually has the source
    is_source_from_parent: bool  # Whether source is from parent
    traversal_path: List[str]  # Path taken to find source
    hierarchy_depth: int  # How many levels up we went

# Parent-Child Relationship Models
class ParentChildRelationships(BaseModel):
    parent_map: Dict[str, str] = {}  # child_url -> parent_url
    children_map: Dict[str, List[str]] = {}  # parent_url -> [child_urls]
    path_map: Dict[str, List[str]] = {}  # url -> [path_to_root]
