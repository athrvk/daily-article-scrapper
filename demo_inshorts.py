#!/usr/bin/env python3
"""
Demo script showing InShorts API integration.
This demonstrates how the new InShorts functionality works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

from unittest.mock import Mock, patch
from src.scraper import ArticleScraper
from config.settings import Config

def demo_inshorts_integration():
    """Demonstrate InShorts API integration."""
    print("🚀 InShorts API Integration Demo")
    print("=" * 50)
    
    # Mock response to simulate InShorts API
    mock_inshorts_response = {
        'data': {
            'news_list': [
                {
                    'hash_id': 'demo-hash-1',
                    'title': 'India launches new satellite mission',
                    'content': 'India successfully launched a new satellite mission today, marking another milestone in space exploration.',
                    'source_name': 'The Times of India',
                    'source_url': 'https://timesofindia.indiatimes.com/india/space-mission-launch/articleshow/demo1.cms',
                    'image_url': 'https://assets.inshorts.com/news_images/satellite_launch.jpg',
                    'created_at': '2025-01-13T12:30:00Z',
                    'tags': ['space', 'technology', 'india']
                },
                {
                    'hash_id': 'demo-hash-2',
                    'title': 'AI breakthrough in healthcare announced',
                    'content': 'Researchers announce a major breakthrough in AI-powered medical diagnosis, potentially revolutionizing healthcare.',
                    'source_name': 'Reuters',
                    'source_url': 'https://www.reuters.com/technology/artificial-intelligence/ai-healthcare-breakthrough-2025-01-13/',
                    'image_url': 'https://assets.inshorts.com/news_images/ai_healthcare.jpg',
                    'created_at': '2025-01-13T11:45:00Z',
                    'tags': ['ai', 'healthcare', 'technology']
                },
                {
                    'hash_id': 'demo-hash-3',
                    'title': 'Global climate summit reaches agreement',
                    'content': 'World leaders reach a historic agreement on climate action at the annual summit, setting ambitious targets for 2030.',
                    'source_name': 'BBC',
                    'source_url': 'https://www.bbc.com/news/world-climate-summit-agreement-demo',
                    'image_url': 'https://assets.inshorts.com/news_images/climate_summit.jpg',
                    'created_at': '2025-01-13T10:15:00Z',
                    'tags': ['climate', 'environment', 'politics']
                }
            ]
        }
    }
    
    # Create scraper with real config
    config = Config()
    scraper = ArticleScraper(config=config)
    
    # Mock the session.get method
    with patch.object(scraper.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_inshorts_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        print("📱 Fetching articles from InShorts API...")
        print()
        
        # Demonstrate category-specific scraping
        categories = ['top_stories', 'trending', 'technology']
        for category in categories:
            print(f"📊 Category: {category.upper()}")
            print("-" * 30)
            
            articles = scraper._fetch_inshorts_category(category, 3)
            
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article['title']}")
                print(f"   🔗 URL: {article['url']}")
                print(f"   📰 Original Source: {article['original_source']}")
                print(f"   🏷️  Tags: {', '.join(article['tags'])}")
                print(f"   🖼️  Image: {article['image']}")
                print(f"   📅 Published: {article['published']}")
                print()
            
            print()
        
        # Demonstrate full InShorts integration
        print("🎯 Full InShorts Integration Demo")
        print("-" * 40)
        
        all_articles = scraper.scrape_inshorts_articles(['top_stories', 'trending'])
        
        print(f"Total articles retrieved: {len(all_articles)}")
        print()
        
        print("📋 Article Summary:")
        for i, article in enumerate(all_articles, 1):
            print(f"{i}. {article['title'][:60]}...")
            print(f"   Source: {article['source']} (from {article['original_source']})")
            print(f"   ID: {article['inshorts_id']}")
            print()
        
        # Demonstrate trending topics
        mock_topics_response = Mock()
        mock_topics_response.json.return_value = {
            'data': {
                'topics': [
                    {'name': 'Technology'},
                    {'name': 'Climate Change'},
                    {'name': 'Healthcare'},
                    {'name': 'Space Exploration'},
                    {'name': 'Artificial Intelligence'}
                ]
            }
        }
        mock_topics_response.raise_for_status.return_value = None
        mock_get.return_value = mock_topics_response
        
        print("🔥 Trending Topics from InShorts:")
        print("-" * 35)
        
        topics = scraper.get_inshorts_trending_topics()
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic}")
        
        print()
        print("✅ InShorts API Integration Demo Complete!")
        print("=" * 50)
        
        return all_articles

if __name__ == "__main__":
    demo_inshorts_integration()