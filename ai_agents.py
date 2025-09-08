import openai
from typing import Dict, Any, Optional
import json
import logging

from models import PageContent, EvaluationResult, EvaluationType
from config import settings
from content_processor import ContentProcessor

logger = logging.getLogger(__name__)

class BaseAIAgent:
    """Base class for all AI evaluation agents"""
    
    def __init__(self, agent_name: str, model: str = "gpt-4"):
        self.agent_name = agent_name
        self.model = model
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.content_processor = ContentProcessor()
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        """Evaluate a page and return results"""
        raise NotImplementedError
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        """Create evaluation prompt for the agent"""
        raise NotImplementedError
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return {"score": 50, "issues": [response], "recommendations": []}

class ContentQualityAgent(BaseAIAgent):
    """Evaluates content quality, readability, and value"""
    
    def __init__(self):
        super().__init__("Content Quality Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a content quality expert. Analyze web page content for quality, readability, and value."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.CONTENT_QUALITY,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in ContentQualityAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.CONTENT_QUALITY,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        content_context = self.content_processor.create_context_for_ai(page)
        
        return f"""
        Analyze the following web page content for quality and value:

        {content_context}

        Evaluate the following aspects:
        1. Content depth and substance
        2. Readability and clarity
        3. Information value and usefulness
        4. Grammar and writing quality
        5. Content structure and organization
        6. Uniqueness and originality

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific issues found"],
            "recommendations": ["list of improvement suggestions"],
            "details": {{
                "readability_score": <0-100>,
                "content_depth": <0-100>,
                "grammar_issues": <count>,
                "value_assessment": "<high/medium/low>",
                "structure_quality": <0-100>
            }}
        }}
        """

class DesignAndLayoutAgent(BaseAIAgent):
    """Evaluates design, layout, spacing, and visual hierarchy"""
    
    def __init__(self):
        super().__init__("Design & Layout Agent", "gpt-4o")
    
    def evaluate(self, page: PageContent, context: str = "", screenshot: Optional[str] = None) -> EvaluationResult:
        messages = [
            {"role": "system", "content": "You are a UX/UI design expert. Analyze web page design, layout, and visual hierarchy."}
        ]
        
        # Add screenshot if available
        if screenshot:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": self._create_prompt(page, context)},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot}"}}
                ]
            })
        else:
            messages.append({"role": "user", "content": self._create_prompt(page, context)})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.DESIGN_ISSUES,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in DesignAndLayoutAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.DESIGN_ISSUES,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the design and layout of this web page:

        URL: {page.url}
        Title: {page.title or "No title"}
        
        HTML Structure Analysis:
        - Has Header: {page.has_header}
        - Has Footer: {page.has_footer}
        - Has Navigation: {page.has_navigation}
        - Word Count: {page.word_count}

        Evaluate the following design aspects:
        1. Visual hierarchy and spacing
        2. Layout consistency
        3. Header/footer design
        4. Navigation structure
        5. Content organization
        6. White space usage
        7. Typography and readability
        8. Mobile responsiveness indicators

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific design issues"],
            "recommendations": ["list of design improvement suggestions"],
            "details": {{
                "spacing_issues": <count>,
                "hierarchy_problems": <count>,
                "layout_score": <0-100>,
                "header_footer_quality": <0-100>,
                "navigation_score": <0-100>,
                "responsive_design": "<good/needs_work/poor>"
            }}
        }}
        """

class AccessibilityAgent(BaseAIAgent):
    """Evaluates accessibility compliance and usability"""
    
    def __init__(self):
        super().__init__("Accessibility Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an accessibility expert. Analyze web page accessibility compliance and usability."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.ACCESSIBILITY,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in AccessibilityAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.ACCESSIBILITY,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the accessibility of this web page:

        URL: {page.url}
        Title: {page.title or "No title"}
        
        HTML Content (first 2000 chars):
        {page.html_content[:2000]}

        Evaluate the following accessibility aspects:
        1. Semantic HTML structure
        2. Alt text for images
        3. Heading hierarchy (h1, h2, h3, etc.)
        4. Link accessibility
        5. Form accessibility
        6. Color contrast considerations
        7. Keyboard navigation support
        8. Screen reader compatibility
        9. ARIA labels and roles
        10. Focus management

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific accessibility issues"],
            "recommendations": ["list of accessibility improvements"],
            "details": {{
                "wcag_compliance": "<A/AA/AAA/none>",
                "semantic_html_score": <0-100>,
                "alt_text_coverage": <percentage>,
                "heading_structure_score": <0-100>,
                "keyboard_navigation": "<good/needs_work/poor>",
                "screen_reader_friendly": <true/false>
            }}
        }}
        """

