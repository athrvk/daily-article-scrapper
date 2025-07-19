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
            image_fields = ['image', 'featured_image', 'thumbnail', 'img', 'picture']
            for field in image_fields:
                if hasattr(entry, field):
                    img_value = getattr(entry, field)
                    if isinstance(img_value, str) and img_value.strip():
                        if self._is_valid_image_url(img_value):
                            return img_value
                    elif hasattr(img_value, 'href') and img_value.href:
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
                    urls = srcset.split(',')
                    if urls:
                        first_url = urls[0].strip().split(' ')[0]
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
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('//')):
            return False
        
        # Skip common non-image extensions
        skip_extensions = ['.pdf', '.doc', '.docx', '.zip', '.mp4', '.avi', '.mp3']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip obviously invalid URLs (but allow example.com for testing)
        if any(invalid in url.lower() for invalid in ['localhost', '127.0.0.1']):
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
        if url.startswith('//'):
            url = 'https:' + url
        
        # Handle relative URLs (this is basic, may need domain context)
        if url.startswith('/') and not url.startswith('//'):
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
            if not (page_url.startswith('http://') or page_url.startswith('https://')):
                return ""
            
            # Quick check for common news domains that are likely to have meta tags
            trusted_domains = ['bbc.com', 'cnn.com', 'reuters.com', 'bloomberg.com', 
                              'techcrunch.com', 'theverge.com', 'wired.com', 'forbes.com']
            
            if not any(domain in page_url.lower() for domain in trusted_domains):
                return ""
            
            response = self.session.get(page_url, timeout=5, headers={'User-Agent': self.config.USER_AGENT})
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

    def _extract_medium_image(self, link_element) -> str:
        """Extract image URL from Medium article link context with enhanced methods."""
        try:
            # Look for nearby img elements in the same container
            parent = link_element.parent
            if parent:
                # Look for img tags in the parent container and siblings
                for container in [parent, parent.parent] if parent.parent else [parent]:
                    if not container:
                        continue
                    
                    # Look for img tags in the container
                    img = container.find("img")
                    if img:
                        # Check src attribute
                        if img.get("src"):
                            src = img["src"]
                            if self._is_valid_image_url(src):
                                return self._normalize_image_url(src)
                        
                        # Check data-src for lazy loading
                        if img.get("data-src"):
                            src = img["data-src"]
                            if self._is_valid_image_url(src):
                                return self._normalize_image_url(src)
                        
                        # Check srcset
                        if img.get("srcset"):
                            srcset = img["srcset"]
                            urls = srcset.split(',')
                            if urls:
                                first_url = urls[0].strip().split(' ')[0]
                                if self._is_valid_image_url(first_url):
                                    return self._normalize_image_url(first_url)
                
                # Look for background images in style attributes
                for element in container.find_all(["div", "span", "section", "article"], style=True):
                    style = element.get("style", "")
                    if "background-image" in style:
                        # Extract URL from background-image: url(...)
                        import re
                        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                        if match:
                            img_url = match.group(1)
                            if self._is_valid_image_url(img_url):
                                return self._normalize_image_url(img_url)
                
                # Look for picture elements (responsive images)
                picture = container.find("picture")
                if picture:
                    source = picture.find("source")
                    if source and source.get("srcset"):
                        srcset = source["srcset"]
                        urls = srcset.split(',')
                        if urls:
                            first_url = urls[0].strip().split(' ')[0]
                            if self._is_valid_image_url(first_url):
                                return self._normalize_image_url(first_url)

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
                    "title": getattr(entry, 'title', entry.get("title", "No Title") if hasattr(entry, 'get') else "No Title"),
                    "url": getattr(entry, 'link', entry.get("link", "") if hasattr(entry, 'get') else ""),
                    "published": getattr(entry, 'published', entry.get("published", "") if hasattr(entry, 'get') else ""),
                    "summary": getattr(entry, 'summary', entry.get("summary", "") if hasattr(entry, 'get') else ""),
                    "source": urlparse(feed_url).netloc,
                    "tags": [tag.term for tag in getattr(entry, 'tags', entry.get("tags", []) if hasattr(entry, 'get') else [])],
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

    def _enhance_articles_with_images(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process articles to ensure maximum image coverage."""
        enhanced_articles = []
        articles_without_images = []
        
        # Separate articles with and without images
        for article in articles:
            if article.get('image', '').strip():
                enhanced_articles.append(article)
            else:
                articles_without_images.append(article)
        
        logger.info(f"Articles with images: {len(enhanced_articles)}, without images: {len(articles_without_images)}")
        
        # Try to get images for articles without them
        for article in articles_without_images:
            enhanced_article = article.copy()
            
            # Try to extract image from the article URL
            if article.get('url'):
                try:
                    img_url = self._extract_image_from_webpage(article['url'])
                    if img_url:
                        enhanced_article['image'] = img_url
                        logger.debug(f"Found image for article: {article['title'][:50]}...")
                    else:
                        # As a last resort, try to find a generic image based on source or tags
                        enhanced_article['image'] = self._get_fallback_image(article)
                        
                except Exception as e:
                    logger.debug(f"Could not fetch image for {article['url']}: {e}")
                    # Set a fallback image
                    enhanced_article['image'] = self._get_fallback_image(article)
            else:
                enhanced_article['image'] = self._get_fallback_image(article)
            
            enhanced_articles.append(enhanced_article)
            
            # Add small delay to avoid overwhelming servers
            time.sleep(0.1)
        
        final_with_images = sum(1 for article in enhanced_articles if article.get('image', '').strip())
        percentage = (final_with_images / len(enhanced_articles)) * 100 if enhanced_articles else 0
        logger.info(f"Final image coverage: {final_with_images}/{len(enhanced_articles)} articles ({percentage:.1f}%)")
        
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

        # Add InShorts API as the highest priority task with more categories
        inshorts_categories = [
            "top_stories", "trending", "business", "technology", "world",
            "sports", "entertainment", "science", "automobile", "politics"
        ]
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
        
        # Enhance articles with better image coverage
        enhanced_articles = self._enhance_articles_with_images(final_articles)
        
        logger.info(
            f"📋 Final result: {len(enhanced_articles)} unique articles after deduplication, sorting, and image enhancement"
        )

        return enhanced_articles

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
