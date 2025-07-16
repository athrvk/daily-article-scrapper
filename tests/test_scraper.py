"""Tests for the article scraper module."""

import pytest
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
        mock_entry.get.side_effect = lambda key, default='': {
            'title': 'Test Article',
            'link': 'https://example.com/test',
            'published': '2025-01-01',
            'summary': 'Test summary'
        }.get(key, default)
        mock_entry.tags = []
        
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
    def test_scrape_daily_articles(self, mock_trending, mock_rss, mock_sleep, scraper, sample_articles):
        """Test daily article scraping."""
        mock_rss.return_value = [sample_articles[0]]
        mock_trending.return_value = [sample_articles[1]]
        
        articles = scraper.scrape_daily_articles(target_count=5)
        
        assert len(articles) > 0
        # Verify image field is present in results
        for article in articles:
            assert 'image' in article
        mock_sleep.assert_called()  # Ensure rate limiting is applied
