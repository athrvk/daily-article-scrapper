"""Tests for the article scraper module."""

import pytest
import requests
from unittest.mock import Mock, patch
from src.scraper import ArticleScraper


class TestArticleScraper:
    """Test cases for ArticleScraper class."""
    
    def test_init(self, mock_config):
        """Test scraper initialization."""
        scraper = ArticleScraper(config=mock_config)
        assert scraper.config == mock_config
        assert scraper.session is not None
    
    def test_remove_duplicates(self, scraper, sample_articles):
        """Test duplicate removal functionality."""
        # Add a duplicate article
        articles_with_duplicate = sample_articles + [sample_articles[0]]
        
        unique_articles = scraper._remove_duplicates(articles_with_duplicate)
        
        assert len(unique_articles) == 2
        assert unique_articles == sample_articles
    
    def test_get_urls_only(self, scraper, sample_articles):
        """Test URL extraction."""
        urls = scraper.get_urls_only(sample_articles)
        
        expected_urls = [
            'https://example.com/article1',
            'https://example.com/article2'
        ]
        assert urls == expected_urls
    
    @patch('src.scraper.feedparser.parse')
    def test_get_rss_articles(self, mock_parse, scraper):
        """Test RSS article extraction."""
        # Mock feedparser response
        mock_entry = Mock()
        # Set up both attribute and dict-style access
        mock_entry.title = 'Test Article'
        mock_entry.link = 'https://example.com/test'
        mock_entry.published = '2025-01-01'
        mock_entry.summary = 'Test summary'
        mock_entry.get.side_effect = lambda key, default='': {
            'title': 'Test Article',
            'link': 'https://example.com/test',
            'published': '2025-01-01',
            'summary': 'Test summary'
        }.get(key, default)
        mock_entry.tags = []
        mock_entry.media_content = []
        mock_entry.media_thumbnail = []
        mock_entry.enclosures = []
        mock_entry.links = []
        mock_entry.content = []
        mock_entry.description = ""
        # Add image field attributes
        for attr in ['image', 'featured_image', 'thumbnail', 'img', 'picture']:
            setattr(mock_entry, attr, "")
        
        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False
        mock_parse.return_value = mock_feed
        
        articles = scraper.get_rss_articles('https://example.com/feed')
        
        assert len(articles) == 1
        assert articles[0]['title'] == 'Test Article'
        assert articles[0]['url'] == 'https://example.com/test'
        assert 'image' in articles[0]  # Ensure image field is present
    
    def test_extract_image_from_html(self, scraper):
        """Test image extraction from HTML content."""
        html_content = '<p>Some text</p><img src="https://example.com/test.jpg" alt="test"><p>More text</p>'
        image_url = scraper._extract_image_from_html(html_content)
        assert image_url == 'https://example.com/test.jpg'
        
        # Test with no image
        html_no_image = '<p>Some text without images</p>'
        image_url = scraper._extract_image_from_html(html_no_image)
        assert image_url == ''
    
    def test_extract_image_from_rss_entry(self, scraper):
        """Test image extraction from RSS entry."""
        # Mock RSS entry with media content
        mock_entry = Mock()
        mock_media = Mock()
        mock_media.url = 'https://example.com/media.jpg'
        mock_entry.media_content = [mock_media]
        
        image_url = scraper._extract_image_from_rss_entry(mock_entry)
        assert image_url == 'https://example.com/media.jpg'
        
        # Test entry with no image data
        empty_entry = Mock()
        empty_entry.media_content = []
        empty_entry.media_thumbnail = []
        empty_entry.enclosures = []
        empty_entry.links = []
        empty_entry.summary = 'No images here'
        empty_entry.content = []
        
        image_url = scraper._extract_image_from_rss_entry(empty_entry)
        assert image_url == ''
    
    @patch('src.scraper.time.sleep')
    @patch.object(ArticleScraper, 'get_rss_articles')
    @patch.object(ArticleScraper, 'scrape_medium_trending')
    @patch.object(ArticleScraper, 'scrape_inshorts_articles')
    def test_scrape_daily_articles(self, mock_inshorts, mock_trending, mock_rss, mock_sleep, scraper, sample_articles):
        """Test daily article scraping."""
        mock_rss.return_value = [sample_articles[0]]
        mock_trending.return_value = [sample_articles[1]]
        mock_inshorts.return_value = [{
            'title': 'InShorts Test Article',
            'url': 'https://example.com/inshorts-test',
            'published': '2025-01-01T00:00:00Z',
            'summary': 'Test summary from InShorts',
            'source': 'inshorts.com',
            'tags': ['test', 'trending'],
            'image': 'https://example.com/image.jpg'
        }]
        
        articles = scraper.scrape_daily_articles(target_count=5)
        
        assert len(articles) > 0
        # Verify image field is present in results
        for article in articles:
            assert 'image' in article
        mock_sleep.assert_called()  # Ensure rate limiting is applied
        mock_inshorts.assert_called_once()  # Ensure InShorts was called
    
    @patch('src.scraper.requests.Session.get')
    def test_scrape_inshorts_articles(self, mock_get, scraper):
        """Test InShorts API scraping."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'news_list': [
                    {
                        'hash_id': 'test-hash-1',
                        'title': 'Test InShorts Article',
                        'content': 'Test content from InShorts',
                        'source_name': 'Test Source',
                        'source_url': 'https://example.com/test',
                        'image_url': 'https://example.com/image.jpg',
                        'created_at': '2025-01-01T00:00:00Z',
                        'tags': ['test']
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        articles = scraper.scrape_inshorts_articles(['top_stories'])
        
        assert len(articles) == 1
        assert articles[0]['title'] == 'Test InShorts Article'
        assert articles[0]['source'] == 'inshorts.com'
        assert articles[0]['inshorts_id'] == 'test-hash-1'
        assert articles[0]['original_source'] == 'Test Source'
        assert 'image' in articles[0]
        mock_get.assert_called()
    
    @patch('src.scraper.requests.Session.get')
    def test_fetch_inshorts_category_error_handling(self, mock_get, scraper):
        """Test InShorts API error handling."""
        # Mock network error
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        articles = scraper._fetch_inshorts_category('top_stories', 5)
        
        assert articles == []
        mock_get.assert_called()
    
    @patch('src.scraper.requests.Session.get')
    def test_fetch_inshorts_category_invalid_json(self, mock_get, scraper):
        """Test InShorts API invalid JSON handling."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        articles = scraper._fetch_inshorts_category('top_stories', 5)
        
        assert articles == []
        mock_get.assert_called()
    
    def test_parse_inshorts_article(self, scraper):
        """Test parsing of InShorts article data."""
        item = {
            'hash_id': 'test-hash',
            'title': 'Test Article',
            'content': 'Test content',
            'source_name': 'Test Source',
            'source_url': 'https://example.com/test',
            'image_url': 'https://example.com/image.jpg',
            'created_at': '2025-01-01T00:00:00Z',
            'tags': ['test', 'news']
        }
        
        article = scraper._parse_inshorts_article(item, 'top_stories')
        
        assert article['title'] == 'Test Article'
        assert article['source'] == 'inshorts.com'
        assert article['inshorts_id'] == 'test-hash'
        assert article['original_source'] == 'Test Source'
        assert 'top_stories' in article['tags']
        assert 'test' in article['tags']
    
    def test_parse_inshorts_article_missing_fields(self, scraper):
        """Test parsing of InShorts article with missing fields."""
        item = {
            'hash_id': 'test-hash'
            # Missing title and url
        }
        
        article = scraper._parse_inshorts_article(item, 'top_stories')
        
        assert article is None  # Should return None for invalid articles
    
    @patch('src.scraper.requests.Session.get')
    def test_get_inshorts_trending_topics(self, mock_get, scraper):
        """Test getting trending topics from InShorts."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'topics': [
                    {'name': 'Technology'},
                    {'name': 'Business'},
                    {'name': 'Science'}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        topics = scraper.get_inshorts_trending_topics()
        
        assert len(topics) == 3
        assert 'Technology' in topics
        assert 'Business' in topics
        assert 'Science' in topics
        mock_get.assert_called_once()
    
    @patch('src.scraper.requests.Session.get')
    def test_get_inshorts_trending_topics_error(self, mock_get, scraper):
        """Test trending topics error handling."""
        # Mock network error
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        topics = scraper.get_inshorts_trending_topics()
        
        assert topics == []
        mock_get.assert_called_once()
