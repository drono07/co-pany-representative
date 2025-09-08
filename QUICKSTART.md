# 🚀 Quick Start Guide

## Installation Complete! ✅

Your Website Insights Platform is now ready to use. Here's how to get started:

## 1. Set Up Your OpenAI API Key

Edit the `.env` file and add your OpenAI API key:

```bash
# Copy the example file if you haven't already
cp env.example .env

# Edit the .env file
nano .env
```

Add your API key:
```env
OPENAI_API_KEY=your_actual_api_key_here
MAX_CRAWL_DEPTH=3
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
USER_AGENT=WebsiteInsightsBot/1.0
```

## 2. Activate Virtual Environment

Always activate the virtual environment before using the platform:

```bash
source venv/bin/activate
```

## 3. Run Your First Analysis

### Basic Analysis
```bash
python main.py https://example.com
```

### Advanced Analysis
```bash
python main.py https://example.com --depth 5 --output my_report.json
```

### Try the Examples
```bash
python example.py
```

## 4. Understanding the Output

The platform will:
1. **Crawl** the website and discover all pages
2. **Validate** all links for broken links
3. **Analyze** content quality and structure
4. **Run AI evaluations** across 8 different dimensions
5. **Generate** a comprehensive report

### Sample Output:
```
🔍 Starting analysis of https://example.com
Step 1: Crawling website...
Step 2: Validating links...
Step 3: Detecting blank pages...
Step 4: Processing content...
Step 5: Running AI evaluations...

============================================================
WEBSITE ANALYSIS SUMMARY
============================================================
Website: https://example.com
Overall Score: 75.5/100

PAGE ANALYSIS:
  Total Pages: 25
  Total Links: 150
  Broken Links: 3
  Blank Pages: 2

SCORES BY CATEGORY:
  Content Quality: 80.0/100
  Design Layout: 70.0/100
  Accessibility: 85.0/100
  SEO: 75.0/100
  Technical: 65.0/100

CRITICAL ISSUES:
  ⚠️  Security vulnerability found
  ⚠️  Broken checkout link

HIGH PRIORITY RECOMMENDATIONS:
  ✅ Fix security issues immediately
  ✅ Add missing alt text
  ✅ Improve heading structure
```

## 5. AI Evaluation Agents

The platform includes 8 specialized AI agents:

1. **Content Quality Agent** - Evaluates content depth and readability
2. **Design & Layout Agent** - Analyzes visual hierarchy and spacing
3. **Accessibility Agent** - WCAG compliance and usability
4. **SEO Agent** - Search engine optimization
5. **Technical Performance Agent** - Code quality and performance
6. **Conversion Optimization Agent** - User experience and conversions
7. **Security Agent** - Vulnerability assessment
8. **Brand Consistency Agent** - Brand messaging alignment

## 6. Report Files

Reports are saved as JSON files with detailed analysis including:
- Overall website score
- Category-specific scores
- Critical/major/minor issues
- Priority-based recommendations
- Action plans with effort estimates
- Agent performance metrics

## 7. Configuration Options

You can customize the analysis by editing the `.env` file:

- `MAX_CRAWL_DEPTH` - How deep to crawl (default: 3)
- `MAX_CONCURRENT_REQUESTS` - Concurrent requests (default: 10)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)

## 8. Troubleshooting

### Common Issues:

1. **"OpenAI API key not found"**
   - Make sure you've set `OPENAI_API_KEY` in your `.env` file

2. **"Analysis failed"**
   - Check your internet connection
   - Verify the website URL is accessible
   - Try reducing `MAX_CRAWL_DEPTH` for large websites

3. **"Module not found"**
   - Make sure you've activated the virtual environment: `source venv/bin/activate`

### Getting Help:

- Check the logs in `website_insights.log`
- Run the test script: `python test_installation.py`
- Read the full documentation in `README.md`

## 9. Next Steps

- Try analyzing different types of websites
- Experiment with different crawl depths
- Use the programmatic API for integration
- Customize the evaluation criteria
- Add your own evaluation agents

## 🎯 Example Use Cases

- **Website Health Check** - Identify broken links and technical issues
- **SEO Audit** - Analyze on-page SEO factors
- **Accessibility Compliance** - WCAG compliance assessment
- **Content Quality Review** - Evaluate content depth and value
- **Security Assessment** - Identify potential vulnerabilities
- **Conversion Optimization** - Analyze user experience factors

Happy analyzing! 🚀
