from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class LinkStatus(str, Enum):
    VALID = "valid"
    BROKEN = "broken"
    REDIRECT = "redirect"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"

class PageType(str, Enum):
    CONTENT = "content"
    BLANK = "blank"
    ERROR = "error"
    REDIRECT = "redirect"

class EvaluationType(str, Enum):
    CONTENT_QUALITY = "content_quality"
    DESIGN_ISSUES = "design_issues"
    ACCESSIBILITY = "accessibility"
    SEO = "seo"
    TECHNICAL = "technical"

class Link(BaseModel):
    url: str
    status_code: Optional[int] = None
    status: LinkStatus = LinkStatus.UNKNOWN
    title: Optional[str] = None
    depth: int = 0
    parent_url: Optional[str] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    discovered_at: datetime = datetime.now()

class PageContent(BaseModel):
    url: str
    title: Optional[str] = None
    html_content: str
    markdown_content: Optional[str] = None
    text_content: str
    word_count: int
    page_type: PageType = PageType.CONTENT
    has_header: bool = False
    has_footer: bool = False
    has_navigation: bool = False
    content_chunks: List[str] = []
    extracted_at: datetime = datetime.now()
    
    # New fields for path tracking and HTML structure
    path: List[str] = []  # Click path to reach this page
    crawled_at: Optional[str] = None  # When this page was crawled
    session_id: Optional[str] = None  # Crawl session ID
    html_structure: Optional[Dict[str, Any]] = None  # Extracted HTML structure

class EvaluationResult(BaseModel):
    url: str
    evaluation_type: EvaluationType
    score: float  # 0-100
    issues: List[str] = []
    recommendations: List[str] = []
    details: Dict[str, Any] = {}
    evaluated_at: datetime = datetime.now()
    evaluator_agent: str

class WebsiteAnalysis(BaseModel):
    base_url: str
    total_pages: int = 0
    total_links: int = 0
    broken_links: int = 0
    blank_pages: int = 0
    pages: List[PageContent] = []
    links: List[Link] = []
    evaluations: List[EvaluationResult] = []
    analysis_started_at: datetime = datetime.now()
    analysis_completed_at: Optional[datetime] = None
    overall_score: Optional[float] = None
