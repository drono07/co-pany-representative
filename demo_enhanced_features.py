#!/usr/bin/env python3
"""
Demo script showing the enhanced features without requiring MongoDB
"""

import asyncio
from path_tracker import PathTracker
from html_structure_extractor import HTMLStructureExtractor
from change_detector import ChangeDetector

def demo_path_tracking():
    """Demonstrate path tracking functionality"""
    print("🛤️  PATH TRACKING DEMO")
    print("=" * 50)
    
    tracker = PathTracker()
    
    # Simulate a website crawl
    tracker.set_start_url("https://example.com")
    tracker.add_page_relationship("https://example.com", "https://example.com/products")
    tracker.add_page_relationship("https://example.com", "https://example.com/about")
    tracker.add_page_relationship("https://example.com/products", "https://example.com/products/electronics")
    tracker.add_page_relationship("https://example.com/products/electronics", "https://example.com/products/electronics/laptop")
    tracker.add_page_relationship("https://example.com/products/electronics", "https://example.com/products/electronics/phone")
    
    print("Navigation paths discovered:")
    paths = tracker.get_all_paths()
    for url, path in paths.items():
        depth = len(path) - 1
        print(f"  {url} (depth: {depth})")
        print(f"    Path: {' → '.join(path)}")
    
    print(f"\nPath statistics:")
    stats = tracker.get_path_statistics()
    print(f"  Total pages: {stats['total_pages']}")
    print(f"  Max depth: {stats['max_depth']}")
    print(f"  Pages by depth: {stats['pages_by_depth']}")
    
    print("\n" + "=" * 50)

