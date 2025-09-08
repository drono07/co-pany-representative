#!/usr/bin/env python3
"""
Professional Demo Script for Website Analysis Platform
This script demonstrates all the key features of the platform
"""

import asyncio
import time
import os
import sys
from pathlib import Path

def print_banner():
    """Print a professional banner"""
    print("=" * 80)
    print("🚀 WEBSITE ANALYSIS PLATFORM - PROFESSIONAL DEMO")
    print("=" * 80)
    print("📊 Comprehensive Website Analysis & Quality Assessment")
    print("🔍 Link Validation | 📄 Content Analysis | 🤖 AI Evaluation")
    print("=" * 80)

def print_section(title, description=""):
    """Print a section header"""
    print(f"\n🎯 {title}")
    if description:
        print(f"   {description}")
    print("-" * 60)

def print_feature(feature, status="✅"):
    """Print a feature with status"""
    print(f"   {status} {feature}")

def wait_for_user(message="Press Enter to continue..."):
    """Wait for user input"""
    input(f"\n⏸️  {message}")

def run_demo_analysis(url, depth=1):
    """Run the analysis and return results"""
    print(f"🔍 Analyzing: {url}")
    print(f"📏 Depth: {depth}")
    
    # Import here to avoid issues if main.py has problems
    try:
        from main import WebsiteAnalyzer
        analyzer = WebsiteAnalyzer()
        result = analyzer.analyze_website(url, depth)
        return result
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

def main():
    """Main demo function"""
    print_banner()
    
    print_section("DEMO OVERVIEW", "This demo showcases the Website Analysis Platform capabilities")
    
    print("🎯 Key Features Demonstrated:")
    print_feature("Website Crawling & Link Discovery")
    print_feature("Broken Link Detection (4xx, 5xx errors)")
    print_feature("Blank Page Detection (header/footer only)")
    print_feature("Content Quality Analysis")
    print_feature("AI-Powered Evaluation (8 specialized agents)")
    print_feature("Comprehensive Reporting")
    print_feature("Rate Limiting Handling")
    print_feature("Parallel Processing for Speed")
    
    wait_for_user("Ready to start the demo?")
    
    # Demo 1: Local Test Website
    print_section("DEMO 1: LOCAL TEST WEBSITE", "Testing with our controlled demo environment")
    
    print("🌐 Starting local demo website server...")
    print("📁 Demo website includes:")
    print_feature("Rich content pages (Home, About, Services)")
    print_feature("Blank pages (header/footer only)")
    print_feature("Empty pages (minimal content)")
    print_feature("Broken links (404 errors)")
    print_feature("Various content types for testing")
    
    wait_for_user("Start the demo website server?")
    
    # Start the demo server
    import subprocess
    import threading
    import http.server
    import socketserver
    import os
    
    def start_server():
        os.chdir('demo_website')
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", 8080), handler) as httpd:
            httpd.serve_forever()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print("✅ Demo server started at http://localhost:8080")
    print("🌐 You can visit the website in your browser to see the pages")
    
    wait_for_user("Ready to analyze the demo website?")
    
    # Run analysis on demo website
    print_section("RUNNING ANALYSIS", "Analyzing the demo website...")
    
    result = run_demo_analysis("http://localhost:8080", depth=1)
    
    if result:
        print("✅ Analysis completed successfully!")
        print(f"📊 Results saved to: {result}")
        print(f"📁 Full path: {os.path.abspath(result)}")
        
        # Show summary
        print_section("ANALYSIS RESULTS", "Key findings from the demo website")
        
        # Parse the results file to show summary
        try:
            import json
            with open(result, 'r') as f:
                data = json.load(f)
            
            print(f"📄 Total Pages Found: {data.get('summary', {}).get('total_pages', 'N/A')}")
            print(f"🔗 Total Links Found: {data.get('summary', {}).get('total_links', 'N/A')}")
            print(f"❌ Broken Links: {data.get('summary', {}).get('broken_links', 'N/A')}")
            print(f"📝 Blank Pages: {data.get('summary', {}).get('blank_pages', 'N/A')}")
            print(f"📊 Overall Score: {data.get('summary', {}).get('overall_score', 'N/A')}")
            
            # Show some issues
            issues = data.get('issues', {})
            if issues.get('critical'):
                print(f"\n🚨 Critical Issues Found: {len(issues['critical'])}")
                for issue in issues['critical'][:3]:  # Show first 3
                    print(f"   • {issue}")
            
            if issues.get('major'):
                print(f"\n⚠️  Major Issues Found: {len(issues['major'])}")
                for issue in issues['major'][:3]:  # Show first 3
                    print(f"   • {issue}")
                    
        except Exception as e:
            print(f"⚠️  Could not parse results: {e}")
    
    wait_for_user("Ready to test with a real website?")
    
    # Demo 2: Real Website
    print_section("DEMO 2: REAL WEBSITE ANALYSIS", "Testing with a live website")
    
    print("🌐 Available test websites:")
    print("   1. httpbin.org (Simple, fast)")
    print("   2. example.com (Basic website)")
    print("   3. http://localhost:8080 (Our demo site)")
    
    choice = input("\n🎯 Enter website URL to analyze (or press Enter for httpbin.org): ").strip()
    if not choice:
        choice = "https://httpbin.org"
    
    print(f"\n🔍 Analyzing: {choice}")
    print("⏳ This may take a few moments...")
    
    result = run_demo_analysis(choice, depth=1)
    
    if result:
        print("✅ Real website analysis completed!")
        print(f"📊 Results saved to: {result}")
        print(f"📁 Full path: {os.path.abspath(result)}")
    
    # Demo 3: Show advanced features
    print_section("ADVANCED FEATURES", "Platform capabilities and configuration")
    
    print("⚙️  Configuration Options:")
    print_feature("Configurable crawl depth")
    print_feature("Parallel processing control")
    print_feature("Rate limiting handling")
    print_feature("AI evaluation enable/disable")
    print_feature("Custom user agents")
    print_feature("Timeout settings")
    
    print("\n🤖 AI Agents Available:")
    print_feature("Content Quality Agent")
    print_feature("Design & Layout Agent")
    print_feature("Accessibility Agent")
    print_feature("SEO Agent")
    print_feature("Performance Agent")
    print_feature("Security Agent")
    print_feature("User Experience Agent")
    print_feature("Technical Agent")
    
    print("\n📊 Report Features:")
    print_feature("Detailed JSON reports")
    print_feature("Issue categorization")
    print_feature("Recommendations")
    print_feature("Performance metrics")
    print_feature("Debug information")
    
    wait_for_user("Ready to see the final summary?")
    
    # Final summary
    print_section("DEMO COMPLETE", "Thank you for watching the demo!")
    
    print("🎉 What you've seen:")
    print_feature("Complete website crawling and analysis")
    print_feature("Broken link detection and validation")
    print_feature("Blank page identification")
    print_feature("Content quality assessment")
    print_feature("Professional reporting system")
    print_feature("Scalable architecture")
    
    print("\n🚀 Next Steps:")
    print("   1. Review the generated reports")
    print("   2. Test with your own websites")
    print("   3. Configure AI agents for your needs")
    print("   4. Integrate with your workflow")
    
    print("\n📞 Contact & Support:")
    print("   • Documentation: README.md")
    print("   • Quick Start: QUICKSTART.md")
    print("   • Configuration: config.py")
    
    print("\n" + "=" * 80)
    print("🎯 DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        sys.exit(1)
