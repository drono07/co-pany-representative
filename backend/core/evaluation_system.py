import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import statistics

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.models import PageContent, EvaluationResult, EvaluationType, WebsiteAnalysis
from ai.agents.ai_agents import (
    ContentQualityAgent, DesignAndLayoutAgent, AccessibilityAgent, 
    SEOAgent, TechnicalPerformanceAgent, ConversionOptimizationAgent,
    SecurityAgent, BrandConsistencyAgent
)

logger = logging.getLogger(__name__)

class MultiAgentEvaluationSystem:
    """Orchestrates multiple AI agents for comprehensive website evaluation"""
    
    def __init__(self):
        self.agents = {
            'content_quality': ContentQualityAgent(),
            'design_layout': DesignAndLayoutAgent(),
            'accessibility': AccessibilityAgent(),
            'seo': SEOAgent(),
            'technical': TechnicalPerformanceAgent(),
            'conversion': ConversionOptimizationAgent(),
            'security': SecurityAgent(),
            'brand_consistency': BrandConsistencyAgent()
        }
        
        self.evaluation_weights = {
            'content_quality': 0.20,
            'design_layout': 0.15,
            'accessibility': 0.15,
            'seo': 0.15,
            'technical': 0.15,
            'conversion': 0.10,
            'security': 0.05,
            'brand_consistency': 0.05
        }
    
    def evaluate_page(self, page: PageContent, screenshot: Optional[str] = None) -> List[EvaluationResult]:
        """Evaluate a single page with all agents"""
        logger.info(f"Starting multi-agent evaluation for {page.url}")
        
        # Create evaluation tasks for all agents
        tasks = []
        agent_names = []
        
        for agent_name, agent in self.agents.items():
            if agent_name == 'design_layout' and screenshot:
                # Special handling for design agent with screenshot
                result = agent.evaluate(page, context="", screenshot=screenshot)
            else:
                result = agent.evaluate(page)
            
            tasks.append(result)
            agent_names.append(agent_name)
        
        # Results are already completed since they're synchronous
        results = tasks
        
        # Process results
        evaluation_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in {agent_names[i]} agent: {result}")
                # Create error result
                error_result = EvaluationResult(
                    url=page.url,
                    evaluation_type=EvaluationType.CONTENT_QUALITY,
                    score=0,
                    issues=[f"Agent error: {str(result)}"],
                    evaluator_agent=agent_names[i]
                )
                evaluation_results.append(error_result)
            else:
                evaluation_results.append(result)
        
        logger.info(f"Completed multi-agent evaluation for {page.url}")
        return evaluation_results
    
    async def evaluate_website(self, analysis: WebsiteAnalysis, screenshots: Optional[Dict[str, str]] = None) -> WebsiteAnalysis:
        """Evaluate entire website with all agents"""
        logger.info(f"Starting website evaluation for {analysis.base_url}")
        
        all_evaluations = []
        
        # Evaluate each page
        for page in analysis.pages:
            screenshot = screenshots.get(page.url) if screenshots else None
            page_evaluations = self.evaluate_page(page, screenshot)
            all_evaluations.extend(page_evaluations)
        
        # Add evaluations to analysis
        analysis.evaluations = all_evaluations
        
        # Calculate overall scores
        analysis.overall_score = self._calculate_overall_score(all_evaluations)
        analysis.analysis_completed_at = datetime.now()
        
        logger.info(f"Completed website evaluation. Overall score: {analysis.overall_score}")
        return analysis
    
    def _calculate_overall_score(self, evaluations: List[EvaluationResult]) -> float:
        """Calculate weighted overall score from all evaluations"""
        if not evaluations:
            return 0.0
        
        # Group evaluations by type
        type_scores = {}
        for evaluation in evaluations:
            eval_type = evaluation.evaluation_type.value
            if eval_type not in type_scores:
                type_scores[eval_type] = []
            type_scores[eval_type].append(evaluation.score)
        
        # Calculate average score for each type
        type_averages = {}
        for eval_type, scores in type_scores.items():
            type_averages[eval_type] = statistics.mean(scores)
        
        # Calculate weighted overall score
        weighted_score = 0.0
        total_weight = 0.0
        
        for eval_type, avg_score in type_averages.items():
            weight = self.evaluation_weights.get(eval_type, 0.1)  # Default weight
            weighted_score += avg_score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0

