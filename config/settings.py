"""Configuration settings for the article scraper."""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the article scraper."""

    # MongoDB settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "article_scraper")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "articles")

    # Scraping settings
    TARGET_ARTICLE_COUNT = int(os.getenv("TARGET_ARTICLE_COUNT", "50"))
    RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "2"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/scraper.log")

    # Cleanup settings
    AUTO_CLEANUP_ENABLED = os.getenv("AUTO_CLEANUP_ENABLED", "true").lower() == "true"
    CLEANUP_MONTHS_OLD = int(os.getenv("CLEANUP_MONTHS_OLD", "2"))

    # User agent for requests - Updated to match Chrome 137 (consistent with sec-ch-ua header)
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # InShorts API configuration - Prioritized for better image coverage
    INSHORTS_API_BASE_URL = "https://inshorts.com/api/en"
    INSHORTS_CATEGORIES = {
        "all_news": {"max_limit": 35, "priority": 1},
        "top_stories": {"max_limit": 20, "priority": 2},
        "trending": {"max_limit": 15, "priority": 3},
        "business": {"max_limit": 10, "priority": 4},
        "technology": {"max_limit": 10, "priority": 5},
    }

    # Headers for InShorts API to avoid bot detection
    # Based on analysis of actual InShorts website requests
    INSHORTS_HEADERS = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://inshorts.com/en/read",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": USER_AGENT,
    }

    # RSS feeds configuration - Global current affairs and trending topics
    RSS_FEEDS: Dict[str, str] = {
        # Global News Sources - Major International Outlets
        "bbc_world": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "bbc_technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "guardian_world": "https://www.theguardian.com/world/rss",
        "guardian_technology": "https://www.theguardian.com/technology/rss",
        "al_jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "reuters_world": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        # Technology & Innovation - Top Tech Publications
        "techcrunch": "https://techcrunch.com/feed/",
        "wired": "https://www.wired.com/feed/rss",
        "the_verge": "https://www.theverge.com/rss/index.xml",
        "ars_technica": "http://feeds.arstechnica.com/arstechnica/index",
        "engadget": "https://www.engadget.com/rss.xml",
        "cnet": "https://www.cnet.com/rss/news/",
        # Business & Economics - Financial News
        "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "financial_times": "https://www.ft.com/rss/home",
        "forbes": "https://www.forbes.com/real-time/feed2/",
        "economist": "https://www.economist.com/rss",
        "business_insider": "https://www.businessinsider.com/rss",
        # Science & Health - Research and Medical News
        "nature_news": "https://www.nature.com/nature.rss",
        "scientific_american": "http://rss.sciam.com/ScientificAmerican-Global",
        "new_scientist": "https://www.newscientist.com/feed/home/",
        "science_daily": "https://www.sciencedaily.com/rss/all.xml",
        # Regional Perspectives - Diverse Global Sources
        "cnn_international": "http://rss.cnn.com/rss/edition.rss",
        "cnn_technology": "http://rss.cnn.com/rss/edition_technology.rss",
        "dw_english": "https://rss.dw.com/rdf/rss-en-all",
        "france24": "https://www.france24.com/en/rss",
        "japan_times": "https://www.japantimes.co.jp/feed/",
        "south_china_morning_post": "https://www.scmp.com/rss/91/feed",
        # Quality Content Aggregators
        "reddit_worldnews": "https://www.reddit.com/r/worldnews/.rss",
        "hackernews": "https://hnrss.org/frontpage",
        # Specialized Quality Publications
        "mit_tech_review": "https://www.technologyreview.com/feed/",
        "atlantic": "https://www.theatlantic.com/feed/all/",
        "national_geographic": "https://www.nationalgeographic.com/pages/topic/latest-stories/_jcr_content.feed",
        # Eastern Europe, Russia & Belarus - Independent & Regional Sources
        "moscow_times": "https://www.themoscowtimes.com/rss/news",
        "meduza_en": "https://meduza.io/rss/en/all",
        "kyiv_independent": "https://kyivindependent.com/feed/",
        "politico_europe": "https://www.politico.eu/feed/",
        "notes_from_poland": "https://notesfrompoland.com/feed/",
        "emerging_europe": "https://emerging-europe.com/feed/",
        "balkan_insight": "https://balkaninsight.com/feed/",
        "intellinews": "https://www.intellinews.com/rss/",
        "euromaidanpress": "https://euromaidanpress.com/feed/",
        "novaya_gazeta_europe": "https://novayagazeta.eu/feed/",
    }

    # Medium publication feeds - Diverse topics and global perspectives (Working feeds only)
    MEDIUM_PUBLICATIONS: List[str] = [
        # Data Science & AI
        "https://towardsdatascience.com/feed",
        # Technology & Startups
        "https://medium.com/feed/hackernoon",
        "https://medium.com/feed/the-startup",
        "https://medium.com/feed/better-programming",
        # Business & Leadership
        "https://medium.com/feed/the-mission",
        "https://medium.com/feed/swlh",  # The Startup's publication
        # Personal Development
        "https://medium.com/feed/personal-growth",
        "https://medium.com/feed/thrive-global",
        # Design & UX
        "https://medium.com/feed/ux-collective",
        # Science & Future
        "https://medium.com/feed/predict",
    ]
