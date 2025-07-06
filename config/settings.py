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
    
    # User agent for requests
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    
    # RSS feeds configuration - Global current affairs and trending topics
    RSS_FEEDS: Dict[str, str] = {
        # Global News Sources
        'bbc_world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'reuters_world': 'https://feeds.reuters.com/reuters/worldNews',
        'ap_news': 'https://feeds.apnews.com/apnews/general',
        'guardian_world': 'https://www.theguardian.com/world/rss',
        'al_jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
        
        # Technology & Innovation
        'techcrunch': 'https://techcrunch.com/feed/',
        'wired': 'https://www.wired.com/feed/rss',
        'the_verge': 'https://www.theverge.com/rss/index.xml',
        'ars_technica': 'http://feeds.arstechnica.com/arstechnica/index',
        
        # Business & Economics
        'bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
        'financial_times': 'https://www.ft.com/rss/home',
        'economist': 'https://www.economist.com/rss/all.xml',
        'forbes': 'https://www.forbes.com/real-time/feed2/',
        
        # Science & Health
        'nature_news': 'https://www.nature.com/nature.rss',
        'scientific_american': 'http://rss.sciam.com/ScientificAmerican-Global',
        'new_scientist': 'https://www.newscientist.com/feed/home/',
        'who_news': 'https://www.who.int/rss-feeds/news-english.xml',
        
        # Culture & Society
        'medium_general': 'https://medium.com/feed',
        'medium_trending': 'https://medium.com/feed/tag/trending',
        'medium_culture': 'https://medium.com/feed/tag/culture',
        'npr_news': 'https://feeds.npr.org/1001/rss.xml',
        
        # Regional Perspectives
        'cnn_international': 'http://rss.cnn.com/rss/edition.rss',
        'dw_english': 'https://rss.dw.com/rdf/rss-en-all',
        'france24': 'https://www.france24.com/en/rss',
        'rt_news': 'https://www.rt.com/rss/news/',
        'china_daily': 'http://www.chinadaily.com.cn/rss/world_rss.xml',
        
        # Social & Trending
        'buzzfeed_news': 'https://www.buzzfeednews.com/arc/outboundfeeds/rss/',
        'reddit_worldnews': 'https://www.reddit.com/r/worldnews/.rss',
        'hackernews': 'https://hnrss.org/frontpage'
    }
    
    # Medium publication feeds - Diverse topics and global perspectives
    MEDIUM_PUBLICATIONS: List[str] = [
        'https://towardsdatascience.com/feed',
        'https://medium.com/feed/@freecodecamp',
        'https://medium.com/feed/hackernoon',
        'https://medium.com/feed/the-startup',
        'https://medium.com/feed/better-programming',
        'https://medium.com/feed/better-humans',
        'https://medium.com/feed/the-mission',
        'https://medium.com/feed/personal-growth',
        'https://medium.com/feed/thrive-global',
        'https://uxdesign.cc/feed',
        'https://medium.com/feed/swlh',
        'https://medium.com/feed/change-becomes-you',
        'https://medium.com/feed/politics',
        'https://medium.com/feed/world-issues',
        'https://medium.com/feed/global-perspectives'
    ]
