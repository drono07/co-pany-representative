import asyncio
import json
import logging
import os
import aiohttp
from typing import Dict, Any
from datetime import datetime
import argparse
import sys
from pathlib import Path

from ..utils.models import WebsiteAnalysis
from .crawler import WebsiteCrawler
from .validators import LinkValidator, BlankPageDetector, ContentAnalyzer
from .content_processor import ContentProcessor
from .evaluation_system import EvaluationOrchestrator
from ..utils.config import settings
from ..database.database_schema import get_database
from .change_detector import ChangeDetector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('website_insights.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebsiteInsightsPlatform:
    """Main platform class that orchestrates the entire website analysis process"""
    
    def __init__(self):
        self.crawler = None
        self.link_validator = None
        self.blank_page_detector = BlankPageDetector()
        self.content_analyzer = ContentAnalyzer()
        self.content_processor = ContentProcessor()
        self.evaluation_orchestrator = EvaluationOrchestrator()
        self.db = None
        self.change_detector = ChangeDetector()
    
    async def analyze_website(self, url: str, max_depth: int = None, include_screenshots: bool = False, max_pages_to_crawl: int = None, max_links_to_validate: int = None,
                             extract_static: bool = True, extract_dynamic: bool = False, extract_resources: bool = False, extract_external: bool = False) -> Dict[str, Any]:
        """Main method to analyze a website comprehensively"""
        logger.info(f"Starting comprehensive analysis of {url}")
        
        # Connect to MongoDB if enabled
        if settings.enable_mongodb_storage:
            try:
                self.db = await get_database()
                logger.info("Connected to MongoDB successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to MongoDB: {e}. Continuing without MongoDB storage.")
                self.db = None
        
        
        try:
            # Step 1: Crawl the website
            logger.info("Step 1: Crawling website...")
            crawl_results = await self._crawl_website(url, max_depth, max_pages_to_crawl, max_links_to_validate,
                                                     extract_static, extract_dynamic, extract_resources, extract_external)
            
            
            # Step 2: Validate links (always run for all pages)
            if settings.enable_link_validation:
                logger.info("Step 2: Validating links...")
                validated_links = await self._validate_links(crawl_results['links'])
                
            else:
                logger.info("Step 2: Link validation disabled")
                validated_links = crawl_results['links']
            
            # Step 3: Detect blank pages (always run for all pages)
            if settings.enable_blank_page_detection:
                logger.info("Step 3: Detecting blank pages...")
                analyzed_pages = self._detect_blank_pages(crawl_results['pages'])
                
            else:
                logger.info("Step 3: Blank page detection disabled")
                analyzed_pages = crawl_results['pages']
            
            # Step 4: Process content (always run for all pages)
            if settings.enable_content_analysis:
                logger.info("Step 4: Processing content...")
                processed_pages = self._process_content(analyzed_pages)
                
            else:
                logger.info("Step 4: Content processing disabled")
                processed_pages = analyzed_pages
            
            # Step 5: Create analysis object
            analysis = self._create_analysis_object(url, processed_pages, validated_links)
            
            # Step 5.5: Save to MongoDB and detect changes (if enabled)
            if self.db:
                await self._save_to_mongodb_and_detect_changes(url, crawl_results, processed_pages, analysis)
            
            # Step 6: Run AI evaluations (limited to configured number of pages)
            if settings.enable_ai_evaluation:
                logger.info(f"Step 5: Running AI evaluations on {min(settings.max_ai_evaluation_pages, len(processed_pages))} pages...")
                # Select pages for AI evaluation (prioritize content pages)
                pages_for_ai = self._select_pages_for_ai_evaluation(processed_pages)
                analysis.pages = pages_for_ai  # Temporarily limit for AI evaluation
                
                screenshots = await self._capture_screenshots(pages_for_ai) if include_screenshots else None
                final_report = await self.evaluation_orchestrator.run_complete_evaluation(analysis, screenshots)
                
                # Restore all pages in the final report
                analysis.pages = processed_pages
                final_report['summary']['total_pages_analyzed'] = len(processed_pages)
                final_report['summary']['ai_evaluated_pages'] = len(pages_for_ai)
            else:
                logger.info("Step 5: AI evaluation disabled")
                final_report = self._create_basic_report(analysis, crawl_results.get('path_tracking', {}))
            
            logger.info("Website analysis completed successfully")
            return final_report
            
        except Exception as e:
            logger.error(f"Error during website analysis: {e}")
            raise
    
    async def _crawl_website(self, url: str, max_depth: int = None, max_pages_to_crawl: int = None, max_links_to_validate: int = None,
                            extract_static: bool = True, extract_dynamic: bool = False, extract_resources: bool = False, extract_external: bool = False) -> Dict[str, Any]:
        """Crawl the website and extract all pages and links with configurable link types"""
        async with WebsiteCrawler() as crawler:
            return await crawler.crawl_website(url, max_depth, max_pages_to_crawl, max_links_to_validate,
                                             extract_static, extract_dynamic, extract_resources, extract_external)
    
    async def _validate_links(self, links) -> list:
        """Validate all discovered links"""
        async with LinkValidator() as validator:
            validated_links = await validator.validate_links(links)
        
        # Add manual link checking for known links that might be missed
        manual_links = await self._check_manual_links()
        if manual_links:
            validated_links.extend(manual_links)
            logger.info(f"Added {len(manual_links)} manually checked links")
        
        return validated_links
    
    async def _check_manual_links(self) -> list:
        """Check specific known links that might be dynamically loaded"""
        # List of known links to check manually
        manual_urls = [
            # "https://thegoodbug.com/pages/blockbuster-sale",  # Commented out due to rate limiting
            # Add more known links here as needed
        ]
        
        manual_links = []
        async with aiohttp.ClientSession() as session:
            for url in manual_urls:
                max_retries = 10  # Reasonable limit
                base_delay = 2  # Start with 2 seconds
                attempt = 0
                
                while attempt < max_retries:
                    try:
                        attempt += 1
                        async with session.get(url, allow_redirects=True) as response:
                            # If rate limited, retry with exponential backoff
                            if response.status == 429:
                                if attempt < max_retries:
                                    retry_delay = min(base_delay * (2 ** (attempt - 1)), 15)  # 2s, 4s, 8s, 15s max
                                    logger.warning(f"Rate limited manual check {url} (attempt {attempt}/{max_retries}) - retrying in {retry_delay}s")
                                    await asyncio.sleep(retry_delay)
                                    continue
                                else:
                                    logger.warning(f"Rate limited manual check {url} after {max_retries} attempts - giving up")
                                    from models import Link, LinkStatus
                                    link = Link(
                                        url=url,
                                        status=LinkStatus.RATE_LIMITED,
                                        status_code=429,
                                        response_time=0.0,
                                        title="",
                                        error_message=f"Rate limited after {max_retries} attempts"
                                    )
                                    manual_links.append(link)
                                    break
                            
                            from models import Link, LinkStatus
                            # Use the same categorization logic as the validator
                            if response.status < 400:
                                status = LinkStatus.VALID
                            else:
                                status = LinkStatus.BROKEN
                                
                            link = Link(
                                url=url,
                                status=status,
                                status_code=response.status,
                                response_time=0.0,  # We don't measure time for manual checks
                                title="",  # Could extract title if needed
                                error_message=None if response.status < 400 else f"HTTP {response.status}"
                            )
                            manual_links.append(link)
                            logger.info(f"Manual check: {url} - Status: {response.status}")
                            break  # Success, exit retry loop
                            
                    except Exception as e:
                        if attempt < max_retries:
                            retry_delay = min(base_delay * (2 ** (attempt - 1)), 15)
                            logger.warning(f"Manual check error for {url} (attempt {attempt}/{max_retries}): {str(e)} - retrying in {retry_delay}s")
                            await asyncio.sleep(retry_delay)
                        else:
                            logger.error(f"Manual check failed for {url} after {max_retries} attempts: {str(e)}")
                            from models import Link, LinkStatus
                            link = Link(
                                url=url,
                                status=LinkStatus.BROKEN,
                                status_code=None,
                                response_time=0.0,
                                title="",
                                error_message=str(e)
                            )
                            manual_links.append(link)
                            break
        
        return manual_links
    
    def _detect_blank_pages(self, pages) -> list:
        """Detect blank or low-content pages"""
        return self.blank_page_detector.detect_blank_pages(pages)
    
    def _process_content(self, pages) -> list:
        """Process page content and create chunks"""
        logger.info("Processing content for all pages...")
        
        try:
            processed_pages = self.content_processor.process_pages(pages)
            logger.info(f"Successfully processed content for {len(processed_pages)} pages")
            return processed_pages
        except Exception as e:
            logger.error(f"Error in content processing: {e}")
            # Return pages with minimal processing
            for page in pages:
                if not hasattr(page, 'content_chunks') or not page.content_chunks:
                    page.content_chunks = [page.text_content[:2000]] if page.text_content else []
            return pages
    
    def _create_analysis_object(self, url: str, pages: list, links: list) -> WebsiteAnalysis:
        """Create the main analysis object"""
        broken_links = sum(1 for link in links if link.status.value == 'broken')
        blank_pages = sum(1 for page in pages if page.page_type.value == 'blank')
        
        return WebsiteAnalysis(
            base_url=url,
            total_pages=len(pages),
            total_links=len(links),
            broken_links=broken_links,
            blank_pages=blank_pages,
            pages=pages,
            links=links
        )
    
    async def _save_to_mongodb_and_detect_changes(self, url: str, crawl_results: Dict, processed_pages: list, analysis: WebsiteAnalysis):
        """Save crawl data to MongoDB and detect changes from previous runs"""
        try:
            # Get previous crawl session for comparison
            previous_session = await self.db.get_previous_crawl_session(url)
            
            # Save current crawl session
            session_data = {
                "session_id": crawl_results.get("session_id", f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "website_url": url,
                "max_depth": crawl_results.get("max_depth", 1),
                "created_at": datetime.now().isoformat(),
                "total_pages": crawl_results.get("total_pages", 0),
                "total_visited": crawl_results.get("total_visited", 0),
                "error_rate": crawl_results.get("error_rate", 0),
                "path_tracking": crawl_results.get("path_tracking", {})
            }
            
            session_id = await self.db.save_crawl_session(session_data)
            logger.info(f"Crawl session saved with ID: {session_id}")
            
            # Save page data to MongoDB
            for page in processed_pages:
                page_data = {
                    "session_id": session_data["session_id"],
                    "url": page.url,
                    "title": page.title,
                    "word_count": page.word_count,
                    "page_type": page.page_type.value,
                    "path": getattr(page, 'path', []),
                    "crawled_at": getattr(page, 'crawled_at', datetime.now().isoformat()),
                    "html_structure": getattr(page, 'html_structure', None),
                    "has_header": page.has_header,
                    "has_footer": page.has_footer,
                    "has_navigation": page.has_navigation,
                    "content_chunks": page.content_chunks
                }
                await self.db.save_page_data(page_data)
            
            logger.info(f"Saved {len(processed_pages)} pages to MongoDB")
            
            # Detect changes if previous session exists
            if previous_session:
                logger.info("Detecting changes from previous crawl...")
                previous_pages = await self.db.get_pages_from_session(previous_session["session_id"])
                
                # Set pages for comparison
                self.change_detector.set_current_pages([page.dict() for page in processed_pages])
                self.change_detector.set_previous_pages(previous_pages)
                
                # Detect changes
                changes = self.change_detector.detect_changes()
                
                # Save change detection results
                change_data = {
                    "website_url": url,
                    "current_session_id": session_data["session_id"],
                    "previous_session_id": previous_session["session_id"],
                    "detected_at": datetime.now().isoformat(),
                    "changes": changes
                }
                
                change_id = await self.db.save_change_detection(change_data)
                logger.info(f"Change detection results saved with ID: {change_id}")
                
                # Print change report
                print("\n" + "="*80)
                print("CHANGE DETECTION REPORT")
                print("="*80)
                print(self.change_detector.get_change_report())
                print("="*80)
            else:
                logger.info("No previous crawl data found for comparison")
                
        except Exception as e:
            logger.error(f"Failed to save to MongoDB or detect changes: {e}")
    
    def _select_pages_for_ai_evaluation(self, pages: list) -> list:
        """Select pages for AI evaluation, prioritizing content pages"""
        # Prioritize pages with actual content
        content_pages = [p for p in pages if p.page_type.value == 'content' and p.word_count > 100]
        other_pages = [p for p in pages if p not in content_pages]
        
        # Take up to max_ai_evaluation_pages, prioritizing content pages
        selected_pages = content_pages[:settings.max_ai_evaluation_pages]
        
        # If we need more pages, add from other pages
        if len(selected_pages) < settings.max_ai_evaluation_pages:
            remaining_slots = settings.max_ai_evaluation_pages - len(selected_pages)
            selected_pages.extend(other_pages[:remaining_slots])
        
        logger.info(f"Selected {len(selected_pages)} pages for AI evaluation: {len(content_pages)} content pages, {len(selected_pages) - len(content_pages)} other pages")
        return selected_pages
    
    def _create_basic_report(self, analysis: WebsiteAnalysis, path_tracking: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a basic report without AI evaluation"""
        # Filter out rate-limited links from broken links
        broken_links = [link for link in analysis.links if link.status.value == 'broken' and link.status_code != 429]
        rate_limited_links = [link for link in analysis.links if link.status.value == 'rate_limited' or link.status_code == 429]
        blank_pages = [page for page in analysis.pages if page.page_type.value == 'blank']
        content_pages = [page for page in analysis.pages if page.page_type.value == 'content']
        
        # Calculate basic scores based on non-AI analysis
        total_issues = len(broken_links) + len(blank_pages)
        technical_score = max(0, 100 - (total_issues * 10))  # Deduct 10 points per issue
        
        return {
            'website_url': analysis.base_url,
            'analysis_date': analysis.analysis_completed_at.isoformat() if analysis.analysis_completed_at else None,
            'overall_score': technical_score,
            'summary': {
                'total_pages_analyzed': analysis.total_pages,
                'total_links_found': analysis.total_links,
                'broken_links': len(broken_links),
                'rate_limited_links': len(rate_limited_links),
                'blank_pages': len(blank_pages),
                'content_pages': len(content_pages),
                'ai_evaluated_pages': 0
            },
            'scores_by_category': {
                'content_quality': None,
                'design_layout': None,
                'accessibility': None,
                'seo': None,
                'technical': technical_score
            },
            'issues': {
                'critical': [
                    f"Broken link (HTTP {link.status_code}): {link.url}" 
                    for link in broken_links[:10]
                ],
                'major': [
                    f"Blank page (only {page.word_count} words): {page.url}" 
                    for page in blank_pages[:10]
                ],
                'minor': [],  # Rate-limited links are not issues - they're just being retried
                'total_count': len(broken_links) + len(blank_pages)
            },
            'recommendations': {
                'high_priority': [
                    f"Fix broken link: {link.url} (Error: {link.error_message})" 
                    for link in broken_links[:5]
                ],
                'medium_priority': [
                    f"Add content to blank page: {page.url} (Currently only {page.word_count} words)" 
                    for page in blank_pages[:5]
                ],
                'low_priority': [],  # Rate-limited links are not recommendations - they're being retried
                'total_count': total_issues
            },
            'agent_performance': {
                'note': 'AI evaluation disabled - only technical analysis performed'
            },
            'detailed_findings': {
                'broken_links': [
                    {
                        'url': link.url, 
                        'status_code': link.status_code, 
                        'error': link.error_message,
                        'response_time': link.response_time
                    } for link in broken_links
                ],
                'valid_links': [
                    {
                        'url': link.url, 
                        'status_code': link.status_code, 
                        'response_time': link.response_time
                    } for link in analysis.links if link.status.value == 'valid'
                ],
                'blank_pages': [
                    {
                        'url': page.url, 
                        'word_count': page.word_count, 
                        'title': page.title,
                        'has_header': page.has_header,
                        'has_footer': page.has_footer,
                        'has_navigation': page.has_navigation,
                        'html_content': getattr(page, 'html_content', ''),
                        'path': getattr(page, 'path', [])
                    } for page in blank_pages
                ],
                'content_pages': [
                    {
                        'url': page.url,
                        'word_count': page.word_count,
                        'title': page.title,
                        'has_header': page.has_header,
                        'has_footer': page.has_footer,
                        'has_navigation': page.has_navigation,
                        'html_content': getattr(page, 'html_content', ''),
                        'path': getattr(page, 'path', [])
                    } for page in content_pages
                ],
                'rate_limited_links': [
                    {
                        'url': link.url,
                        'status_code': link.status_code,
                        'error': link.error_message,
                        'response_time': link.response_time
                    } for link in rate_limited_links
                ],
                'all_pages_summary': [
                    {
                        'url': page.url,
                        'word_count': page.word_count,
                        'title': page.title,
                        'page_type': page.page_type.value,
                        'has_header': page.has_header,
                        'has_footer': page.has_footer,
                        'has_navigation': page.has_navigation
                    } for page in analysis.pages
                ],
                'all_links_summary': [
                    {
                        'url': link.url,
                        'status': link.status.value,
                        'status_code': link.status_code,
                        'title': getattr(link, 'title', ''),
                        'response_time': link.response_time
                    } for link in analysis.links
                ]
            },
            'action_plan': [
                {
                    'phase': 'Immediate (1-3 days)',
                    'priority': 'Critical',
                    'actions': [f"Fix broken link: {link.url}" for link in broken_links[:5]],
                    'estimated_effort': 'Medium',
                    'expected_impact': 'High'
                },
                {
                    'phase': 'Short term (1-2 weeks)',
                    'priority': 'Major',
                    'actions': [f"Add content to blank page: {page.url}" for page in blank_pages[:5]],
                    'estimated_effort': 'High',
                    'expected_impact': 'Medium'
                }
            ] if total_issues > 0 else [],
            'path_tracking': path_tracking or {}
        }
    
    async def _capture_screenshots(self, pages: list) -> Dict[str, str]:
        """Capture screenshots of pages (placeholder for future implementation)"""
        # This would integrate with tools like Playwright or Selenium
        # For now, return empty dict
        logger.info("Screenshot capture not implemented yet")
        return {}
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save the analysis report to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Extract just the domain name, not the full URL
            from urllib.parse import urlparse
            parsed_url = urlparse(report['website_url'])
            domain = parsed_url.netloc.replace('www.', '')
            filename = f"website_analysis_{domain}_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Report saved to {filepath}")
        return str(filepath)
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a summary of the analysis results"""
        print("\n" + "="*80)
        print("WEBSITE ANALYSIS SUMMARY")
        print("="*80)
        print(f"Website: {report['website_url']}")
        print(f"Analysis Date: {report['analysis_date']}")
        overall_score = report['overall_score']
        if overall_score is not None:
            print(f"Overall Score: {overall_score:.1f}/100")
        else:
            print("Overall Score: N/A (AI evaluation disabled)")
        print()
        
        # Summary statistics
        summary = report['summary']
        print("PAGE ANALYSIS:")
        print(f"  Total Pages: {summary['total_pages_analyzed']}")
        print(f"  Total Links: {summary['total_links_found']}")
        print(f"  Broken Links: {summary['broken_links']}")
        if 'rate_limited_links' in summary:
            print(f"  Rate Limited Links: {summary['rate_limited_links']}")
        print(f"  Blank Pages: {summary['blank_pages']}")
        if 'content_pages' in summary:
            print(f"  Content Pages: {summary['content_pages']}")
        if 'ai_evaluated_pages' in summary:
            print(f"  AI Evaluated Pages: {summary['ai_evaluated_pages']}")
        print()
        
        # Scores by category
        print("SCORES BY CATEGORY:")
        scores = report['scores_by_category']
        for category, score in scores.items():
            if score is not None:
                print(f"  {category.replace('_', ' ').title()}: {score:.1f}/100")
            else:
                print(f"  {category.replace('_', ' ').title()}: N/A")
        print()
        
        # Critical issues
        issues = report['issues']
        if issues['critical']:
            print("CRITICAL ISSUES:")
            for issue in issues['critical'][:5]:  # Show top 5
                print(f"  ⚠️  {issue}")
            print()
        
        # High priority recommendations
        recommendations = report['recommendations']
        if recommendations['high_priority']:
            print("HIGH PRIORITY RECOMMENDATIONS:")
            for rec in recommendations['high_priority'][:5]:  # Show top 5
                print(f"  ✅ {rec}")
            print()
        
        print("="*80)

async def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='Website Insights Platform - Comprehensive Website Analysis')
    parser.add_argument('url', help='Website URL to analyze')
    parser.add_argument('--depth', type=int, default=3, help='Maximum crawl depth (default: 3)')
    parser.add_argument('--screenshots', action='store_true', help='Include screenshot analysis')
    parser.add_argument('--output', help='Output file path for the report')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # Validate OpenAI API key
    if not settings.openai_api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        sys.exit(1)
    
    # Create platform instance
    platform = WebsiteInsightsPlatform()
    
    try:
        # Run analysis
        if not args.quiet:
            print(f"Starting analysis of {args.url}...")
            print(f"Max depth: {args.depth}")
            print(f"Include screenshots: {args.screenshots}")
            print()
        
        report = await platform.analyze_website(
            url=args.url,
            max_depth=args.depth,
            include_screenshots=args.screenshots
        )
        
        # Save report
        output_file = platform.save_report(report, args.output)
        
        # Print summary
        if not args.quiet:
            platform.print_summary(report)
            print(f"\n📊 Detailed report saved to: {output_file}")
            print(f"📁 Full path: {os.path.abspath(output_file)}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if not args.quiet:
            print(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
