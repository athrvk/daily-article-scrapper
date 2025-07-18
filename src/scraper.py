"""Article scraper module for extracting articles from various sources."""

import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import time
import random
from urllib.parse import urlparse
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from config.settings import Config

logger = logging.getLogger(__name__)


class ArticleScraper:
    """Main article scraper class."""

    def __init__(self, config: Config = None):
        """Initialize the scraper with configuration."""
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.USER_AGENT})
        self.articles_lock = Lock()  # For thread-safe operations

    def _extract_image_from_rss_entry(self, entry) -> str:
        """Extract image URL from RSS entry."""
        try:
            # Try different common image sources in RSS feeds

            # 1. Check for media:content (common in many feeds)
            if hasattr(entry, "media_content") and entry.media_content:
                for media in entry.media_content:
                    if hasattr(media, "url") and media.url:
                        return media.url

            # 2. Check for media:thumbnail
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                for thumb in entry.media_thumbnail:
                    if hasattr(thumb, "url") and thumb.url:
                        return thumb.url

            # 3. Check enclosures for images
            if hasattr(entry, "enclosures") and entry.enclosures:
                for enclosure in entry.enclosures:
                    if hasattr(enclosure, "type") and hasattr(enclosure, "href"):
                        if enclosure.type and enclosure.type.startswith("image/"):
                            return enclosure.href

            # 4. Check links for image attachments
            if hasattr(entry, "links") and entry.links:
                for link in entry.links:
                    if hasattr(link, "type") and hasattr(link, "href"):
                        if link.type and link.type.startswith("image/"):
                            return link.href

            # 5. Parse summary/description for img tags
            if hasattr(entry, "summary") and entry.summary:
                img_url = self._extract_image_from_html(entry.summary)
                if img_url:
                    return img_url

            # 6. Parse content for img tags
            if hasattr(entry, "content") and entry.content:
                for content_item in entry.content:
                    if hasattr(content_item, "value"):
                        img_url = self._extract_image_from_html(content_item.value)
                        if img_url:
                            return img_url

            return ""  # Return empty string if no image found

        except Exception as e:
            logger.debug(f"Error extracting image from RSS entry: {e}")
            return ""

    def _extract_image_from_html(self, html_content: str) -> str:
        """Extract first image URL from HTML content."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            img_tag = soup.find("img")
            if img_tag and img_tag.get("src"):
                return img_tag["src"]
            return ""
        except Exception as e:
            logger.debug(f"Error extracting image from HTML: {e}")
            return ""

    def _extract_medium_image(self, link_element) -> str:
        """Extract image URL from Medium article link context."""
        try:
            # Look for nearby img elements in the same container
            parent = link_element.parent
            if parent:
                # Look for img tags in the parent container
                img = parent.find("img")
                if img and img.get("src"):
                    src = img["src"]
                    # Medium images often have query parameters, clean them if needed
                    if src and ("medium.com" in src or src.startswith("http")):
                        return src

                # Look for background images in style attributes
                for element in parent.find_all(["div", "span"], style=True):
                    style = element.get("style", "")
                    if "background-image" in style:
                        # Extract URL from background-image: url(...)
                        import re

                        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                        if match:
                            return match.group(1)

            return ""
        except Exception as e:
            logger.debug(f"Error extracting Medium image: {e}")
            return ""

    def get_rss_articles(self, feed_url: str, max_articles: int = 5) -> List[Dict[str, Any]]:
        """Extract articles from RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"RSS feed has issues: {feed_url}")

            articles = []
            for entry in feed.entries[:max_articles]:
                # Extract image from RSS entry
                image_url = self._extract_image_from_rss_entry(entry)

                article = {
                    "title": entry.get("title", "No Title"),
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "source": urlparse(feed_url).netloc,
                    "tags": [tag.term for tag in entry.get("tags", [])],
                    "image": image_url,
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

            soup = BeautifulSoup(response.content, "html.parser")

            articles = []
            # Medium uses dynamic loading, so we'll try to find article links
            article_links = soup.find_all("a", href=True)

            for link in article_links:
                href = link.get("href", "")
                if "/p/" in href or "/@" in href:
                    if href.startswith("/"):
                        href = "https://medium.com" + href
                    elif href.startswith("https://medium.com"):
                        pass
                    else:
                        continue

                    title = link.get_text(strip=True)
                    if title and len(title) > 10:  # Filter out short/empty titles
                        # Try to extract image from the link's context
                        image_url = self._extract_medium_image(link)

                        articles.append(
                            {
                                "title": title,
                                "url": href,
                                "published": datetime.now().isoformat(),
                                "summary": "",
                                "source": "medium.com",
                                "tags": ["trending"],
                                "image": image_url,
                            }
                        )

                        if len(articles) >= max_articles:
                            break

            logger.info(f"Scraped {len(articles)} trending articles from Medium")
            return articles

        except Exception as e:
            logger.error(f"Error scraping Medium trending: {str(e)}")
            return []

    def _fetch_rss_feed_safe(self, feed_info: tuple) -> List[Dict[str, Any]]:
        """Thread-safe wrapper for RSS feed fetching."""
        feed_name, feed_url, max_articles = feed_info
        try:
            logger.info(f"🔄 Fetching {feed_name} in thread...")
            articles = self.get_rss_articles(feed_url, max_articles)
            logger.info(f"✅ {feed_name}: Found {len(articles)} articles")

            # Add a small random delay to avoid overwhelming servers
            time.sleep(random.uniform(0.5, 1.5))
            return articles

        except Exception as e:
            logger.error(f"❌ Error processing feed {feed_name}: {e}")
            return []

    def _fetch_medium_trending_safe(self, max_articles: int) -> List[Dict[str, Any]]:
        """Thread-safe wrapper for Medium trending scraping."""
        try:
            logger.info("🔄 Fetching Medium trending in thread...")
            articles = self.scrape_medium_trending(max_articles)
            logger.info(f"✅ Medium trending: Found {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"❌ Error scraping Medium trending: {e}")
            return []

    def scrape_inshorts_articles(
        self, categories: List[str] = None, max_articles_per_category: int = None
    ) -> List[Dict[str, Any]]:
        """Scrape articles from InShorts API."""
        if categories is None:
            categories = list(self.config.INSHORTS_CATEGORIES.keys())

        all_articles = []

        for category in categories:
            try:
                category_config = self.config.INSHORTS_CATEGORIES.get(category, {"max_limit": 5})
                max_limit = max_articles_per_category or category_config["max_limit"]

                logger.info(f"Fetching InShorts articles for category: {category}")
                articles = self._fetch_inshorts_category(category, max_limit)

                if articles:
                    all_articles.extend(articles)
                    logger.info(f"Retrieved {len(articles)} articles from InShorts {category}")
                else:
                    logger.warning(f"No articles found for InShorts {category}")

                # Add delay between category requests to be respectful
                time.sleep(self.config.RATE_LIMIT_DELAY)

            except Exception as e:
                logger.error(f"Error fetching InShorts {category}: {str(e)}")
                continue

        logger.info(f"Total InShorts articles retrieved: {len(all_articles)}")
        return all_articles

    def _fetch_inshorts_category(
        self, category: str, max_limit: int, news_offset: str = None
    ) -> List[Dict[str, Any]]:
        """Fetch articles from a specific InShorts category."""
        try:
            # Build API URL
            url = f"{self.config.INSHORTS_API_BASE_URL}/news"
            params = {"category": category, "max_limit": max_limit, "include_card_data": "true"}

            if news_offset:
                params["news_offset"] = news_offset

            # Make request with proper headers
            response = self.session.get(
                url, params=params, headers=self.config.INSHORTS_HEADERS, timeout=10
            )
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Extract articles from response
            articles = []
            if "data" in data and "news_list" in data["data"]:
                for item in data["data"]["news_list"]:
                    article = self._parse_inshorts_article(item, category)
                    if article:
                        articles.append(article)

            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching InShorts {category}: {str(e)}")
            return []
        except ValueError as e:
            logger.error(f"JSON parsing error for InShorts {category}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching InShorts {category}: {str(e)}")
            return []

    def _parse_inshorts_article(self, item: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Parse a single InShorts article from API response."""
        try:
            # Extract article data
            article = {
                "title": item.get("title", ""),
                "url": item.get("source_url", ""),
                "published": item.get("created_at", ""),
                "summary": item.get("content", ""),
                "source": "inshorts.com",
                "tags": item.get("tags", []) + [category],
                "image": item.get("image_url", ""),
                "inshorts_id": item.get("hash_id", ""),
                "original_source": item.get("source_name", ""),
            }

            # Validate required fields
            if not article["title"] or not article["url"]:
                logger.warning(f"Invalid InShorts article: missing title or URL")
                return None

            # Convert timestamp if needed
            if article["published"]:
                try:
                    # InShorts typically uses ISO format
                    if "T" in article["published"]:
                        dt = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
                        article["published"] = dt.isoformat()
                except Exception as e:
                    logger.debug(f"Could not parse InShorts timestamp: {e}")
                    article["published"] = datetime.now().isoformat()
            else:
                article["published"] = datetime.now().isoformat()

            return article

        except Exception as e:
            logger.error(f"Error parsing InShorts article: {str(e)}")
            return None

    def get_inshorts_trending_topics(self) -> List[str]:
        """Get trending topics from InShorts API."""
        try:
            url = f"{self.config.INSHORTS_API_BASE_URL}/search/trending_topics"

            response = self.session.get(url, headers=self.config.INSHORTS_HEADERS, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract trending topics (structure may vary)
            topics = []
            if "data" in data and "topics" in data["data"]:
                topics = [topic.get("name", "") for topic in data["data"]["topics"]]
            elif "trending_topics" in data:
                topics = data["trending_topics"]

            logger.info(f"Retrieved {len(topics)} trending topics from InShorts")
            return topics

        except Exception as e:
            logger.error(f"Error fetching InShorts trending topics: {str(e)}")
            return []

    def _fetch_inshorts_safe(self, categories: List[str]) -> List[Dict[str, Any]]:
        """Thread-safe wrapper for InShorts API scraping."""
        try:
            logger.info("🔄 Fetching InShorts articles in thread...")
            articles = self.scrape_inshorts_articles(categories)
            logger.info(f"✅ InShorts: Found {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"❌ Error scraping InShorts: {e}")
            return []

    def scrape_daily_articles(self, target_count: int = None) -> List[Dict[str, Any]]:
        target_count = target_count or self.config.TARGET_ARTICLE_COUNT
        all_articles = []

        logger.info("🚀 Starting multi-threaded article scraping...")

        # Prepare tasks for thread pool
        tasks = []

        # Add RSS feeds to tasks
        for feed_name, feed_url in self.config.RSS_FEEDS.items():
            tasks.append(("rss", feed_name, feed_url, 3))

        # Add Medium publications to tasks
        for i, pub_feed in enumerate(self.config.MEDIUM_PUBLICATIONS):
            feed_name = f"medium_pub_{i+1}"
            tasks.append(("rss", feed_name, pub_feed, 2))

        # Add Medium trending as a special task
        tasks.append(("trending", "medium_trending", None, 5))

        # Add InShorts API as a special task
        inshorts_categories = ["top_stories", "trending", "business", "technology"]
        tasks.append(("inshorts", "inshorts_api", inshorts_categories, None))

        # Use ThreadPoolExecutor for concurrent fetching
        max_workers = min(len(tasks), 5)  # Limit to 5 concurrent threads
        logger.info(f"📊 Processing {len(tasks)} sources with {max_workers} worker threads")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {}

            for task in tasks:
                task_type, name, url_or_data, max_articles = task

                if task_type == "rss":
                    future = executor.submit(
                        self._fetch_rss_feed_safe, (name, url_or_data, max_articles)
                    )
                elif task_type == "trending":
                    future = executor.submit(self._fetch_medium_trending_safe, max_articles)
                elif task_type == "inshorts":
                    future = executor.submit(self._fetch_inshorts_safe, url_or_data)
                else:
                    continue

                future_to_task[future] = (task_type, name)

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task_type, name = future_to_task[future]
                try:
                    articles = future.result()
                    if articles:
                        with self.articles_lock:
                            all_articles.extend(articles)
                        logger.info(f"✅ Completed {name}: Added {len(articles)} articles")
                    else:
                        logger.warning(f"⚠️ No articles from {name}")

                except Exception as exc:
                    logger.error(f"❌ {name} generated an exception: {exc}")

        logger.info(
            f"🏁 Multi-threaded scraping completed. Total articles collected: {len(all_articles)}"
        )

        # Remove duplicates based on URL
        unique_articles = self._remove_duplicates(all_articles)

        # Sort by published date (newest first) and limit to target count
        sorted_articles = self._sort_articles(unique_articles)

        final_articles = sorted_articles[:target_count]
        logger.info(
            f"📋 Final result: {len(final_articles)} unique articles after deduplication and sorting"
        )

        return final_articles

    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL."""
        unique_articles = []
        seen_urls = set()

        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        logger.info(f"Removed {len(articles) - len(unique_articles)} duplicate articles")
        return unique_articles

    def _sort_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort articles by published date (newest first)."""

        def get_sort_key(article):
            published = article.get("published", "")
            if published:
                try:
                    # Try to parse the date and normalize timezone
                    if "Z" in published:
                        # Replace Z with +00:00 for UTC
                        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    elif "+" in published or published.endswith(("GMT", "UTC")):
                        # Already has timezone info
                        dt = datetime.fromisoformat(
                            published.replace("GMT", "+00:00").replace("UTC", "+00:00")
                        )
                    else:
                        # No timezone info, assume UTC
                        dt = datetime.fromisoformat(published)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception as e:
                    logger.debug(f"Failed to parse date '{published}': {e}")
                    return datetime.min.replace(tzinfo=timezone.utc)
            return datetime.min.replace(tzinfo=timezone.utc)

        return sorted(articles, key=get_sort_key, reverse=True)

    def save_articles_json(self, articles: List[Dict[str, Any]], filename: str = None) -> str:
        """Save articles to JSON file."""
        if filename is None:
            filename = f"articles_{datetime.now().strftime('%Y%m%d')}.json"

        with open(filename, "w", encoding="utf-8") as f:
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
            if article.get("tags"):
                print(f"   Tags: {', '.join(article['tags'])}")
            if article["summary"]:
                summary = article["summary"][:150]
                print(f"   Summary: {summary}{'...' if len(article['summary']) > 150 else ''}")

    def get_urls_only(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract only URLs from articles."""
        return [article["url"] for article in articles if article.get("url")]
