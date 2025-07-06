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
    
    @patch('src.scraper.time.sleep')
    @patch.object(ArticleScraper, 'get_rss_articles')
    @patch.object(ArticleScraper, 'scrape_medium_trending')
    def test_scrape_daily_articles(self, mock_trending, mock_rss, mock_sleep, scraper, sample_articles):
        """Test daily article scraping."""
        mock_rss.return_value = [sample_articles[0]]
        mock_trending.return_value = [sample_articles[1]]
        
        articles = scraper.scrape_daily_articles(target_count=5)
        
        assert len(articles) > 0
        mock_sleep.assert_called()  # Ensure rate limiting is applied