def demo_html_extraction():
    """Demonstrate HTML structure extraction"""
    print("🏗️  HTML STRUCTURE EXTRACTION DEMO")
    print("=" * 50)
    
    extractor = HTMLStructureExtractor()
    
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>E-commerce Product Page</title>
        <meta name="description" content="Best laptop for developers">
        <style>body { font-family: Arial; }</style>
    </head>
    <body>
        <header>
            <nav>
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/contact">Contact</a>
            </nav>
        </header>
        
        <main>
            <h1>MacBook Pro 16-inch</h1>
            <h2>Features</h2>
            <ul>
                <li>M2 Pro chip</li>
                <li>16GB RAM</li>
                <li>512GB SSD</li>
            </ul>
            
            <h2>Specifications</h2>
            <p>This laptop is perfect for developers and creative professionals.</p>
            
            <form action="/cart/add" method="post">
                <input type="hidden" name="product_id" value="123">
                <input type="number" name="quantity" value="1" min="1">
                <button type="submit">Add to Cart</button>
            </form>
        </main>
        
        <footer>
            <p>&copy; 2024 Example Store</p>
        </footer>
    </body>
    </html>
    """
    
    structure = extractor.extract_structure(sample_html, "https://example.com/products/macbook-pro")
    
    print("Page Information:")
    print(f"  Title: {structure['page_info']['title']}")
    print(f"  Description: {structure['page_info']['meta_description']}")
    
    print(f"\nStructural Elements:")
    elements = structure['structure_elements']
    print(f"  Headings: {len(elements['headings'])}")
    for heading in elements['headings']:
        print(f"    {heading['tag'].upper()}: {heading['text']}")
    
    print(f"  Links: {len(elements['links'])}")
    for link in elements['links'][:3]:  # Show first 3
        print(f"    Link: {link['text']}")
    
    print(f"  Forms: {len(elements.get('forms', []))}")
    for form in elements.get('forms', []):
        print(f"    Form: {form['action']} ({form['method']})")
        print(f"      Inputs: {len(form['inputs'])}")
    
    print(f"  Lists: {len(elements['lists'])}")
    for list_item in elements['lists']:
        print(f"    {list_item['type'].upper()}: {list_item['item_count']} items")
    
    print("\n" + "=" * 50)

def demo_change_detection():
    """Demonstrate change detection functionality"""
    print("🔄 CHANGE DETECTION DEMO")
    print("=" * 50)
    
    detector = ChangeDetector()
    
    # Simulate current crawl (after some changes)
    current_pages = [
        {
            "url": "https://example.com/",
            "title": "Home Page",
            "word_count": 200,
            "page_type": "content",
            "path": ["https://example.com/"]
        },
        {
            "url": "https://example.com/products",
            "title": "Products - Updated",
            "word_count": 300,
            "page_type": "content",
            "path": ["https://example.com/", "https://example.com/products"]
        },
        {
            "url": "https://example.com/new-page",
            "title": "New Page",
            "word_count": 150,
            "page_type": "content",
            "path": ["https://example.com/", "https://example.com/new-page"]
        }
    ]
    
    # Simulate previous crawl (before changes)
    previous_pages = [
        {
            "url": "https://example.com/",
            "title": "Home Page",
            "word_count": 200,
            "page_type": "content",
            "path": ["https://example.com/"]
        },
        {
            "url": "https://example.com/products",
            "title": "Products",
            "word_count": 250,
            "page_type": "content",
            "path": ["https://example.com/", "https://example.com/products"]
        },
        {
            "url": "https://example.com/old-page",
            "title": "Old Page",
            "word_count": 100,
            "page_type": "content",
            "path": ["https://example.com/", "https://example.com/old-page"]
        }
    ]
    
    detector.set_current_pages(current_pages)
    detector.set_previous_pages(previous_pages)
    
    changes = detector.detect_changes()
    
    print("Change Detection Results:")
    print(f"  Current pages: {changes['current_pages_count']}")
    print(f"  Previous pages: {changes['previous_pages_count']}")
    
    print(f"\n🆕 New Pages ({len(changes['new_pages'])}):")
    for page in changes['new_pages']:
        print(f"    {page['url']} ({page['word_count']} words)")
    
    print(f"\n❌ Removed Pages ({len(changes['removed_pages'])}):")
    for page in changes['removed_pages']:
        print(f"    {page['url']} ({page['word_count']} words)")
    
    print(f"\n📝 Modified Pages ({len(changes['modified_pages'])}):")
    for page in changes['modified_pages']:
        print(f"    {page['url']}")
        for change in page['changes']:
            print(f"      • {change['type']}")
    
    print(f"\n📊 Summary:")
    summary = changes['summary']
    print(f"    Total changes: {summary['total_changes']}")
    print(f"    Impact level: {summary['impact_assessment'].upper()}")
    
    print("\n" + "=" * 50)

def demo_combined_features():
    """Demonstrate how all features work together"""
    print("🔗 COMBINED FEATURES DEMO")
    print("=" * 50)
    
    print("This is how the enhanced system works:")
    print("1. 🕷️  Crawl website and track navigation paths")
    print("2. 🏗️  Extract HTML structure (no CSS/images)")
    print("3. 💾 Store everything in MongoDB")
    print("4. 🔄 Compare with previous crawls")
    print("5. 📊 Generate comprehensive reports")
    
    print("\nBenefits:")
    print("✅ Track how users navigate your site")
    print("✅ Detect structural changes over time")
    print("✅ Monitor content quality and growth")
    print("✅ Identify broken links and blank pages")
    print("✅ Historical analysis and trending")
    
    print("\nUse cases:")
    print("• Website monitoring and health checks")
    print("• SEO analysis and optimization")
    print("• Content management and planning")
    print("• Development testing and QA")
    print("• Competitive analysis")
    
    print("\n" + "=" * 50)

async def main():
    """Run all demos"""
    print("🚀 ENHANCED WEBSITE ANALYSIS - FEATURE DEMO")
    print("=" * 60)
    
    # Run demos
    demo_path_tracking()
    demo_html_extraction()
    demo_change_detection()
    demo_combined_features()
    
    print("\n🎯 NEXT STEPS")
    print("=" * 50)
    print("1. Install MongoDB: https://docs.mongodb.com/manual/installation/")
    print("2. Install dependencies: pip install -r requirements_mongodb.txt")
    print("3. Setup database: python setup_mongodb.py")
    print("4. Run enhanced analysis: python main.py 'http://localhost:8000' --depth 2")
    print("5. Check the generated report for path tracking and change detection")
    
    print("\n💡 TIP: Use your localhost website for testing!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
