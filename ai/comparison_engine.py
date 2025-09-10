"""
AI-Powered Content Comparison Engine
"""

import openai
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ai_models import ContentComparisonResult, ContentChange, AIAnalysisResult
from config import settings

logger = logging.getLogger(__name__)

class ComparisonEngine:
    """AI-powered content comparison between analysis runs"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 2000):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        openai.api_key = self.api_key
    
    async def compare_analysis_runs(self, current_analysis: Dict[str, Any], 
                                  previous_analysis: Dict[str, Any]) -> ContentComparisonResult:
        """
        Compare two analysis runs and generate AI insights
        
        Args:
            current_analysis: Current run analysis data
            previous_analysis: Previous run analysis data
            
        Returns:
            ContentComparisonResult: Comprehensive comparison results
        """
        start_time = time.time()
        
        try:
            # Extract analysis results
            current_results = current_analysis.get("analysis_results", [])
            previous_results = previous_analysis.get("analysis_results", [])
            
            # Perform basic comparison
            basic_comparison = self._perform_basic_comparison(current_results, previous_results)
            
            # Generate AI insights if requested
            ai_insights = await self._generate_ai_insights(
                current_results, previous_results, basic_comparison
            )
            
            # Create comprehensive result
            result = ContentComparisonResult(
                current_run_id=current_analysis.get("run_id"),
                previous_run_id=previous_analysis.get("run_id"),
                new_pages=basic_comparison["new_pages"],
                removed_pages=basic_comparison["removed_pages"],
                modified_pages=basic_comparison["modified_pages"],
                total_pages_compared=basic_comparison["total_pages_compared"],
                changes_summary=basic_comparison["changes_summary"],
                overall_change_assessment=ai_insights.get("overall_assessment"),
                impact_analysis=ai_insights.get("impact_analysis"),
                recommendations=ai_insights.get("recommendations", []),
                processing_time=time.time() - start_time
            )
            
            logger.info(f"Successfully compared runs {current_analysis.get('run_id')} and {previous_analysis.get('run_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Error comparing analysis runs: {e}")
            
            # Return basic comparison without AI insights
            basic_comparison = self._perform_basic_comparison(
                current_analysis.get("analysis_results", []),
                previous_analysis.get("analysis_results", [])
            )
            
            return ContentComparisonResult(
                current_run_id=current_analysis.get("run_id"),
                previous_run_id=previous_analysis.get("run_id"),
                new_pages=basic_comparison["new_pages"],
                removed_pages=basic_comparison["removed_pages"],
                modified_pages=basic_comparison["modified_pages"],
                total_pages_compared=basic_comparison["total_pages_compared"],
                changes_summary=basic_comparison["changes_summary"],
                overall_change_assessment=f"Comparison completed with errors: {str(e)}",
                impact_analysis="Unable to generate AI insights due to technical error",
                recommendations=["Fix technical issues and retry comparison"],
                processing_time=time.time() - start_time
            )
    
    def _perform_basic_comparison(self, current_results: List[Dict], 
                                previous_results: List[Dict]) -> Dict[str, Any]:
        """Perform basic comparison between two analysis result sets"""
        
        # Create URL maps for comparison
        current_pages = {page["page_url"]: page for page in current_results}
        previous_pages = {page["page_url"]: page for page in previous_results}
        
        # Find new pages
        new_pages = [url for url in current_pages.keys() if url not in previous_pages]
        
        # Find removed pages
        removed_pages = [url for url in previous_pages.keys() if url not in current_pages]
        
        # Find modified pages
        modified_pages = []
        for url in current_pages.keys():
            if url in previous_pages:
                current_page = current_pages[url]
                previous_page = previous_pages[url]
                
                # Check for changes - compare actual HTML content
                word_count_change = current_page.get("word_count", 0) - previous_page.get("word_count", 0)
                
                # Compare actual HTML content
                current_html = current_page.get("html_content", "")
                previous_html = previous_page.get("html_content", "")
                html_content_changed = current_html != previous_html
                
                # Also check text content
                current_text = current_page.get("text_content", "")
                previous_text = previous_page.get("text_content", "")
                text_content_changed = current_text != previous_text
                
                # Check AI analysis changes
                ai_analysis_changed = current_page.get("ai_analysis") != previous_page.get("ai_analysis")
                
                if (word_count_change != 0 or html_content_changed or text_content_changed):
                    modified_pages.append(ContentChange(
                        url=url,
                        title=current_page.get("page_title", ""),
                        change_type="modified",
                        word_count_change=word_count_change,
                        content_changed=html_content_changed or text_content_changed,
                        ai_analysis_changed=ai_analysis_changed
                    ))
        
        return {
            "new_pages": new_pages,
            "removed_pages": removed_pages,
            "modified_pages": modified_pages,
            "total_pages_compared": len(current_pages),
            "changes_summary": {
                "new_pages_count": len(new_pages),
                "removed_pages_count": len(removed_pages),
                "modified_pages_count": len(modified_pages)
            }
        }
    
    async def _generate_ai_insights(self, current_results: List[Dict], 
                                  previous_results: List[Dict], 
                                  basic_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights about the changes"""
        
        try:
            # Create comparison prompt
            prompt = self._create_comparison_prompt(current_results, previous_results, basic_comparison)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse AI response
            ai_insights = self._parse_ai_insights_response(response)
            
            return ai_insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {
                "overall_assessment": "Unable to generate AI insights due to technical error",
                "impact_analysis": "Analysis failed",
                "recommendations": ["Fix technical issues and retry comparison"]
            }
    
    def _create_comparison_prompt(self, current_results: List[Dict], 
                                previous_results: List[Dict], 
                                basic_comparison: Dict[str, Any]) -> str:
        """Create a comprehensive comparison prompt for OpenAI"""
        
        # Prepare summary data
        new_pages_count = basic_comparison["changes_summary"]["new_pages_count"]
        removed_pages_count = basic_comparison["changes_summary"]["removed_pages_count"]
        modified_pages_count = basic_comparison["changes_summary"]["modified_pages_count"]
        
        # Sample some pages for detailed analysis - focus on content changes
        sample_current = []
        sample_previous = []
        
        # Get samples of modified pages to show content changes
        for page in current_results[:5]:
            sample_current.append({
                "url": page.get("page_url", ""),
                "title": page.get("page_title", ""),
                "word_count": page.get("word_count", 0),
                "content_preview": page.get("text_content", "")[:500] if page.get("text_content") else "",
                "html_changed": "Yes" if page.get("html_content") else "No"
            })
        
        for page in previous_results[:5]:
            sample_previous.append({
                "url": page.get("page_url", ""),
                "title": page.get("page_title", ""),
                "word_count": page.get("word_count", 0),
                "content_preview": page.get("text_content", "")[:500] if page.get("text_content") else "",
                "html_changed": "Yes" if page.get("html_content") else "No"
            })
        
        prompt = f"""
You are an expert web content strategist. Analyze the changes between two website analysis runs and provide strategic insights based on actual HTML content changes.

CHANGE SUMMARY:
- New Pages: {new_pages_count}
- Removed Pages: {removed_pages_count}
- Modified Pages: {modified_pages_count}
- Total Pages Compared: {basic_comparison["total_pages_compared"]}

SAMPLE CURRENT PAGES (showing actual content):
{json.dumps(sample_current, indent=2)[:2000]}

SAMPLE PREVIOUS PAGES (showing actual content):
{json.dumps(sample_previous, indent=2)[:2000]}

Please provide strategic insights in the following JSON format:

{{
    "overall_assessment": "Comprehensive assessment of the actual content changes and their impact on the website",
    "impact_analysis": "Analysis of how these HTML content changes affect user experience, SEO, and business goals",
    "recommendations": [
        "Strategic recommendation 1 based on content changes",
        "Strategic recommendation 2 based on content changes", 
        "Strategic recommendation 3 based on content changes",
        "Strategic recommendation 4 based on content changes",
        "Strategic recommendation 5 based on content changes"
    ]
}}

GUIDELINES:
1. Focus on actual HTML content changes, not just structure or quality metrics
2. Analyze the impact of content additions, removals, and modifications
3. Consider SEO implications of content changes
4. Assess user experience impact of content modifications
5. Provide actionable recommendations based on content strategy
6. Consider the overall website content health and growth trajectory
7. Keep recommendations specific and implementable based on actual content changes
"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with the comparison prompt"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert web content strategist. Provide strategic insights about website changes and their impact on business goals, SEO, and user experience. Always respond with valid JSON."
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
    
    def _parse_ai_insights_response(self, response: str) -> Dict[str, Any]:
        """Parse AI insights response"""
        try:
            ai_data = json.loads(response)
            return {
                "overall_assessment": ai_data.get("overall_assessment", "Assessment not available"),
                "impact_analysis": ai_data.get("impact_analysis", "Impact analysis not available"),
                "recommendations": ai_data.get("recommendations", [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI insights response: {e}")
            return {
                "overall_assessment": "AI response parsing failed",
                "impact_analysis": "Unable to parse impact analysis",
                "recommendations": ["Retry comparison or check AI response format"]
            }
