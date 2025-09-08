# Website Insights Platform

A comprehensive website analysis platform that crawls websites, identifies issues, and provides AI-powered evaluations across multiple dimensions including content quality, design, accessibility, SEO, technical performance, security, and more.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [🎯 Local Demo Website Testing](#-local-demo-website-testing)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output Format](#output-format)
- [Troubleshooting](#troubleshooting)
- [🚀 Quick Demo Commands](#-quick-demo-commands)
- [Roadmap](#roadmap)

## Features

### 🔍 **Website Crawling**
- Recursive crawling of all internal links
- Configurable depth limits
- Concurrent request handling
- Duplicate link detection
- Response time tracking

### 🔗 **Link Validation**
- Automatic detection of broken links (4xx, 5xx status codes)
- Link status categorization (valid, broken, redirect, timeout)
- Response time analysis
- Error message capture

### 📄 **Content Analysis**
- Blank page detection (pages with only header/footer)
- Content quality assessment
- HTML to Markdown conversion
- Content chunking for AI processing
- Word count and structure analysis

### 🤖 **AI-Powered Evaluation Agents**

#### 1. **Content Quality Agent**
- Evaluates content depth and substance
- Analyzes readability and clarity
- Assesses information value and usefulness
- Checks grammar and writing quality
- Reviews content structure and organization

#### 2. **Design & Layout Agent**
- Analyzes visual hierarchy and spacing
- Evaluates layout consistency
- Reviews header/footer design
- Assesses navigation structure
- Checks white space usage and typography

#### 3. **Accessibility Agent**
- WCAG compliance assessment
- Semantic HTML structure analysis
- Alt text coverage evaluation
- Heading hierarchy review
- Keyboard navigation support
- Screen reader compatibility

#### 4. **SEO Agent**
- Title tag optimization
- Meta description analysis
- Heading structure evaluation
- Keyword density assessment
- Internal linking analysis
- Schema markup detection

#### 5. **Technical Performance Agent**
- HTML structure validation
- CSS organization analysis
- JavaScript implementation review
- Performance optimization indicators
- Security considerations
- Mobile optimization assessment

#### 6. **Conversion Optimization Agent**
- Call-to-action effectiveness
- Value proposition clarity
- Trust signals evaluation
- User journey optimization
- Form design analysis
- Mobile conversion experience

#### 7. **Security Agent**
- HTTPS implementation
- Form security (CSRF protection)
- XSS vulnerability assessment
- Input validation review
- Content Security Policy analysis
- Authentication mechanisms

#### 8. **Brand Consistency Agent**
- Tone of voice consistency
- Brand messaging alignment
- Visual identity consistency
- Target audience alignment
- Competitive differentiation
- Brand story coherence

### 📊 **Comprehensive Reporting**
- Overall website score calculation
- Category-specific scores
- Priority-based issue categorization
- Actionable recommendations
- Detailed findings and metrics
- Phased action plan generation

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd website-insights
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp env.example .env
# Edit .env and add your OpenAI API key
```

4. **Configure settings**
Edit the `.env` file with your preferences:
```env
OPENAI_API_KEY=your_openai_api_key_here
MAX_CRAWL_DEPTH=3
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
USER_AGENT=WebsiteInsightsBot/1.0

# AI Evaluation Settings
ENABLE_AI_EVALUATION=true
MAX_AI_EVALUATION_PAGES=10

# Non-AI Analysis Settings (always run for all pages)
ENABLE_LINK_VALIDATION=true
ENABLE_BLANK_PAGE_DETECTION=true
ENABLE_CONTENT_ANALYSIS=true
```

## 🎯 Local Demo Website Testing

### **Demo Overview**
The platform includes a professional demo website (`demo_website/`) designed to showcase all analysis features including:
- Rich content pages
- Blank pages (header/footer only)
- Empty pages (minimal content)
- Broken links (404 errors)
- Various content types for comprehensive testing

### **🚀 Quick Demo Setup**

#### **Option 1: Interactive Demo Script**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the interactive demo
python demo_script.py
```

#### **Option 2: Manual Demo**
```bash
# Start demo website server
cd demo_website
python -m http.server 8080 &

# Run analysis (in new terminal)
cd ..
source venv/bin/activate
python main.py "http://localhost:8080" --depth 1
```

### **🌐 Demo Website Pages**

| Page | URL | Content Type | Purpose |
|------|-----|--------------|---------|
| **Home** | `http://localhost:8080/` | Rich Content (200+ words) | Shows good content detection |
| **About** | `http://localhost:8080/about.html` | Rich Content (500+ words) | Demonstrates comprehensive content |
| **Services** | `http://localhost:8080/services.html` | Rich Content (200+ words) | Shows service page analysis |
| **Blank Page** | `http://localhost:8080/blank-page.html` | Blank (39 words) | Tests blank page detection |
| **Empty Page** | `http://localhost:8080/empty-page.html` | Empty (41 words) | Tests minimal content detection |
| **Broken Links** | Various 404 pages | Broken (404 errors) | Tests broken link detection |

### **📊 Expected Demo Results**

When analyzing the demo website, you should see:

```
================================================================================
WEBSITE ANALYSIS SUMMARY
================================================================================
Website: http://localhost:8080
Overall Score: 0.0/100

PAGE ANALYSIS:
  Total Pages: 6
  Total Links: 17
  Broken Links: 11
  Rate Limited Links: 0
  Blank Pages: 2
  Content Pages: 2
  AI Evaluated Pages: 0

CRITICAL ISSUES:
  ⚠️  Broken link (HTTP 404): http://localhost:8080/portfolio.html
  ⚠️  Broken link (HTTP 404): http://localhost:8080/pricing.html
  ⚠️  Broken link (HTTP 404): http://localhost:8080/contact.html

MAJOR ISSUES:
  ⚠️  Blank page (only 39 words): http://localhost:8080/blank-page.html
  ⚠️  Blank page (only 41 words): http://localhost:8080/empty-page.html
```

### **📁 Demo Results Storage**

Results are saved to:
- **Main Report**: `website_analysis_localhost:8080_YYYYMMDD_HHMMSS.json`
- **Debug Files**: `debug_output/` directory
- **Full Path**: `/Users/dhruvyadav/Desktop/website-insights/`

### **🎬 Demo Presentation Guide**

#### **Step 1: Show Demo Website (2 minutes)**
1. Open browser to `http://localhost:8080`
2. Navigate through different pages:
   - Home page (rich content)
   - About page (comprehensive content)
   - Services page (moderate content)
   - Blank page (header/footer only)
   - Empty page (minimal content)
3. Show navigation with broken links

#### **Step 2: Run Analysis (1 minute)**
```bash
python main.py "http://localhost:8080" --depth 1
```
- Show real-time crawling progress
- Highlight speed (3-second analysis)
- Display comprehensive discovery

#### **Step 3: Review Results (3 minutes)**
- Show summary statistics
- Explain broken link detection (11 found)
- Highlight blank page identification (2 found)
- Display content page recognition (2 found)
- Show actionable recommendations

#### **Step 4: Show Report (2 minutes)**
- Open JSON report file
- Show detailed findings
- Explain issue categorization
- Highlight recommendations

### **💼 Demo Talking Points**

- **"Watch as we discover 6 pages and 17 links in just 3 seconds"**
- **"Notice how it automatically identifies 11 broken links"**
- **"See how it detects 2 blank pages that need content"**
- **"The system provides specific recommendations for each issue"**
- **"This analysis would take hours to do manually"**

### **🔧 Demo Troubleshooting**

#### **Common Issues:**
1. **Port 8080 in use**: Change port in demo script
2. **Server not starting**: Check if Python is installed
3. **Analysis fails**: Ensure virtual environment is activated
4. **Browser can't connect**: Verify server is running

#### **Backup Plans:**
- Have pre-generated reports ready
- Use screenshots of previous analyses
- Show configuration options
- Demonstrate with real websites

### **📈 Demo Success Metrics**

- ✅ **Fast Analysis**: 3-second analysis of 6 pages
- ✅ **Accurate Detection**: 11 broken links, 2 blank pages
- ✅ **Clear Results**: Easy to understand summary
- ✅ **Professional Output**: Formatted reports
- ✅ **No Technical Issues**: Smooth execution
- ✅ **Realistic Scenarios**: Mix of good and bad pages

### **🎯 Client Value Demonstration**

1. **Time Savings**: Manual checking vs automated analysis
2. **Comprehensive Coverage**: Finds issues humans might miss
3. **Actionable Insights**: Clear recommendations for improvement
4. **Professional Reports**: Detailed JSON with categorization
5. **Scalable Solution**: Works for any website size

## Usage

### Command Line Interface

**Basic analysis:**
```bash
python main.py https://example.com
```

**Advanced analysis with custom depth:**
```bash
python main.py https://example.com --depth 5 --screenshots
```

**Save report to specific file:**
```bash
python main.py https://example.com --output my_report.json
```

**Quiet mode (no console output):**
```bash
python main.py https://example.com --quiet
```

### Programmatic Usage

```python
import asyncio
from main import WebsiteInsightsPlatform

async def analyze_website():
    platform = WebsiteInsightsPlatform()
    report = await platform.analyze_website("https://example.com")
    
    # Save report
    platform.save_report(report, "analysis_report.json")
    
    # Print summary
    platform.print_summary(report)

# Run analysis
asyncio.run(analyze_website())
```

## Configuration Options

### Crawling Settings
- `MAX_CRAWL_DEPTH`: Maximum depth for recursive crawling (default: 3)
- `MAX_CONCURRENT_REQUESTS`: Number of concurrent requests (default: 10)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `USER_AGENT`: User agent string for requests

### AI Evaluation Settings
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `ENABLE_AI_EVALUATION`: Enable/disable AI evaluation (default: true)
- `MAX_AI_EVALUATION_PAGES`: Maximum pages for AI evaluation (default: 10)
- Model selection: GPT-4 for most agents, GPT-4-Vision for design analysis

### Non-AI Analysis Settings
- `ENABLE_LINK_VALIDATION`: Enable broken link detection (default: true)
- `ENABLE_BLANK_PAGE_DETECTION`: Enable blank page detection (default: true)
- `ENABLE_CONTENT_ANALYSIS`: Enable content processing (default: true)

**Note**: Non-AI analysis runs on ALL discovered pages, while AI evaluation is limited to the configured number of pages for cost and performance reasons.

## Output Format

The platform generates comprehensive JSON reports containing:

```json
{
  "website_url": "https://example.com",
  "analysis_date": "2024-01-15T10:30:00",
  "overall_score": 75.5,
  "summary": {
    "total_pages_analyzed": 25,
    "total_links_found": 150,
    "broken_links": 3,
    "blank_pages": 2
  },
  "scores_by_category": {
    "content_quality": 80.0,
    "design_layout": 70.0,
    "accessibility": 85.0,
    "seo": 75.0,
    "technical": 65.0
  },
  "issues": {
    "critical": ["Security vulnerability found", "Broken checkout link"],
    "major": ["Missing alt text on images", "Poor heading structure"],
    "minor": ["Long page titles", "Inconsistent spacing"]
  },
  "recommendations": {
    "high_priority": ["Fix security issues immediately", "Add missing alt text"],
    "medium_priority": ["Improve heading structure", "Optimize page titles"],
    "low_priority": ["Enhance visual consistency", "Add more internal links"]
  },
  "action_plan": [
    {
      "phase": "Immediate (1-3 days)",
      "priority": "Critical",
      "actions": ["Fix security vulnerabilities", "Repair broken links"],
      "estimated_effort": "High",
      "expected_impact": "High"
    }
  ]
}
```

## Common Use Cases

### 1. **Website Health Check**
- Identify broken links and technical issues
- Assess overall website performance
- Get prioritized action plan

### 2. **SEO Audit**
- Analyze on-page SEO factors
- Identify optimization opportunities
- Review content structure and quality

### 3. **Accessibility Compliance**
- WCAG compliance assessment
- Screen reader compatibility
- Keyboard navigation support

### 4. **Content Quality Review**
- Evaluate content depth and value
- Check grammar and readability
- Assess brand consistency

### 5. **Security Assessment**
- Identify potential vulnerabilities
- Review security best practices
- Check for common security issues

### 6. **Conversion Optimization**
- Analyze user experience factors
- Evaluate call-to-action effectiveness
- Review trust signals and credibility

## Advanced Features

### Multi-Agent Evaluation System
- Parallel processing of multiple evaluation agents
- Weighted scoring system
- Comprehensive issue categorization
- Priority-based recommendations

### Content Processing
- Intelligent content chunking
- HTML to Markdown conversion
- Semantic content analysis
- Token-optimized processing

### Screenshot Analysis (Future)
- Visual design evaluation
- Layout consistency checking
- Mobile responsiveness assessment

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is correctly set in the `.env` file
   - Verify you have sufficient API credits

2. **Crawling Timeout**
   - Increase `REQUEST_TIMEOUT` in configuration
   - Reduce `MAX_CONCURRENT_REQUESTS`
   - Check if the website blocks automated requests

3. **Memory Issues with Large Websites**
   - Reduce `MAX_CRAWL_DEPTH`
   - Process websites in smaller batches
   - Increase system memory

### Performance Optimization

- Use appropriate `MAX_CONCURRENT_REQUESTS` for your system
- Adjust `MAX_CRAWL_DEPTH` based on website size
- Monitor API usage and costs
- Use caching for repeated analyses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `website_insights.log`
3. Open an issue on GitHub
4. Contact the development team

## 🚀 Quick Demo Commands

### **Start Demo Website**
```bash
cd demo_website
python -m http.server 8080 &
```

### **Run Analysis**
```bash
python main.py "http://localhost:8080" --depth 1
```

### **Interactive Demo**
```bash
python demo_script.py
```

### **Expected Results**
- **Pages**: 6 pages discovered
- **Links**: 17 links found
- **Issues**: 11 broken links, 2 blank pages
- **Time**: ~3 seconds
- **Report**: `website_analysis_localhost:8080_YYYYMMDD_HHMMSS.json`

## Roadmap

- [ ] Screenshot capture and analysis
- [ ] Performance metrics integration
- [ ] Database storage for historical analysis
- [ ] Web interface for report visualization
- [ ] API endpoints for integration
- [ ] Batch processing capabilities
- [ ] Custom evaluation criteria
- [ ] Integration with popular CMS platforms
