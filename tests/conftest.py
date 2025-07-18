"""Test configuration and fixtures."""

import pytest
import os
from unittest.mock import Mock
from src.scraper import ArticleScraper
from src.database import DatabaseManager
from config.settings import Config


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=Config)
    config.RSS_FEEDS = {
        'test_feed': 'https://example.com/feed'
    }
    config.MEDIUM_PUBLICATIONS = ['https://example.com/medium/feed']
    config.TARGET_ARTICLE_COUNT = 5
    config.RATE_LIMIT_DELAY = 0.1
    config.USER_AGENT = 'Test Agent'
    config.INSHORTS_API_BASE_URL = 'https://inshorts.com/api/en'
    config.INSHORTS_CATEGORIES = {
        'top_stories': {'max_limit': 10, 'priority': 1},
        'trending': {'max_limit': 8, 'priority': 2}
    }
    config.INSHORTS_HEADERS = {
        'accept': '*/*',
        'user-agent': 'Test Agent'
    }
    return config


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    return [
        {
            'title': 'Test Article 1',
            'url': 'https://example.com/article1',
            'published': '2025-01-01T12:00:00',
            'summary': 'Test summary 1',
            'source': 'example.com',
            'tags': ['tech'],
            'image': 'https://example.com/image1.jpg'
        },
        {
            'title': 'Test Article 2',
            'url': 'https://example.com/article2',
            'published': '2025-01-01T13:00:00',
            'summary': 'Test summary 2',
            'source': 'example.com',
            'tags': ['ai'],
            'image': 'https://example.com/image2.jpg'
        }
    ]


@pytest.fixture
def scraper(mock_config):
    """ArticleScraper instance for testing."""
    return ArticleScraper(config=mock_config)