class SEOAgent(BaseAIAgent):
    """Evaluates SEO optimization and search engine visibility"""
    
    def __init__(self):
        super().__init__("SEO Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an SEO expert. Analyze web page SEO optimization and search engine visibility."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.SEO,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in SEOAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.SEO,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the SEO optimization of this web page:

        URL: {page.url}
        Title: {page.title or "No title"}
        Word Count: {page.word_count}
        
        HTML Content (first 2000 chars):
        {page.html_content[:2000]}

        Evaluate the following SEO aspects:
        1. Title tag optimization
        2. Meta description presence
        3. Heading structure (H1, H2, H3)
        4. Keyword density and relevance
        5. Internal linking structure
        6. Image alt text
        7. URL structure
        8. Content length and depth
        9. Schema markup indicators
        10. Mobile-friendliness signals

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific SEO issues"],
            "recommendations": ["list of SEO improvements"],
            "details": {{
                "title_optimization": <0-100>,
                "meta_description_score": <0-100>,
                "heading_structure": <0-100>,
                "content_quality_seo": <0-100>,
                "keyword_optimization": <0-100>,
                "technical_seo": <0-100>
            }}
        }}
        """

class TechnicalPerformanceAgent(BaseAIAgent):
    """Evaluates technical performance and code quality"""
    
    def __init__(self):
        super().__init__("Technical Performance Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical performance expert. Analyze web page technical implementation and performance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.TECHNICAL,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in TechnicalPerformanceAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.TECHNICAL,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the technical implementation of this web page:

        URL: {page.url}
        Response Time: {getattr(page, 'response_time', 'Unknown')}
        
        HTML Content (first 3000 chars):
        {page.html_content[:3000]}

        Evaluate the following technical aspects:
        1. HTML structure and validation
        2. CSS organization and efficiency
        3. JavaScript implementation
        4. Image optimization
        5. Loading performance indicators
        6. Code cleanliness and maintainability
        7. Security considerations
        8. Browser compatibility
        9. Mobile optimization
        10. Core Web Vitals indicators

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific technical issues"],
            "recommendations": ["list of technical improvements"],
            "details": {{
                "html_quality": <0-100>,
                "css_efficiency": <0-100>,
                "js_optimization": <0-100>,
                "performance_score": <0-100>,
                "security_score": <0-100>,
                "mobile_optimization": <0-100>
            }}
        }}
        """

