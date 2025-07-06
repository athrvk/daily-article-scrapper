"""Article scraper module for extracting articles from various sources."""

import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import random
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Any, Optional
from config.settings import Config

logger = logging.getLogger(__name__)


class ArticleScraper:
    """Main article scraper class."""
    
    def __init__(self, config: Config = None):
        """Initialize the scraper with configuration."""
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT
        })
        
    def get_rss_articles(self, feed_url: str, max_articles: int = 5) -> List[Dict[str, Any]]:
        """Extract articles from RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"RSS feed has issues: {feed_url}")
            
            articles = []
            for entry in feed.entries[:max_articles]:
                article = {
                    'title': entry.get('title', 'No Title'),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'source': urlparse(feed_url).netloc,
                    'tags': [tag.term for tag in entry.get('tags', [])]
                }
                articles.append(article)
            
            logger.info(f"Extracted {len(articles)} articles from {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
            return []
    
    def scrape_medium_trending(self, max_articles: int = 5) -> List[Dict[str, Any]]:
        """Scrape Medium trending articles."""
        try:
            url = "https://medium.com/tag/trending"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            # Medium uses dynamic loading, so we'll try to find article links
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link.get('href', '')
                if '/p/' in href or '/@' in href:
                    if href.startswith('/'):
                        href = 'https://medium.com' + href
                    elif href.startswith('https://medium.com'):
                        pass
                    else:
                        continue
                    
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:  # Filter out short/empty titles
                        articles.append({
                            'title': title,
                            'url': href,
                            'published': datetime.now().isoformat(),
                            'summary': '',
                            'source': 'medium.com',
                            'tags': ['trending']
                        })
                        
                        if len(articles) >= max_articles:
                            break
            
            logger.info(f"Scraped {len(articles)} trending articles from Medium")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping Medium trending: {str(e)}")
            return []
    
    def scrape_daily_articles(self, target_count: int = None) -> List[Dict[str, Any]]:
        """Scrape articles from multiple sources."""
        target_count = target_count or self.config.TARGET_ARTICLE_COUNT
        all_articles = []
        
        # Get articles from RSS feeds
        for feed_name, feed_url in self.config.RSS_FEEDS.items():
            try:
                articles = self.get_rss_articles(feed_url, max_articles=3)
                all_articles.extend(articles)
                time.sleep(random.uniform(1, self.config.RATE_LIMIT_DELAY))
            except Exception as e:
                logger.error(f"Error processing feed {feed_name}: {e}")
                continue
        
        # Get articles from Medium publications
        for pub_feed in self.config.MEDIUM_PUBLICATIONS:
            try:
                articles = self.get_rss_articles(pub_feed, max_articles=2)
                all_articles.extend(articles)
                time.sleep(random.uniform(1, self.config.RATE_LIMIT_DELAY))
            except Exception as e:
                logger.error(f"Error processing Medium publication {pub_feed}: {e}")
                continue
        
        # Try to get Medium trending articles
        try:
            trending_articles = self.scrape_medium_trending(max_articles=5)
            all_articles.extend(trending_articles)
        except Exception as e:
            logger.error(f"Error scraping Medium trending: {e}")
        
        # Remove duplicates based on URL
        unique_articles = self._remove_duplicates(all_articles)
        
        # Sort by published date (newest first) and limit to target count
        sorted_articles = self._sort_articles(unique_articles)
        return sorted_articles[:target_count]
    
    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL."""
        unique_articles = []
        seen_urls = set()
        
        for article in articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"Removed {len(articles) - len(unique_articles)} duplicate articles")
        return unique_articles
    
    def _sort_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort articles by published date (newest first)."""
        def get_sort_key(article):
            published = article.get('published', '')
            if published:
                try:
                    # Try to parse the date
                    return datetime.fromisoformat(published.replace('Z', '+00:00'))
                except:
                    return datetime.min
            return datetime.min
        
        return sorted(articles, key=get_sort_key, reverse=True)
    
    def save_articles_json(self, articles: List[Dict[str, Any]], filename: str = None) -> str:
        """Save articles to JSON file."""
        if filename is None:
            filename = f"articles_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved {len(articles)} articles to {filename}")
        return filename
    
    def print_articles(self, articles: List[Dict[str, Any]]):
        """Print articles in a readable format."""
        print(f"\n{'='*60}")
        print(f"DAILY ARTICLE SCRAPER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Found {len(articles)} articles:")
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   URL: {article['url']}")
            if article.get('tags'):
                print(f"   Tags: {', '.join(article['tags'])}")
            if article['summary']:
                summary = article['summary'][:150]
                print(f"   Summary: {summary}{'...' if len(article['summary']) > 150 else ''}")
    
    def get_urls_only(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract only URLs from articles."""
        return [article['url'] for article in articles if article.get('url')]
