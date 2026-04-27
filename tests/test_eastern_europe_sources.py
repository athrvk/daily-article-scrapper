"""Tests for Eastern Europe, Russia & Belarus RSS sources."""

import pytest
import feedparser
import requests
from unittest.mock import patch, Mock
from config.settings import Config
from src.scraper import ArticleScraper


EASTERN_EUROPE_FEEDS = [
    "moscow_times",
    "meduza_en",
    "kyiv_independent",
    "rferl",
    "notes_from_poland",
    "emerging_europe",
    "balkan_insight",
    "intellinews",
    "euromaidanpress",
    "novaya_gazeta_europe",
]


class TestEasternEuropeSourcesConfig:
    """Validate Eastern European sources are correctly registered in Config."""

    def test_all_eastern_europe_keys_present(self):
        for key in EASTERN_EUROPE_FEEDS:
            assert key in Config.RSS_FEEDS, f"Missing feed key: {key}"

    def test_all_urls_are_https(self):
        for key in EASTERN_EUROPE_FEEDS:
            url = Config.RSS_FEEDS[key]
            assert url.startswith("https://"), f"{key} URL is not HTTPS: {url}"

    def test_no_duplicate_urls(self):
        ee_urls = [Config.RSS_FEEDS[k] for k in EASTERN_EUROPE_FEEDS]
        assert len(ee_urls) == len(set(ee_urls)), "Duplicate URLs found in Eastern Europe feeds"

    def test_no_trailing_whitespace_in_urls(self):
        for key in EASTERN_EUROPE_FEEDS:
            url = Config.RSS_FEEDS[key]
            assert url == url.strip(), f"{key} URL has leading/trailing whitespace"


class TestEasternEuropeRSSParsing:
    """Test that the scraper correctly handles Eastern European RSS feeds."""

    @pytest.fixture
    def scraper(self, mock_config):
        return ArticleScraper(config=mock_config)

    @patch("src.scraper.feedparser.parse")
    def test_scraper_parses_eastern_europe_feed(self, mock_parse, scraper):
        mock_entry = Mock()
        mock_entry.title = "Russia Signs New Economic Agreement"
        mock_entry.link = "https://www.themoscowtimes.com/2026/04/27/test-article"
        mock_entry.published = "Mon, 27 Apr 2026 10:00:00 +0000"
        mock_entry.summary = "Details about the new economic agreement signed today."
        mock_entry.get.side_effect = lambda key, default="": {
            "title": mock_entry.title,
            "link": mock_entry.link,
            "published": mock_entry.published,
            "summary": mock_entry.summary,
        }.get(key, default)
        mock_entry.tags = []
        mock_entry.media_content = []
        mock_entry.media_thumbnail = []
        mock_entry.enclosures = []
        mock_entry.links = []
        mock_entry.content = []
        mock_entry.description = ""
        for attr in ["image", "featured_image", "thumbnail", "img", "picture"]:
            setattr(mock_entry, attr, "")

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False
        mock_parse.return_value = mock_feed

        articles = scraper.get_rss_articles(Config.RSS_FEEDS["moscow_times"])

        assert len(articles) == 1
        assert articles[0]["title"] == "Russia Signs New Economic Agreement"
        assert "themoscowtimes.com" in articles[0]["url"]

    @patch("src.scraper.feedparser.parse")
    def test_scraper_parses_meduza_feed(self, mock_parse, scraper):
        mock_entry = Mock()
        mock_entry.title = "Meduza: Independent Coverage of Eastern Europe"
        mock_entry.link = "https://meduza.io/en/news/2026/04/27/test"
        mock_entry.published = "Mon, 27 Apr 2026 09:00:00 +0000"
        mock_entry.summary = "Independent news coverage from Meduza."
        mock_entry.get.side_effect = lambda key, default="": {
            "title": mock_entry.title,
            "link": mock_entry.link,
            "published": mock_entry.published,
            "summary": mock_entry.summary,
        }.get(key, default)
        mock_entry.tags = []
        mock_entry.media_content = []
        mock_entry.media_thumbnail = []
        mock_entry.enclosures = []
        mock_entry.links = []
        mock_entry.content = []
        mock_entry.description = ""
        for attr in ["image", "featured_image", "thumbnail", "img", "picture"]:
            setattr(mock_entry, attr, "")

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False
        mock_parse.return_value = mock_feed

        articles = scraper.get_rss_articles(Config.RSS_FEEDS["meduza_en"])

        assert len(articles) == 1
        assert "meduza.io" in articles[0]["url"]

    @patch("src.scraper.feedparser.parse")
    def test_eastern_europe_articles_pass_validation(self, mock_parse, scraper):
        """Articles from EE sources should pass the is_valid_article filter."""
        mock_entry = Mock()
        mock_entry.title = "Poland Announces New Infrastructure Investment Plan"
        mock_entry.link = "https://notesfrompoland.com/2026/04/27/infrastructure-plan"
        mock_entry.published = "Mon, 27 Apr 2026 08:00:00 +0000"
        mock_entry.summary = "The Polish government has announced a major new infrastructure investment."
        mock_entry.get.side_effect = lambda key, default="": {
            "title": mock_entry.title,
            "link": mock_entry.link,
            "published": mock_entry.published,
            "summary": mock_entry.summary,
        }.get(key, default)
        mock_entry.tags = []
        mock_entry.media_content = []
        mock_entry.media_thumbnail = []
        mock_entry.enclosures = []
        mock_entry.links = []
        mock_entry.content = []
        mock_entry.description = ""
        for attr in ["image", "featured_image", "thumbnail", "img", "picture"]:
            setattr(mock_entry, attr, "")

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False
        mock_parse.return_value = mock_feed

        articles = scraper.get_rss_articles(Config.RSS_FEEDS["notes_from_poland"])

        assert len(articles) == 1
        assert scraper._is_valid_article(articles[0])


@pytest.mark.live
class TestEasternEuropeSourcesLive:
    """Live connectivity tests — require network access. Run with: pytest -m live"""

    @pytest.fixture
    def real_scraper(self):
        return ArticleScraper()

    @pytest.mark.parametrize("feed_key", EASTERN_EUROPE_FEEDS)
    def test_feed_reachable_and_returns_articles(self, real_scraper, feed_key):
        url = Config.RSS_FEEDS[feed_key]
        articles = real_scraper.get_rss_articles(url)
        assert isinstance(articles, list), f"{feed_key}: expected list, got {type(articles)}"
        assert len(articles) > 0, f"{feed_key} ({url}) returned no articles — feed may be down or blocked"
        for article in articles[:3]:
            assert article.get("title"), f"{feed_key}: article missing title"
            assert article.get("url", "").startswith("http"), f"{feed_key}: article missing valid URL"