class ConversionOptimizationAgent(BaseAIAgent):
    """Evaluates conversion optimization and user experience for business goals"""
    
    def __init__(self):
        super().__init__("Conversion Optimization Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a conversion optimization expert. Analyze web page effectiveness for business goals and user conversions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.CONTENT_QUALITY,  # Using existing type
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in ConversionOptimizationAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.CONTENT_QUALITY,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the conversion optimization potential of this web page:

        URL: {page.url}
        Title: {page.title or "No title"}
        Word Count: {page.word_count}
        
        Content Context:
        {self.content_processor.create_context_for_ai(page)}

        Evaluate the following conversion aspects:
        1. Call-to-action (CTA) presence and effectiveness
        2. Value proposition clarity
        3. Trust signals and credibility
        4. User journey optimization
        5. Form design and completion rates
        6. Social proof elements
        7. Urgency and scarcity indicators
        8. Mobile conversion experience
        9. Page loading impact on conversions
        10. Content relevance to business goals

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific conversion issues"],
            "recommendations": ["list of conversion improvements"],
            "details": {{
                "cta_effectiveness": <0-100>,
                "value_proposition_clarity": <0-100>,
                "trust_signals": <0-100>,
                "user_journey_score": <0-100>,
                "mobile_conversion": <0-100>,
                "business_alignment": <0-100>
            }}
        }}
        """

class SecurityAgent(BaseAIAgent):
    """Evaluates security vulnerabilities and best practices"""
    
    def __init__(self):
        super().__init__("Security Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a web security expert. Analyze web page security vulnerabilities and best practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.TECHNICAL,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in SecurityAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.TECHNICAL,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the security aspects of this web page:

        URL: {page.url}
        
        HTML Content (first 3000 chars):
        {page.html_content[:3000]}

        Evaluate the following security aspects:
        1. HTTPS implementation
        2. Form security (CSRF protection)
        3. Input validation indicators
        4. XSS vulnerability signs
        5. SQL injection prevention
        6. Content Security Policy (CSP)
        7. Secure cookie settings
        8. External resource security
        9. Authentication mechanisms
        10. Data protection compliance

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific security issues"],
            "recommendations": ["list of security improvements"],
            "details": {{
                "https_score": <0-100>,
                "form_security": <0-100>,
                "xss_protection": <0-100>,
                "data_protection": <0-100>,
                "authentication_security": <0-100>,
                "overall_security_grade": "<A/B/C/D/F>"
            }}
        }}
        """

class BrandConsistencyAgent(BaseAIAgent):
    """Evaluates brand consistency and messaging alignment"""
    
    def __init__(self):
        super().__init__("Brand Consistency Agent", "gpt-4")
    
    def evaluate(self, page: PageContent, context: str = "") -> EvaluationResult:
        prompt = self._create_prompt(page, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a brand consistency expert. Analyze web page brand alignment and messaging consistency."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_data = self._parse_response(response.choices[0].message.content)
            
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.CONTENT_QUALITY,
                score=result_data.get("score", 50),
                issues=result_data.get("issues", []),
                recommendations=result_data.get("recommendations", []),
                details=result_data.get("details", {}),
                evaluator_agent=self.agent_name
            )
        except Exception as e:
            logger.error(f"Error in BrandConsistencyAgent: {e}")
            return EvaluationResult(
                url=page.url,
                evaluation_type=EvaluationType.CONTENT_QUALITY,
                score=0,
                issues=[f"Evaluation error: {str(e)}"],
                evaluator_agent=self.agent_name
            )
    
    def _create_prompt(self, page: PageContent, context: str) -> str:
        return f"""
        Analyze the brand consistency of this web page:

        URL: {page.url}
        Title: {page.title or "No title"}
        
        Content Context:
        {self.content_processor.create_context_for_ai(page)}

        Evaluate the following brand aspects:
        1. Tone of voice consistency
        2. Brand messaging alignment
        3. Visual identity consistency
        4. Value proposition clarity
        5. Brand personality expression
        6. Target audience alignment
        7. Competitive differentiation
        8. Brand story coherence
        9. Call-to-action brand alignment
        10. Overall brand experience

        Provide your analysis in JSON format:
        {{
            "score": <0-100>,
            "issues": ["list of specific brand consistency issues"],
            "recommendations": ["list of brand improvement suggestions"],
            "details": {{
                "tone_consistency": <0-100>,
                "messaging_alignment": <0-100>,
                "visual_consistency": <0-100>,
                "brand_personality": <0-100>,
                "audience_alignment": <0-100>,
                "differentiation_score": <0-100>
            }}
        }}
        """
