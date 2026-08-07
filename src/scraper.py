"""Article scraper module for extracting articles from various sources."""

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import Config

logger = logging.getLogger(__name__)


class ArticleScraper:
    """Main article scraper class."""

    # Query parameters that only track referrals and break URL deduplication
    TRACKING_PARAMS = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "source"}

    def __init__(self, config: Config = None):
        """Initialize the scraper with configuration."""
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.USER_AGENT})
        retry = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _extract_image_from_rss_entry(self, entry) -> str:
        """Extract image URL from RSS entry with enhanced fallback mechanisms."""
        try:
            # Try different common image sources in RSS feeds

            # 1. Check for media:content (common in many feeds)
            if hasattr(entry, "media_content") and entry.media_content:
                for media in entry.media_content:
                    if hasattr(media, "url") and media.url:
                        if self._is_valid_image_url(media.url):
                            return media.url

            # 2. Check for media:thumbnail
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                for thumb in entry.media_thumbnail:
                    if hasattr(thumb, "url") and thumb.url:
                        if self._is_valid_image_url(thumb.url):
                            return thumb.url

            # 3. Check enclosures for images
            if hasattr(entry, "enclosures") and entry.enclosures:
                for enclosure in entry.enclosures:
                    if hasattr(enclosure, "type") and hasattr(enclosure, "href"):
                        if enclosure.type and enclosure.type.startswith("image/"):
                            if self._is_valid_image_url(enclosure.href):
                                return enclosure.href

            # 4. Check links for image attachments
            if hasattr(entry, "links") and entry.links:
                for link in entry.links:
                    if hasattr(link, "type") and hasattr(link, "href"):
                        if link.type and link.type.startswith("image/"):
                            if self._is_valid_image_url(link.href):
                                return link.href

            # 5. Check custom RSS image fields (common extensions)
            image_fields = ["image", "featured_image", "thumbnail", "img", "picture"]
            for field in image_fields:
                if hasattr(entry, field):
                    img_value = getattr(entry, field)
                    if isinstance(img_value, str) and img_value.strip():
                        if self._is_valid_image_url(img_value):
                            return img_value
                    elif hasattr(img_value, "href") and img_value.href:
                        if self._is_valid_image_url(img_value.href):
                            return img_value.href

            # 6. Parse summary/description for img tags
            if hasattr(entry, "summary") and entry.summary:
                img_url = self._extract_image_from_html(entry.summary)
                if img_url:
                    return img_url

            # 7. Parse content for img tags
            if hasattr(entry, "content") and entry.content:
                for content_item in entry.content:
                    if hasattr(content_item, "value"):
                        img_url = self._extract_image_from_html(content_item.value)
                        if img_url:
                            return img_url

            # 8. Parse description for img tags (fallback)
            if hasattr(entry, "description") and entry.description:
                img_url = self._extract_image_from_html(entry.description)
                if img_url:
                    return img_url

            # 9. Try to extract from Open Graph or Twitter meta tags in the link
            if hasattr(entry, "link") and entry.link:
                img_url = self._extract_image_from_webpage(entry.link)
                if img_url:
                    return img_url

            return ""  # Return empty string if no image found

        except Exception as e:
            logger.debug(f"Error extracting image from RSS entry: {e}")
            return ""

    def _extract_image_from_html(self, html_content: str) -> str:
        """Extract first image URL from HTML content with improved parsing."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Look for img tags with various attributes
            img_tags = soup.find_all("img")
            for img_tag in img_tags:
                # Check src attribute
                if img_tag.get("src"):
                    img_url = img_tag["src"]
                    if self._is_valid_image_url(img_url):
                        return self._normalize_image_url(img_url)

                # Check data-src for lazy loading images
                if img_tag.get("data-src"):
                    img_url = img_tag["data-src"]
                    if self._is_valid_image_url(img_url):
                        return self._normalize_image_url(img_url)

                # Check srcset for responsive images
                if img_tag.get("srcset"):
                    srcset = img_tag["srcset"]
                    # Extract the first URL from srcset
                    urls = srcset.split(",")
                    if urls:
                        first_url = urls[0].strip().split(" ")[0]
                        if self._is_valid_image_url(first_url):
                            return self._normalize_image_url(first_url)

            return ""
        except Exception as e:
            logger.debug(f"Error extracting image from HTML: {e}")
            return ""

    def _is_valid_image_url(self, url: str) -> bool:
        """Validate if URL is likely to be a valid image URL."""
        if not url or not isinstance(url, str):
            return False

        url = url.strip()
        if not url:
            return False

        # Must be HTTP/HTTPS or protocol-relative
        if not (
            url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("//")
        ):
            return False

        # Skip common non-image extensions
        skip_extensions = [".pdf", ".doc", ".docx", ".zip", ".mp4", ".avi", ".mp3"]
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip obviously invalid URLs (but allow example.com for testing)
        if any(invalid in url.lower() for invalid in ["localhost", "127.0.0.1"]):
            return False

        # Skip too short URLs
        if len(url) < 10:
            return False

        return True

    def _normalize_image_url(self, url: str) -> str:
        """Normalize image URL to ensure it's properly formatted."""
        if not url:
            return ""

        url = url.strip()

        # Handle protocol-relative URLs
        if url.startswith("//"):
            url = "https:" + url

        # Handle relative URLs (this is basic, may need domain context)
        if url.startswith("/") and not url.startswith("//"):
            # For now, skip relative URLs as we don't have base domain context
            return ""

        return url

    def _extract_image_from_webpage(self, page_url: str) -> str:
        """Extract image from webpage meta tags (Open Graph, Twitter Cards)."""
        try:
            # Only try this for a subset of URLs to avoid too many requests
            if not page_url or len(page_url) > 200:
                return ""

            # Skip if URL seems invalid
            if not (page_url.startswith("http://") or page_url.startswith("https://")):
                return ""

            # Quick check for common news domains that are likely to have meta tags
            trusted_domains = [
                # Global / UK
                "bbc.com",
                "cnn.com",
                "theguardian.com",
                "aljazeera.com",
                "independent.co.uk",
                "news.sky.com",
                "euronews.com",
                "time.com",
                # US national
                "nytimes.com",
                "washingtonpost.com",
                "nbcnews.com",
                "cbsnews.com",
                "abcnews.go.com",
                "foxnews.com",
                "politico.com",
                "axios.com",
                "thehill.com",
                "latimes.com",
                # Tech & business
                "bloomberg.com",
                "techcrunch.com",
                "theverge.com",
                "wired.com",
                "forbes.com",
                "arstechnica.com",
                "cnet.com",
                "zdnet.com",
                "venturebeat.com",
                "theregister.com",
                "spectrum.ieee.org",
                "cnbc.com",
                "marketwatch.com",
                "fortune.com",
                # Russia & Eastern Europe
                "meduza.io",
                "novayagazeta.eu",
                "thebell.io",
                "kommersant.ru",
                "rbc.ru",
                "vedomosti.ru",
                "interfax.ru",
                "themoscowtimes.com",
                "kyivindependent.com",
            ]

            if not any(domain in page_url.lower() for domain in trusted_domains):
                return ""

            response = self.session.get(
                page_url, timeout=5, headers={"User-Agent": self.config.USER_AGENT}
            )
            if response.status_code != 200:
                return ""

            soup = BeautifulSoup(response.content, "html.parser")

            # Check Open Graph image
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                if self._is_valid_image_url(img_url):
                    return self._normalize_image_url(img_url)

            # Check Twitter Card image
            twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
            if twitter_image and twitter_image.get("content"):
                img_url = twitter_image["content"]
                if self._is_valid_image_url(img_url):
                    return self._normalize_image_url(img_url)

            # Check for article featured image meta tags
            featured_meta = soup.find("meta", attrs={"name": "featured-image"})
            if featured_meta and featured_meta.get("content"):
                img_url = featured_meta["content"]
                if self._is_valid_image_url(img_url):
                    return self._normalize_image_url(img_url)

            return ""

        except Exception as e:
            logger.debug(f"Error extracting image from webpage {page_url}: {e}")
            return ""

    def get_rss_articles(
        self, feed_url: str, max_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract articles from RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            # Fetch with the session so requests' timeout, User-Agent, and
            # retry policy apply — feedparser.parse(url) has no timeout and
            # a hanging feed would block a worker thread indefinitely.
            response = self.session.get(feed_url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(f"RSS feed has issues: {feed_url}")

            articles = []
            for entry in feed.entries[:max_articles]:
                # Extract image from RSS entry
                image_url = self._extract_image_from_rss_entry(entry)

                # RSS dates are usually RFC-822 strings; feedparser exposes a
                # parsed struct_time, which we normalize to ISO so sorting and
                # storage use one format.
                published = entry.get("published", "")
                parsed_date = entry.get("published_parsed") or entry.get(
                    "updated_parsed"
                )
                if parsed_date:
                    published = datetime(
                        *parsed_date[:6], tzinfo=timezone.utc
                    ).isoformat()

                article = {
                    "title": entry.get("title", "No Title"),
                    "url": entry.get("link", ""),
                    "published": published,
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

    def _fetch_rss_feed_safe(self, feed_info: tuple) -> List[Dict[str, Any]]:
        """Thread-safe wrapper for RSS feed fetching."""
        feed_name, feed_url, max_articles = feed_info
        try:
            logger.info(f"🔄 Fetching {feed_name} in thread...")
            articles = self.get_rss_articles(feed_url, max_articles)
            logger.info(f"✅ {feed_name}: Found {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"❌ Error processing feed {feed_name}: {e}")
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
                category_config = self.config.INSHORTS_CATEGORIES.get(
                    category, {"max_limit": 5}
                )
                max_limit = max_articles_per_category or category_config["max_limit"]

                logger.info(f"Fetching InShorts articles for category: {category}")
                articles = self._fetch_inshorts_category(category, max_limit)

                if articles:
                    all_articles.extend(articles)
                    logger.info(
                        f"Retrieved {len(articles)} articles from InShorts {category}"
                    )
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
            params = {
                "category": category,
                "max_limit": max_limit,
                "include_card_data": "true",
            }

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

    def _parse_inshorts_article(
        self, item: Dict[str, Any], category: str
    ) -> Dict[str, Any]:
        """Parse a single InShorts article from API response.

        The InShorts API returns items with a 'news_obj' key containing the actual news data.
        """
        try:
            # Extract the news object - InShorts wraps the actual data in 'news_obj'
            news = item.get("news_obj", item)

            # Extract article data from the news object
            article = {
                "title": news.get("title", ""),
                "url": news.get("source_url", ""),
                "published": news.get("created_at", 0),
                "summary": news.get("content", ""),
                "source": "inshorts.com",
                "tags": [category],
                "image": news.get("image_url", ""),
                "inshorts_id": news.get("hash_id", ""),
                "original_source": news.get("author_name", ""),
            }

            # Validate required fields
            if not article["title"] or not article["url"]:
                logger.warning("Invalid InShorts article: missing title or URL")
                return None

            # Convert timestamp - InShorts uses Unix timestamp in milliseconds
            if article["published"]:
                try:
                    if isinstance(article["published"], (int, float)):
                        # Unix timestamp in milliseconds, convert to seconds
                        timestamp = article["published"] / 1000
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        article["published"] = dt.isoformat()
                    elif (
                        isinstance(article["published"], str)
                        and "T" in article["published"]
                    ):
                        # ISO format string
                        dt = datetime.fromisoformat(
                            article["published"].replace("Z", "+00:00")
                        )
                        article["published"] = dt.isoformat()
                except Exception as e:
                    logger.debug(f"Could not parse InShorts timestamp: {e}")
                    article["published"] = datetime.now(timezone.utc).isoformat()
            else:
                article["published"] = datetime.now(timezone.utc).isoformat()

            return article

        except Exception as e:
            logger.error(f"Error parsing InShorts article: {str(e)}")
            return None

    def get_inshorts_trending_topics(self) -> List[str]:
        """Get trending topics from InShorts API."""
        try:
            url = f"{self.config.INSHORTS_API_BASE_URL}/search/trending_topics"

            response = self.session.get(
                url, headers=self.config.INSHORTS_HEADERS, timeout=10
            )
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

    def _enhance_articles_with_images(
        self, articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Post-process articles to ensure maximum image coverage."""
        enhanced_articles = []
        articles_without_images = []

        # Separate articles with and without images
        for article in articles:
            if article.get("image", "").strip():
                enhanced_articles.append(article)
            else:
                articles_without_images.append(article)

        logger.info(
            f"Articles with images: {len(enhanced_articles)}, without images: {len(articles_without_images)}"
        )

        # Try to get images for articles without them
        for article in articles_without_images:
            enhanced_article = article.copy()

            # Try to extract image from the article URL
            if article.get("url"):
                try:
                    img_url = self._extract_image_from_webpage(article["url"])
                    if img_url:
                        enhanced_article["image"] = img_url
                        logger.debug(
                            f"Found image for article: {article['title'][:50]}..."
                        )
                    else:
                        # As a last resort, try to find a generic image based on source or tags
                        enhanced_article["image"] = self._get_fallback_image(article)

                except Exception as e:
                    logger.debug(f"Could not fetch image for {article['url']}: {e}")
                    # Set a fallback image
                    enhanced_article["image"] = self._get_fallback_image(article)
            else:
                enhanced_article["image"] = self._get_fallback_image(article)

            enhanced_articles.append(enhanced_article)

            # Add small delay to avoid overwhelming servers
            time.sleep(0.1)

        final_with_images = sum(
            1 for article in enhanced_articles if article.get("image", "").strip()
        )
        percentage = (
            (final_with_images / len(enhanced_articles)) * 100
            if enhanced_articles
            else 0
        )
        logger.info(
            f"Final image coverage: {final_with_images}/{len(enhanced_articles)} articles ({percentage:.1f}%)"
        )

        return enhanced_articles

    def _get_fallback_image(self, article: Dict[str, Any]) -> str:
        """Generate a fallback image URL based on article metadata."""
        # For now, return empty string. In production, this could:
        # 1. Use a placeholder service like https://via.placeholder.com/
        # 2. Use source-specific default images
        # 3. Use category-based stock images

        # Example placeholder (commented out to avoid external dependencies):
        # source = article.get('source', 'news').replace('.com', '').replace('.', '')
        # title_hash = hash(article.get('title', '')) % 10
        # return f"https://via.placeholder.com/400x300/4a90e2/ffffff?text={source.upper()}"

        return ""

    def _is_valid_article(self, article: Dict[str, Any]) -> bool:
        """Validate if an article meets quality criteria."""
        # Check required fields exist
        if not article.get("title") or not article.get("url"):
            logger.debug(
                f"Article missing required fields: {article.get('title', 'NO_TITLE')[:50]}"
            )
            return False

        # Validate title quality
        title = article["title"].strip()
        if len(title) < 10:
            logger.debug(f"Article title too short: {title}")
            return False

        if len(title) > 300:
            logger.debug(f"Article title too long: {title[:50]}...")
            return False

        # Check for common non-article titles
        skip_keywords = [
            "sign in",
            "sign up",
            "subscribe",
            "newsletter",
            "cookies",
            "privacy policy",
            "terms of service",
            "about us",
            "contact us",
            "home",
            "homepage",
        ]
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in skip_keywords):
            logger.debug(f"Article title contains skip keyword: {title[:50]}")
            return False

        # Validate URL
        url = article["url"].strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            logger.debug(f"Invalid URL format: {url[:50]}")
            return False

        # Check for user profile patterns (Medium, etc.)
        # Allow /@username/article-slug but not just /@username
        if "/@" in url and "/p/" not in url:
            # Check if it's just a profile URL (ends with username or has limited path)
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if p]
            # If path is just ['@username'] or ['@username', 'about'] etc, skip it
            if len(path_parts) <= 2 and path_parts[0].startswith("@"):
                logger.debug(f"Skipping user profile URL: {url}")
                return False

        # Validate source
        source = article.get("source", "").strip()
        if not source:
            logger.debug(
                f"Article missing source: {article.get('title', 'NO_TITLE')[:50]}"
            )
            return False

        # Check URL is not too long (might indicate malformed URLs)
        if len(url) > 500:
            logger.debug(f"URL too long: {url[:50]}...")
            return False

        # Ensure article has some content indicators
        # At minimum, should have title, URL, and source
        # Image is preferred but not required (will be enhanced later)

        return True

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

        # Add InShorts API as the highest priority task with more categories
        inshorts_categories = ["all_news", "top_stories"]
        tasks.append(("inshorts", "inshorts_api", inshorts_categories, None))

        # Use ThreadPoolExecutor for concurrent fetching
        max_workers = min(len(tasks), 5)  # Limit to 5 concurrent threads
        logger.info(
            f"📊 Processing {len(tasks)} sources with {max_workers} worker threads"
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {}

            for task in tasks:
                task_type, name, url_or_data, max_articles = task

                if task_type == "rss":
                    future = executor.submit(
                        self._fetch_rss_feed_safe, (name, url_or_data, max_articles)
                    )
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
                        all_articles.extend(articles)
                        logger.info(
                            f"✅ Completed {name}: Added {len(articles)} articles"
                        )
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

        # Enhance articles with better image coverage
        enhanced_articles = self._enhance_articles_with_images(final_articles)

        logger.info(
            f"📋 Final result: {len(enhanced_articles)} unique articles after deduplication, sorting, and image enhancement"
        )

        return enhanced_articles

    def _canonicalize_url(self, url: str) -> str:
        """Strip tracking parameters and fragments so the same article seen
        via different feeds deduplicates to a single URL."""
        try:
            parsed = urlparse(url)
            query = [
                (key, value)
                for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                if not key.startswith("utm_") and key not in self.TRACKING_PARAMS
            ]
            return urlunparse(parsed._replace(query=urlencode(query), fragment=""))
        except ValueError:
            return url

    def _remove_duplicates(
        self, articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL and filter invalid articles."""
        unique_articles = []
        seen_urls = set()
        invalid_count = 0

        for article in articles:
            # First validate article quality
            if not self._is_valid_article(article):
                invalid_count += 1
                continue

            url = self._canonicalize_url(article.get("url", ""))
            if url and url not in seen_urls:
                seen_urls.add(url)
                article["url"] = url
                unique_articles.append(article)

        duplicates_removed = len(articles) - len(unique_articles) - invalid_count
        logger.info(
            f"Removed {duplicates_removed} duplicate articles and {invalid_count} invalid articles"
        )
        return unique_articles

    def _sort_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort articles by published date (newest first)."""

        oldest = datetime.min.replace(tzinfo=timezone.utc)

        def get_sort_key(article):
            published = article.get("published", "")
            if not published:
                return oldest
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                try:
                    # RSS feeds use RFC-822 dates ("Thu, 07 Aug 2025 12:00:00 GMT")
                    dt = parsedate_to_datetime(published)
                except (TypeError, ValueError):
                    logger.debug(f"Failed to parse date '{published}'")
                    return oldest
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        return sorted(articles, key=get_sort_key, reverse=True)

    def save_articles_json(
        self, articles: List[Dict[str, Any]], filename: str = None
    ) -> str:
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
                print(
                    f"   Summary: {summary}{'...' if len(article['summary']) > 150 else ''}"
                )

    def get_urls_only(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract only URLs from articles."""
        return [article["url"] for article in articles if article.get("url")]
