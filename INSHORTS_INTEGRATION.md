# InShorts API Integration Documentation

## Overview

This document describes the integration of InShorts API as a new article source in the Daily Article Scraper. InShorts is a popular news aggregation service that provides short, concise news articles from various sources.

## API Endpoints Integrated

The following InShorts API endpoints have been integrated:

1. **News Articles**: `https://inshorts.com/api/en/news`
   - Parameters: `category`, `max_limit`, `include_card_data`, `news_offset`
   - Categories: `top_stories`, `trending`, `business`, `technology`, `world`

2. **Trending Topics**: `https://inshorts.com/api/en/search/trending_topics`
   - Returns current trending topics from InShorts

## Configuration

### New Settings Added

In `config/settings.py`, the following new configuration has been added:

```python
# InShorts API configuration
INSHORTS_API_BASE_URL = "https://inshorts.com/api/en"
INSHORTS_CATEGORIES = {
    'top_stories': {'max_limit': 10, 'priority': 1},
    'trending': {'max_limit': 8, 'priority': 2},
    'business': {'max_limit': 5, 'priority': 3},
    'technology': {'max_limit': 5, 'priority': 4},
    'world': {'max_limit': 5, 'priority': 5}
}

# Headers for InShorts API to avoid bot detection
INSHORTS_HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': USER_AGENT
}
```

## New Methods Added

### ArticleScraper Class Methods

#### `scrape_inshorts_articles(categories, max_articles_per_category)`
- **Purpose**: Main method to scrape articles from InShorts API
- **Parameters**: 
  - `categories`: List of category names to scrape (default: all configured categories)
  - `max_articles_per_category`: Override default max articles per category
- **Returns**: List of article dictionaries
- **Features**: 
  - Supports multiple categories
  - Rate limiting between requests
  - Comprehensive error handling

#### `_fetch_inshorts_category(category, max_limit, news_offset)`
- **Purpose**: Fetch articles from a specific InShorts category
- **Parameters**:
  - `category`: Category name (e.g., 'top_stories', 'trending')
  - `max_limit`: Maximum number of articles to fetch
  - `news_offset`: Pagination offset (optional)
- **Returns**: List of parsed articles
- **Features**:
  - Handles API requests with proper headers
  - JSON response parsing
  - Network error handling

#### `_parse_inshorts_article(item, category)`
- **Purpose**: Parse a single article from InShorts API response
- **Parameters**:
  - `item`: Raw article data from API
  - `category`: Category name for tagging
- **Returns**: Parsed article dictionary or None if invalid
- **Features**:
  - Validates required fields
  - Handles timestamp conversion
  - Adds category tags

#### `get_inshorts_trending_topics()`
- **Purpose**: Fetch trending topics from InShorts
- **Returns**: List of trending topic names
- **Features**:
  - Handles different response formats
  - Error handling for network issues

#### `_fetch_inshorts_safe(categories)`
- **Purpose**: Thread-safe wrapper for InShorts scraping
- **Parameters**: `categories` - List of categories to scrape
- **Returns**: List of articles
- **Features**:
  - Thread-safe operations
  - Comprehensive error handling
  - Logging for debugging

## Article Data Structure

InShorts articles are stored with the following structure:

```python
{
    'title': str,                    # Article title
    'url': str,                      # Source article URL
    'published': str,                # ISO format timestamp
    'summary': str,                  # Article content/summary
    'source': 'inshorts.com',       # Always 'inshorts.com'
    'tags': List[str],               # Tags including category
    'image': str,                    # Image URL
    'inshorts_id': str,              # Unique InShorts identifier
    'original_source': str           # Original news source name
}
```

## Integration with Main Scraper

The InShorts API has been integrated into the main multi-threaded scraping system:

1. **Threading**: InShorts scraping runs in parallel with RSS feeds and Medium scraping
2. **Error Handling**: Network failures don't affect other sources
3. **Deduplication**: InShorts articles are included in the deduplication process
4. **Rate Limiting**: Respects configured delays between requests

## Bot Detection Prevention

To avoid being blocked by InShorts:

1. **Proper Headers**: Uses realistic browser headers including Chrome user agent
2. **Rate Limiting**: Implements delays between requests
3. **Request Patterns**: Mimics normal browser behavior
4. **Error Handling**: Gracefully handles rate limiting or blocking

## Error Handling

The integration includes comprehensive error handling:

- **Network Errors**: Handles connection failures gracefully
- **JSON Parsing**: Handles malformed responses
- **Invalid Data**: Validates article data before processing
- **API Changes**: Flexible parsing to handle minor API changes
- **Rate Limiting**: Handles API rate limits without crashing

## Testing

### Unit Tests Added

1. `test_scrape_inshorts_articles()` - Tests main scraping functionality
2. `test_fetch_inshorts_category_error_handling()` - Tests error handling
3. `test_fetch_inshorts_category_invalid_json()` - Tests JSON parsing errors
4. `test_parse_inshorts_article()` - Tests article parsing
5. `test_parse_inshorts_article_missing_fields()` - Tests validation
6. `test_get_inshorts_trending_topics()` - Tests trending topics
7. `test_get_inshorts_trending_topics_error()` - Tests error handling

### Integration Tests

- Full integration with main scraper
- Thread-safe operations
- Error handling in production environment

## Usage Examples

### Basic Usage

```python
from src.scraper import ArticleScraper
from config.settings import Config

scraper = ArticleScraper(Config())

# Scrape all categories
articles = scraper.scrape_inshorts_articles()

# Scrape specific categories
articles = scraper.scrape_inshorts_articles(['top_stories', 'technology'])

# Get trending topics
topics = scraper.get_inshorts_trending_topics()
```

### With Main Scraper

```python
# InShorts is automatically included in the main scraper
articles = scraper.scrape_daily_articles(target_count=50)

# InShorts articles will be included in the results
inshorts_articles = [a for a in articles if a['source'] == 'inshorts.com']
```

## Performance Considerations

- **Thread Safety**: All InShorts methods are thread-safe
- **Rate Limiting**: Configured delays prevent overwhelming the API
- **Memory Usage**: Efficient parsing and processing
- **Error Recovery**: Graceful handling of temporary failures

## Maintenance

### Monitoring

- Check logs for InShorts-related errors
- Monitor API response times
- Watch for changes in API structure

### Updates

- Update headers if bot detection improves
- Adjust rate limits based on usage patterns
- Add new categories as InShorts expands

## Troubleshooting

### Common Issues

1. **No Articles Retrieved**
   - Check internet connectivity
   - Verify API endpoints are accessible
   - Check for rate limiting

2. **Bot Detection**
   - Update user agent headers
   - Increase rate limiting delays
   - Check for IP blocking

3. **JSON Parsing Errors**
   - API response format may have changed
   - Check for valid JSON in responses
   - Update parsing logic if needed

### Debug Logging

Enable detailed logging to diagnose issues:

```python
import logging
logging.getLogger('src.scraper').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Pagination Support**: Implement full pagination for large result sets
2. **Search API**: Add support for InShorts search functionality
3. **Personalization**: Support for user-specific categories
4. **Caching**: Add intelligent caching for frequently accessed articles
5. **Analytics**: Track performance metrics for InShorts integration