"""
AI-Powered Content Analysis Engine
"""

import openai
import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ai_models import AIAnalysisResult, ContentQualityScore, SEOAnalysis, UserExperienceAnalysis, TechnicalAnalysis
from config import settings

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """AI-powered content analysis using OpenAI API"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 1500):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        openai.api_key = self.api_key
    
    async def analyze_page_content(self, page_data: Dict[str, Any]) -> AIAnalysisResult:
        """
        Analyze a single page's content using AI
        
        Args:
            page_data: Dictionary containing page information and content
            
        Returns:
            AIAnalysisResult: Structured analysis results
        """
        start_time = time.time()
        
        try:
            # Prepare content for analysis
            content_text = page_data.get("text_content", "")
            html_structure = page_data.get("html_structure", {})
            page_url = page_data.get("page_url", "Unknown")
            page_title = page_data.get("page_title", "No title")
            word_count = page_data.get("word_count", 0)
            page_type = page_data.get("page_type", "unknown")
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                page_url, page_title, word_count, page_type, 
                content_text, html_structure
            )
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse and structure the response
            analysis_result = self._parse_ai_response(
                response, page_url, page_title, word_count, page_type
            )
            
            # Add processing metadata
            processing_time = time.time() - start_time
            analysis_result.processing_time = processing_time
            analysis_result.raw_ai_response = response
            
            logger.info(f"Successfully analyzed {page_url} in {processing_time:.2f}s")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing page {page_data.get('page_url', 'unknown')}: {e}")
            
            # Return error result
            return AIAnalysisResult(
                page_url=page_data.get("page_url", "Unknown"),
                page_title=page_data.get("page_title", "No title"),
                word_count=page_data.get("word_count", 0),
                page_type=page_data.get("page_type", "unknown"),
                content_quality=ContentQualityScore(
                    score=0,
                    assessment=f"Analysis failed: {str(e)}",
                    strengths=[],
                    weaknesses=["Analysis failed due to technical error"]
                ),
                seo_analysis=SEOAnalysis(
                    title_quality="Analysis failed",
                    content_relevance="Analysis failed",
                    keyword_density="Analysis failed",
                    recommendations=["Fix technical issues and retry analysis"]
                ),
                user_experience=UserExperienceAnalysis(
                    readability="Analysis failed",
                    structure="Analysis failed",
                    navigation="Analysis failed",
                    improvements=["Fix technical issues and retry analysis"]
                ),
                technical_analysis=TechnicalAnalysis(
                    html_structure="Analysis failed",
                    accessibility="Analysis failed",
                    performance_impact="Analysis failed"
                ),
                overall_recommendations=["Fix technical issues and retry analysis"],
                raw_ai_response=f"Error: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def analyze_multiple_pages(self, pages_data: List[Dict[str, Any]]) -> List[AIAnalysisResult]:
        """
        Analyze multiple pages' content
        
        Args:
            pages_data: List of page data dictionaries
            
        Returns:
            List[AIAnalysisResult]: List of analysis results
        """
        results = []
        
        for i, page_data in enumerate(pages_data):
            try:
                logger.info(f"Analyzing page {i+1}/{len(pages_data)}: {page_data.get('page_url', 'Unknown')}")
                result = await self.analyze_page_content(page_data)
                results.append(result)
                
                # Add small delay to avoid rate limiting
                if i < len(pages_data) - 1:
                    import asyncio
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Failed to analyze page {page_data.get('page_url', 'unknown')}: {e}")
                continue
        
        return results
    
    def _create_analysis_prompt(self, url: str, title: str, word_count: int, 
                              page_type: str, content: str, html_structure: Dict) -> str:
        """Create a comprehensive analysis prompt for OpenAI"""
        
        # Limit content to avoid token limits
        content_preview = content[:3000] if content else "No content available"
        structure_preview = str(html_structure)[:1000] if html_structure else "No structure data"
        
        prompt = f"""
You are an expert web content analyst. Analyze the following webpage and provide detailed, actionable insights.