class FinalEvaluator:
    """Final evaluator that synthesizes all agent results and provides comprehensive recommendations"""
    
    def __init__(self):
        self.client = None  # Will be initialized when needed
    
    async def generate_final_report(self, analysis: WebsiteAnalysis) -> Dict[str, Any]:
        """Generate comprehensive final evaluation report"""
        logger.info("Generating final evaluation report")
        
        # Aggregate all issues and recommendations
        all_issues = []
        all_recommendations = []
        agent_scores = {}
        
        for evaluation in analysis.evaluations:
            all_issues.extend(evaluation.issues)
            all_recommendations.extend(evaluation.recommendations)
            
            agent_name = evaluation.evaluator_agent
            if agent_name not in agent_scores:
                agent_scores[agent_name] = []
            agent_scores[agent_name].append(evaluation.score)
        
        # Calculate agent performance
        agent_performance = {}
        for agent_name, scores in agent_scores.items():
            agent_performance[agent_name] = {
                'average_score': statistics.mean(scores),
                'total_evaluations': len(scores),
                'score_distribution': {
                    'min': min(scores),
                    'max': max(scores),
                    'median': statistics.median(scores)
                }
            }
        
        # Categorize issues by severity
        critical_issues = []
        major_issues = []
        minor_issues = []
        
        for issue in all_issues:
            if any(keyword in issue.lower() for keyword in ['critical', 'security', 'broken', 'error']):
                critical_issues.append(issue)
            elif any(keyword in issue.lower() for keyword in ['major', 'important', 'significant']):
                major_issues.append(issue)
            else:
                minor_issues.append(issue)
        
        # Generate priority recommendations
        priority_recommendations = self._prioritize_recommendations(all_recommendations)
        
        # Create comprehensive report
        report = {
            'website_url': analysis.base_url,
            'analysis_date': analysis.analysis_completed_at.isoformat() if analysis.analysis_completed_at else None,
            'overall_score': analysis.overall_score,
            'summary': {
                'total_pages_analyzed': analysis.total_pages,
                'total_links_found': analysis.total_links,
                'broken_links': analysis.broken_links,
                'blank_pages': analysis.blank_pages,
                'total_evaluations': len(analysis.evaluations)
            },
            'scores_by_category': {
                'content_quality': self._get_category_score(analysis.evaluations, 'content_quality'),
                'design_layout': self._get_category_score(analysis.evaluations, 'design_issues'),
                'accessibility': self._get_category_score(analysis.evaluations, 'accessibility'),
                'seo': self._get_category_score(analysis.evaluations, 'seo'),
                'technical': self._get_category_score(analysis.evaluations, 'technical')
            },
            'issues': {
                'critical': critical_issues,
                'major': major_issues,
                'minor': minor_issues,
                'total_count': len(all_issues)
            },
            'recommendations': {
                'high_priority': priority_recommendations.get('high', []),
                'medium_priority': priority_recommendations.get('medium', []),
                'low_priority': priority_recommendations.get('low', []),
                'total_count': len(all_recommendations)
            },
            'agent_performance': agent_performance,
            'detailed_findings': self._generate_detailed_findings(analysis),
            'action_plan': self._generate_action_plan(analysis, priority_recommendations)
        }
        
        return report
    
    def _get_category_score(self, evaluations: List[EvaluationResult], category: str) -> float:
        """Get average score for a specific evaluation category"""
        category_evaluations = [e for e in evaluations if e.evaluation_type.value == category]
        if not category_evaluations:
            return 0.0
        return statistics.mean([e.score for e in category_evaluations])
    
    def _prioritize_recommendations(self, recommendations: List[str]) -> Dict[str, List[str]]:
        """Prioritize recommendations based on impact and effort"""
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for rec in recommendations:
            rec_lower = rec.lower()
            
            # High priority keywords
            if any(keyword in rec_lower for keyword in [
                'security', 'broken', 'error', 'critical', 'urgent', 
                'fix immediately', 'high impact', 'conversion'
            ]):
                high_priority.append(rec)
            # Medium priority keywords
            elif any(keyword in rec_lower for keyword in [
                'improve', 'optimize', 'enhance', 'better', 'consider',
                'recommend', 'suggest'
            ]):
                medium_priority.append(rec)
            else:
                low_priority.append(rec)
        
        return {
            'high': high_priority,
            'medium': medium_priority,
            'low': low_priority
        }
    
    def _generate_detailed_findings(self, analysis: WebsiteAnalysis) -> Dict[str, Any]:
        """Generate detailed findings from the analysis"""
        findings = {
            'page_analysis': {},
            'link_analysis': {},
            'content_analysis': {}
        }
        
        # Page analysis
        page_types = {}
        for page in analysis.pages:
            page_type = page.page_type.value
            page_types[page_type] = page_types.get(page_type, 0) + 1
        
        findings['page_analysis'] = {
            'page_type_distribution': page_types,
            'average_word_count': statistics.mean([p.word_count for p in analysis.pages]) if analysis.pages else 0,
            'pages_with_headers': sum(1 for p in analysis.pages if p.has_header),
            'pages_with_footers': sum(1 for p in analysis.pages if p.has_footer),
            'pages_with_navigation': sum(1 for p in analysis.pages if p.has_navigation)
        }
        
        # Link analysis
        link_statuses = {}
        for link in analysis.links:
            status = link.status.value
            link_statuses[status] = link_statuses.get(status, 0) + 1
        
        findings['link_analysis'] = {
            'link_status_distribution': link_statuses,
            'average_response_time': statistics.mean([l.response_time for l in analysis.links if l.response_time]) if analysis.links else 0,
            'broken_links_percentage': (analysis.broken_links / analysis.total_links * 100) if analysis.total_links > 0 else 0
        }
        
        # Content analysis
        findings['content_analysis'] = {
            'total_content_pages': sum(1 for p in analysis.pages if p.page_type.value == 'content'),
            'blank_pages_percentage': (analysis.blank_pages / analysis.total_pages * 100) if analysis.total_pages > 0 else 0,
            'average_content_chunks': statistics.mean([len(p.content_chunks) for p in analysis.pages]) if analysis.pages else 0
        }
        
        return findings
    
    def _generate_action_plan(self, analysis: WebsiteAnalysis, priority_recommendations: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Generate actionable plan based on findings"""
        action_plan = []
        
        # Immediate actions (critical issues)
        if priority_recommendations.get('high'):
            action_plan.append({
                'phase': 'Immediate (1-3 days)',
                'priority': 'Critical',
                'actions': priority_recommendations['high'][:5],  # Top 5 critical actions
                'estimated_effort': 'High',
                'expected_impact': 'High'
            })
        
        # Short-term actions (major issues)
        if priority_recommendations.get('medium'):
            action_plan.append({
                'phase': 'Short-term (1-2 weeks)',
                'priority': 'High',
                'actions': priority_recommendations['medium'][:8],  # Top 8 medium actions
                'estimated_effort': 'Medium',
                'expected_impact': 'Medium-High'
            })
        
        # Long-term actions (optimization)
        if priority_recommendations.get('low'):
            action_plan.append({
                'phase': 'Long-term (1-3 months)',
                'priority': 'Medium',
                'actions': priority_recommendations['low'][:10],  # Top 10 low priority actions
                'estimated_effort': 'Low-Medium',
                'expected_impact': 'Medium'
            })
        
        return action_plan

class EvaluationOrchestrator:
    """Main orchestrator that coordinates the entire evaluation process"""
    
    def __init__(self):
        self.multi_agent_system = MultiAgentEvaluationSystem()
        self.final_evaluator = FinalEvaluator()
    
    async def run_complete_evaluation(self, analysis: WebsiteAnalysis, screenshots: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Run complete evaluation process"""
        logger.info("Starting complete website evaluation")
        
        # Step 1: Multi-agent evaluation
        analysis = await self.multi_agent_system.evaluate_website(analysis, screenshots)
        
        # Step 2: Generate final report
        final_report = await self.final_evaluator.generate_final_report(analysis)
        
        logger.info("Complete website evaluation finished")
        return final_report
