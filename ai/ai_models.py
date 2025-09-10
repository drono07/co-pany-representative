"""
AI Analysis Data Models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    CONTENT_QUALITY = "content_quality"
    SEO_ANALYSIS = "seo_analysis"
    USER_EXPERIENCE = "user_experience"
    TECHNICAL_ANALYSIS = "technical_analysis"
    ACCESSIBILITY = "accessibility"

class ContentQualityScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Content quality score (0-100)")
    assessment: str = Field(..., description="Brief assessment of content quality")
    strengths: List[str] = Field(default_factory=list, description="Content strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Content weaknesses")

class SEOAnalysis(BaseModel):
    title_quality: str = Field(..., description="Assessment of page title quality")
    content_relevance: str = Field(..., description="Content relevance assessment")
    keyword_density: str = Field(..., description="Keyword density analysis")
    recommendations: List[str] = Field(default_factory=list, description="SEO recommendations")

class UserExperienceAnalysis(BaseModel):
    readability: str = Field(..., description="Content readability assessment")
    structure: str = Field(..., description="Page structure assessment")
    navigation: str = Field(..., description="Navigation assessment")
    improvements: List[str] = Field(default_factory=list, description="UX improvement suggestions")

class TechnicalAnalysis(BaseModel):
    html_structure: str = Field(..., description="HTML structure assessment")
    accessibility: str = Field(..., description="Accessibility assessment")
    performance_impact: str = Field(..., description="Performance impact assessment")

class AIAnalysisResult(BaseModel):
    page_url: str = Field(..., description="URL of the analyzed page")
    page_title: str = Field(..., description="Title of the analyzed page")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = Field(..., description="Word count of the page")
    page_type: str = Field(..., description="Type of page (content, product, etc.)")
    
    # AI Analysis Results
    content_quality: ContentQualityScore = Field(..., description="Content quality analysis")
    seo_analysis: SEOAnalysis = Field(..., description="SEO analysis results")
    user_experience: UserExperienceAnalysis = Field(..., description="User experience analysis")
    technical_analysis: TechnicalAnalysis = Field(..., description="Technical analysis results")
    overall_recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")
    
    # Raw AI Response
    raw_ai_response: Optional[str] = Field(None, description="Raw AI response for debugging")
    ai_model: str = Field(default="gpt-3.5-turbo", description="AI model used for analysis")
    processing_time: Optional[float] = Field(None, description="Time taken to process (seconds)")

class ContentChange(BaseModel):
    url: str = Field(..., description="URL of the changed page")
    title: str = Field(..., description="Page title")
    change_type: str = Field(..., description="Type of change (new, removed, modified)")
    word_count_change: int = Field(default=0, description="Change in word count")
    content_changed: bool = Field(default=False, description="Whether content changed")
    ai_analysis_changed: bool = Field(default=False, description="Whether AI analysis changed")
    change_summary: Optional[str] = Field(None, description="AI-generated change summary")

class ContentComparisonResult(BaseModel):
    comparison_timestamp: datetime = Field(default_factory=datetime.utcnow)
    current_run_id: str = Field(..., description="Current analysis run ID")
    previous_run_id: str = Field(..., description="Previous analysis run ID")
    
    # Change Detection
    new_pages: List[str] = Field(default_factory=list, description="URLs of new pages")
    removed_pages: List[str] = Field(default_factory=list, description="URLs of removed pages")
    modified_pages: List[ContentChange] = Field(default_factory=list, description="Modified pages with details")
    
    # Summary Statistics
    total_pages_compared: int = Field(..., description="Total number of pages compared")
    changes_summary: Dict[str, int] = Field(..., description="Summary of changes")
    
    # AI-Generated Insights
    overall_change_assessment: Optional[str] = Field(None, description="AI assessment of overall changes")
    impact_analysis: Optional[str] = Field(None, description="AI analysis of change impact")
    recommendations: List[str] = Field(default_factory=list, description="AI recommendations based on changes")
    
    # Technical Details
    ai_model: str = Field(default="gpt-3.5-turbo", description="AI model used for comparison")
    processing_time: Optional[float] = Field(None, description="Time taken to process comparison")

class AIAnalysisRequest(BaseModel):
    run_id: str = Field(..., description="Analysis run ID")
    page_urls: Optional[List[str]] = Field(None, description="Specific pages to analyze (if None, analyze all)")
    analysis_types: List[AnalysisType] = Field(default_factory=lambda: list(AnalysisType), description="Types of analysis to perform")
    ai_model: str = Field(default="gpt-3.5-turbo", description="AI model to use")
    max_tokens: int = Field(default=1500, description="Maximum tokens for AI response")

class ContentComparisonRequest(BaseModel):
    current_run_id: str = Field(..., description="Current analysis run ID")
    previous_run_id: str = Field(..., description="Previous analysis run ID")
    include_ai_insights: bool = Field(default=True, description="Whether to include AI-generated insights")
    ai_model: str = Field(default="gpt-3.5-turbo", description="AI model to use for comparison")