WEBPAGE INFORMATION:
- URL: {url}
- Title: {title}
- Word Count: {word_count}
- Page Type: {page_type}

CONTENT:
{content_preview}

HTML STRUCTURE:
{structure_preview}

Please provide a comprehensive analysis in the following JSON format:

{{
    "content_quality": {{
        "score": 85,
        "assessment": "Brief assessment of overall content quality",
        "strengths": ["strength1", "strength2", "strength3"],
        "weaknesses": ["weakness1", "weakness2"]
    }},
    "seo_analysis": {{
        "title_quality": "Assessment of page title quality and SEO optimization",
        "content_relevance": "How well content matches the page purpose",
        "keyword_density": "Analysis of keyword usage and density",
        "recommendations": ["seo_rec1", "seo_rec2", "seo_rec3"]
    }},
    "user_experience": {{
        "readability": "Assessment of content readability and clarity",
        "structure": "Evaluation of page structure and organization",
        "navigation": "Assessment of navigation and user flow",
        "improvements": ["ux_improvement1", "ux_improvement2"]
    }},
    "technical_analysis": {{
        "html_structure": "Assessment of HTML structure and semantic markup",
        "accessibility": "Evaluation of accessibility features and compliance",
        "performance_impact": "Assessment of content's impact on page performance"
    }},
    "overall_recommendations": ["rec1", "rec2", "rec3", "rec4", "rec5"]
}}

IMPORTANT GUIDELINES:
1. Be specific and actionable in your recommendations
2. Consider the page type and purpose in your analysis
3. Focus on practical improvements that can be implemented
4. Provide scores and assessments that are realistic and helpful
5. Ensure all JSON is properly formatted and valid
6. Keep recommendations concise but informative
"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with the analysis prompt"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert web content analyst. Provide detailed, actionable insights about webpage content quality, SEO, and user experience. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _parse_ai_response(self, response: str, url: str, title: str, 
                          word_count: int, page_type: str) -> AIAnalysisResult:
        """Parse AI response and create structured result"""
        try:
            # Try to parse JSON response
            ai_data = json.loads(response)
            
            # Extract analysis components
            content_quality = ContentQualityScore(**ai_data.get("content_quality", {}))
            seo_analysis = SEOAnalysis(**ai_data.get("seo_analysis", {}))
            user_experience = UserExperienceAnalysis(**ai_data.get("user_experience", {}))
            technical_analysis = TechnicalAnalysis(**ai_data.get("technical_analysis", {}))
            overall_recommendations = ai_data.get("overall_recommendations", [])
            
            return AIAnalysisResult(
                page_url=url,
                page_title=title,
                word_count=word_count,
                page_type=page_type,
                content_quality=content_quality,
                seo_analysis=seo_analysis,
                user_experience=user_experience,
                technical_analysis=technical_analysis,
                overall_recommendations=overall_recommendations,
                raw_ai_response=response
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            
            # Return fallback result with raw response
            return AIAnalysisResult(
                page_url=url,
                page_title=title,
                word_count=word_count,
                page_type=page_type,
                content_quality=ContentQualityScore(
                    score=50,
                    assessment="AI response parsing failed",
                    strengths=[],
                    weaknesses=["Unable to parse AI analysis"]
                ),
                seo_analysis=SEOAnalysis(
                    title_quality="Analysis parsing failed",
                    content_relevance="Analysis parsing failed",
                    keyword_density="Analysis parsing failed",
                    recommendations=["Retry analysis or check AI response format"]
                ),
                user_experience=UserExperienceAnalysis(
                    readability="Analysis parsing failed",
                    structure="Analysis parsing failed",
                    navigation="Analysis parsing failed",
                    improvements=["Retry analysis or check AI response format"]
                ),
                technical_analysis=TechnicalAnalysis(
                    html_structure="Analysis parsing failed",
                    accessibility="Analysis parsing failed",
                    performance_impact="Analysis parsing failed"
                ),
                overall_recommendations=["Retry analysis or check AI response format"],
                raw_ai_response=response
            )
        
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise
