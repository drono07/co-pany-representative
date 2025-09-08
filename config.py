import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    max_crawl_depth: int = int(os.getenv("MAX_CRAWL_DEPTH", "3"))
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "2"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    user_agent: str = os.getenv("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # AI Evaluation Settings
    enable_ai_evaluation: bool = os.getenv("ENABLE_AI_EVALUATION", "false").lower() == "true"
    max_ai_evaluation_pages: int = int(os.getenv("MAX_AI_EVALUATION_PAGES", "10"))
    
    # Non-AI Analysis Settings (always run for all pages)
    enable_link_validation: bool = os.getenv("ENABLE_LINK_VALIDATION", "true").lower() == "true"
    enable_blank_page_detection: bool = os.getenv("ENABLE_BLANK_PAGE_DETECTION", "true").lower() == "true"
    enable_content_analysis: bool = os.getenv("ENABLE_CONTENT_ANALYSIS", "true").lower() == "true"
    
    # Crawling Limits (for testing and performance control)
    max_pages_to_crawl: int = int(os.getenv("MAX_PAGES_TO_CRAWL", "50"))  # Limit total pages crawled
    max_links_to_validate: int = int(os.getenv("MAX_LINKS_TO_VALIDATE", "100"))  # Limit total links validated
    
    class Config:
        env_file = ".env"

settings = Settings()
