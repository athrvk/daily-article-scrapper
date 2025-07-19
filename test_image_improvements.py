#!/usr/bin/env python3
"""
Test script to validate image URL improvements.
Tests the enhanced image extraction capabilities.
"""

import sys
import os
from unittest.mock import Mock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

from src.scraper import ArticleScraper
from config.settings import Config

def test_image_validation():
    """Test image URL validation logic."""
    print("🔍 Testing Image URL Validation")
    print("-" * 40)
    
    scraper = ArticleScraper(Config())
    
    test_urls = [
        ("https://example.com/image.jpg", True),
        ("https://example.com/image.png", True),
        ("http://example.com/image.gif", True),
        ("//example.com/image.webp", True),
        ("", False),
        ("not-a-url", False),
        ("https://example.com/document.pdf", False),
        ("https://localhost/image.jpg", False),
        ("abc", False),
    ]
    
    for url, expected in test_urls:
        result = scraper._is_valid_image_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url[:50]:<50} -> {result} (expected {expected})")

def test_rss_image_extraction():
    """Test enhanced RSS image extraction."""
    print("\n🔍 Testing RSS Image Extraction")
    print("-" * 40)
    
    scraper = ArticleScraper(Config())
    
    # Mock RSS entry with various image sources
    mock_entry = Mock()
    
    # Test 1: media:content
    mock_media = Mock()
    mock_media.url = "https://example.com/media-content.jpg"
    mock_entry.media_content = [mock_media]
    mock_entry.media_thumbnail = []
    mock_entry.enclosures = []
    mock_entry.links = []
    mock_entry.summary = ""
    mock_entry.content = []
    mock_entry.description = ""
    mock_entry.link = ""
    # Add missing attributes
    for attr in ['image', 'featured_image', 'thumbnail', 'img', 'picture']:
        setattr(mock_entry, attr, "")
    
    result = scraper._extract_image_from_rss_entry(mock_entry)
    print(f"Media content test: {result}")
    
    # Test 2: HTML img tag in summary
    mock_entry2 = Mock()
    mock_entry2.media_content = []
    mock_entry2.media_thumbnail = []
    mock_entry2.enclosures = []
    mock_entry2.links = []
    mock_entry2.summary = '<p>Article text <img src="https://example.com/summary-image.jpg" alt="test"> more text</p>'
    mock_entry2.content = []
    mock_entry2.description = ""
    mock_entry2.link = ""
    # Add missing attributes
    for attr in ['image', 'featured_image', 'thumbnail', 'img', 'picture']:
        setattr(mock_entry2, attr, "")
    
    result2 = scraper._extract_image_from_rss_entry(mock_entry2)
    print(f"HTML summary test: {result2}")

def test_inshorts_priority():
    """Test InShorts prioritization."""
    print("\n🔍 Testing InShorts Priority Configuration")
    print("-" * 40)
    
    config = Config()
    
    print(f"Total InShorts categories: {len(config.INSHORTS_CATEGORIES)}")
    print("Categories with limits:")
    
    total_articles = 0
    for category, settings in config.INSHORTS_CATEGORIES.items():
        limit = settings["max_limit"]
        priority = settings["priority"]
        total_articles += limit
        print(f"  {category}: {limit} articles (priority {priority})")
    
    print(f"Total potential InShorts articles: {total_articles}")

def test_enhanced_scraping_mock():
    """Test the enhanced scraping with mocked data."""
    print("\n🔍 Testing Enhanced Scraping (Mocked)")
    print("-" * 40)
    
    # Mock various article types
    mock_articles = [
        {
            "title": "InShorts Article with Image",
            "url": "https://example.com/article1",
            "source": "inshorts.com",
            "image": "https://assets.inshorts.com/image1.jpg",
            "summary": "Test summary",
            "published": "2025-01-13T12:00:00Z",
            "tags": ["news"]
        },
        {
            "title": "RSS Article without Image",
            "url": "https://example.com/article2",
            "source": "techcrunch.com",
            "image": "",
            "summary": "Test summary",
            "published": "2025-01-13T11:00:00Z",
            "tags": ["tech"]
        },
        {
            "title": "Medium Article with Image",
            "url": "https://medium.com/article3",
            "source": "medium.com",
            "image": "https://miro.medium.com/image3.jpg",
            "summary": "Test summary",
            "published": "2025-01-13T10:00:00Z",
            "tags": ["medium"]
        }
    ]
    
    scraper = ArticleScraper(Config())
    
    # Test image enhancement
    enhanced = scraper._enhance_articles_with_images(mock_articles)
    
    print(f"Original articles: {len(mock_articles)}")
    print(f"Enhanced articles: {len(enhanced)}")
    
    images_before = sum(1 for article in mock_articles if article.get('image', '').strip())
    images_after = sum(1 for article in enhanced if article.get('image', '').strip())
    
    print(f"Images before: {images_before}/{len(mock_articles)} ({images_before/len(mock_articles)*100:.1f}%)")
    print(f"Images after: {images_after}/{len(enhanced)} ({images_after/len(enhanced)*100:.1f}%)")

def main():
    """Run all tests."""
    print("🚀 Testing Image URL Improvements")
    print("=" * 50)
    
    test_image_validation()
    test_rss_image_extraction() 
    test_inshorts_priority()
    test_enhanced_scraping_mock()
    
    print("\n✅ All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()