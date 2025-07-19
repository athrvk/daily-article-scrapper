#!/usr/bin/env python3
"""
Demo script showing enhanced image URL prioritization.
This demonstrates the improvements made to achieve 99% image coverage.
"""

import sys
import os
from unittest.mock import Mock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

from src.scraper import ArticleScraper
from config.settings import Config

def create_mock_feedparser_response():
    """Create a proper feedparser-style mock response."""
    from types import SimpleNamespace
    
    # Create mock entries with proper attribute access
    entry1 = SimpleNamespace()
    entry1.title = 'RSS Article with Media Content'
    entry1.link = 'https://mocktech.com/article1'
    entry1.published = '2025-01-13T12:00:00Z'
    entry1.summary = 'Article with media content image'
    
    # Mock media content
    media_obj = SimpleNamespace()
    media_obj.url = 'https://mocktech.com/media1.jpg'
    entry1.media_content = [media_obj]
    entry1.media_thumbnail = []
    entry1.enclosures = []
    entry1.links = []
    entry1.content = []
    entry1.description = ""
    entry1.tags = []
    
    # Add image field attributes
    for attr in ['image', 'featured_image', 'thumbnail', 'img', 'picture']:
        setattr(entry1, attr, "")
    
    entry2 = SimpleNamespace()
    entry2.title = 'RSS Article with HTML Image'
    entry2.link = 'https://mocktech.com/article2'
    entry2.published = '2025-01-13T11:00:00Z'
    entry2.summary = '<p>Article content <img src="https://mocktech.com/html-img.jpg" alt="test"> more content</p>'
    entry2.media_content = []
    entry2.media_thumbnail = []
    entry2.enclosures = []
    entry2.links = []
    entry2.content = []
    entry2.description = ""
    entry2.tags = []
    
    # Add image field attributes
    for attr in ['image', 'featured_image', 'thumbnail', 'img', 'picture']:
        setattr(entry2, attr, "")
    
    entry3 = SimpleNamespace()
    entry3.title = 'RSS Article without Image Initially'
    entry3.link = 'https://mocktech.com/article3'
    entry3.published = '2025-01-13T10:00:00Z'
    entry3.summary = 'Article without any image in RSS'
    entry3.media_content = []
    entry3.media_thumbnail = []
    entry3.enclosures = []
    entry3.links = []
    entry3.content = []
    entry3.description = ""
    entry3.tags = []
    
    # Add image field attributes
    for attr in ['image', 'featured_image', 'thumbnail', 'img', 'picture']:
        setattr(entry3, attr, "")
    
    # Create the main response object
    response = SimpleNamespace()
    response.bozo = False
    response.entries = [entry1, entry2, entry3]
    response.feed = SimpleNamespace()
    response.feed.title = 'Mock Tech News'
    response.feed.link = 'https://mocktech.com'
    
    return response

def create_mock_webpage_response():
    """Create mock webpage response with Open Graph image."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:image" content="https://mocktech.com/og-image.jpg">
        <meta name="twitter:image" content="https://mocktech.com/twitter-img.jpg">
        <title>Mock Article</title>
    </head>
    <body>
        <h1>Mock Article Content</h1>
        <img src="https://mocktech.com/article-img.jpg" alt="Article image">
    </body>
    </html>
    '''

def demo_enhanced_image_extraction():
    """Demonstrate enhanced image extraction capabilities."""
    print("🚀 Enhanced Image URL Extraction Demo")
    print("=" * 60)
    
    config = Config()
    scraper = ArticleScraper(config)
    
    # Show InShorts prioritization
    print("📊 InShorts API Prioritization")
    print("-" * 40)
    print(f"Total InShorts categories: {len(config.INSHORTS_CATEGORIES)}")
    
    total_inshorts_articles = sum(cat['max_limit'] for cat in config.INSHORTS_CATEGORIES.values())
    print(f"Maximum InShorts articles per run: {total_inshorts_articles}")
    
    sorted_categories = sorted(config.INSHORTS_CATEGORIES.items(), key=lambda x: x[1]['priority'])
    print("\nPriority order:")
    for category, settings in sorted_categories[:5]:  # Show top 5
        print(f"  {settings['priority']}. {category}: {settings['max_limit']} articles")
    
    # Mock InShorts response (with 100% image coverage)
    mock_inshorts_response = {
        'data': {
            'news_list': [
                {
                    'hash_id': 'enhanced-1',
                    'title': 'InShorts Article - Always has image',
                    'content': 'InShorts ensures all articles have images',
                    'source_name': 'TechCrunch',
                    'source_url': 'https://techcrunch.com/enhanced-article',
                    'image_url': 'https://assets.inshorts.com/enhanced-image.jpg',
                    'created_at': '2025-01-13T14:00:00Z',
                    'tags': ['technology', 'ai']
                }
            ]
        }
    }
    
    # Demo RSS image extraction improvements
    print("\n🔍 Enhanced RSS Image Extraction")
    print("-" * 40)
    
    mock_rss_data = create_mock_feedparser_response()
    
    with patch('feedparser.parse') as mock_parse:
        mock_parse.return_value = mock_rss_data
        
        articles = scraper.get_rss_articles('https://mocktech.com/rss', max_articles=3)
        
        print(f"Extracted {len(articles)} articles from RSS:")
        for i, article in enumerate(articles, 1):
            has_image = bool(article.get('image', '').strip())
            status = "✅" if has_image else "❌" 
            print(f"  {i}. {article['title'][:40]}... {status} Image: {article.get('image', 'None')[:50]}")
    
    # Demo webpage image extraction
    print("\n🌐 Webpage Image Extraction (Fallback)")
    print("-" * 40)
    
    mock_webpage = create_mock_webpage_response()
    
    with patch.object(scraper.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_webpage.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Test webpage image extraction
        test_url = "https://techcrunch.com/article3"  # Use trusted domain
        extracted_image = scraper._extract_image_from_webpage(test_url)
        
        print(f"Webpage: {test_url}")
        print(f"Extracted image: {extracted_image}")
    
    # Demo complete enhanced scraping
    print("\n🎯 Complete Enhanced Scraping Demo")
    print("-" * 40)
    
    # Create mixed articles (some with, some without images)
    test_articles = [
        {
            "title": "InShorts Article (100% image coverage)",
            "url": "https://inshorts.com/article1",
            "source": "inshorts.com", 
            "image": "https://assets.inshorts.com/image1.jpg",
            "summary": "InShorts provides guaranteed images",
            "published": "2025-01-13T15:00:00Z",
            "tags": ["news"]
        },
        {
            "title": "RSS Article with good image extraction",
            "url": "https://techcrunch.com/article2",
            "source": "techcrunch.com",
            "image": "https://techcrunch.com/wp-content/image2.jpg",
            "summary": "Enhanced RSS extraction found this image",
            "published": "2025-01-13T14:00:00Z", 
            "tags": ["tech"]
        },
        {
            "title": "Article without image (will be enhanced)",
            "url": "https://techcrunch.com/article3",  # Use trusted domain
            "source": "techcrunch.com",
            "image": "",
            "summary": "This article initially has no image",
            "published": "2025-01-13T13:00:00Z",
            "tags": ["news"]
        }
    ]
    
    print("Before enhancement:")
    images_before = sum(1 for article in test_articles if article.get('image', '').strip())
    print(f"  Articles with images: {images_before}/{len(test_articles)} ({images_before/len(test_articles)*100:.1f}%)")
    
    # Mock the webpage extraction for the article without image
    with patch.object(scraper.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_webpage.encode('utf-8')
        mock_get.return_value = mock_response
        
        enhanced_articles = scraper._enhance_articles_with_images(test_articles)
    
    print("After enhancement:")
    images_after = sum(1 for article in enhanced_articles if article.get('image', '').strip())
    print(f"  Articles with images: {images_after}/{len(enhanced_articles)} ({images_after/len(enhanced_articles)*100:.1f}%)")
    
    print("\nDetailed results:")
    for i, article in enumerate(enhanced_articles, 1):
        has_image = bool(article.get('image', '').strip())
        status = "✅" if has_image else "❌"
        print(f"  {i}. {article['title'][:45]}... {status}")
        if has_image:
            print(f"     Image: {article['image'][:60]}...")
    
    print("\n📈 Summary of Improvements")
    print("-" * 40)
    print(f"✅ InShorts prioritization: {total_inshorts_articles} articles (100% image coverage)")
    print("✅ Enhanced RSS image extraction with 8+ fallback mechanisms")
    print("✅ Improved Medium image extraction with lazy loading support")
    print("✅ Webpage fallback extraction from Open Graph and Twitter meta tags")
    print("✅ Comprehensive image URL validation and normalization")
    print("✅ Post-processing enhancement for articles without images")
    
    target_percentage = 99.0
    print(f"\n🎯 Target: {target_percentage}% image coverage")
    print("💡 Strategy: Prioritize InShorts (100% coverage) + Enhanced extraction for other sources")
    
    return enhanced_articles

if __name__ == "__main__":
    demo_enhanced_image_extraction()