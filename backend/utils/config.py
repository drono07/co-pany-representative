"""
Configuration settings for Website Insights Platform

IMPORTANT: When using the frontend, you only need minimal .env settings!
- Essential: OPENAI_API_KEY, MONGODB_URI, ENABLE_MONGODB_STORAGE
- Optional: Crawler performance settings (MAX_CRAWL_DEPTH, etc.)
- Local testing: Analysis settings (only when running main.py directly)

All analysis parameters (crawl depth, page limits, etc.) come from the frontend UI.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # =============================================================================
    # PRODUCTION SETTINGS (Always Required)
    # =============================================================================
    
    # OpenAI API Key (Required for AI evaluation)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database Settings (Required for production)
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/website_analysis_platform")
    enable_mongodb_storage: bool = os.getenv("ENABLE_MONGODB_STORAGE", "true").lower() == "true"
    
    # =============================================================================
    # CRAWLER SETTINGS (Used by crawler.py and validators.py)
    # =============================================================================
    
    # Crawler Performance Settings
    max_crawl_depth: int = int(os.getenv("MAX_CRAWL_DEPTH", "1"))  # Shallow crawl for performance
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "100"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    user_agent: str = os.getenv("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # =============================================================================
    # LOCAL TESTING SETTINGS (Only used when running main.py directly)
    # =============================================================================
    # NOTE: In production, these values come from the frontend through API calls
    # These are fallback defaults for local testing and development
    
    # AI Evaluation Settings (for local testing)
    enable_ai_evaluation: bool = os.getenv("ENABLE_AI_EVALUATION", "false").lower() == "true"
    max_ai_evaluation_pages: int = int(os.getenv("MAX_AI_EVALUATION_PAGES", "10"))
    
    # Analysis Settings (for local testing)
    enable_link_validation: bool = os.getenv("ENABLE_LINK_VALIDATION", "true").lower() == "true"
    enable_blank_page_detection: bool = os.getenv("ENABLE_BLANK_PAGE_DETECTION", "true").lower() == "true"
    enable_content_analysis: bool = os.getenv("ENABLE_CONTENT_ANALYSIS", "true").lower() == "true"
    
    # Crawling Limits (for local testing - overridden by frontend in production)
    max_pages_to_crawl: int = int(os.getenv("MAX_PAGES_TO_CRAWL", "500"))  # Default: 500 pages
    max_links_to_validate: int = int(os.getenv("MAX_LINKS_TO_VALIDATE", "1500"))  # Default: 1500 links (3x pages for comprehensive validation)
    
    class Config:
        env_file = ".env"

settings = Settings()
