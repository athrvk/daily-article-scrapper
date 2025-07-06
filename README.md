# Daily Article Scraper

A Python application that scrapes articles from various tech news sources and stores them in MongoDB. Designed to run as a scheduled job via GitHub Actions.

## Features

- **Multi-source scraping**: Extracts articles from Medium, TechCrunch, HackerNews, Dev.to, BBC Tech, CNN Tech, Reuters Tech, and more
- **MongoDB integration**: Stores articles with deduplication and indexing
- **Automatic cleanup**: Removes articles older than 2 months (configurable)
- **GitHub Actions workflow**: Automated daily scraping via cron jobs
- **Professional structure**: Modular codebase with proper configuration management
- **Comprehensive logging**: Detailed logging with file and console output
- **Error handling**: Robust error handling and retry mechanisms
- **Rate limiting**: Respectful scraping with configurable delays
- **Database monitoring**: Statistics and health checking tools

## Project Structure

```
daily-article-scrapper/
├── .github/
│   └── workflows/
│       └── daily-scraper.yml      # GitHub Actions workflow
├── config/
│   ├── __init__.py
│   └── settings.py                # Configuration settings
├── src/
│   ├── __init__.py
│   ├── database.py               # MongoDB operations
│   └── scraper.py                # Core scraping logic
├── tests/                        # Test files
├── scripts/                      # Utility scripts
│   ├── setup.sh                  # Environment setup
│   ├── manage.sh                 # Project management
│   ├── status_check.py           # Health monitoring
│   └── cleanup_articles.py       # Database cleanup
├── logs/                         # Log files (created at runtime)
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore file
├── main.py                       # Main application entry point
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── CLEANUP_GUIDE.md              # Database cleanup documentation
└── README.md                     # This file
```

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd daily-article-scrapper
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your MongoDB configuration
```

### 5. Set up MongoDB

Make sure you have access to a MongoDB instance. You can use:
- Local MongoDB installation
- MongoDB Atlas (cloud)
- Docker container

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=article_scraper
MONGODB_COLLECTION=articles

# Scraping Configuration
TARGET_ARTICLE_COUNT=20
RATE_LIMIT_DELAY=2
MAX_RETRIES=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log

# Cleanup Configuration
AUTO_CLEANUP_ENABLED=true
CLEANUP_MONTHS_OLD=2
```

### MongoDB Setup

The application will automatically:
- Create the database and collection if they don't exist
- Set up indexes for optimal performance
- Handle duplicate articles based on URL

## Usage

### Local Development

```bash
# Run the scraper once
python main.py

# Run with custom article count
TARGET_ARTICLE_COUNT=50 python main.py

# Check database statistics
python scripts/cleanup_articles.py --stats

# Manual cleanup (dry run)
python scripts/cleanup_articles.py --dry-run

# Manual cleanup (execute)
python scripts/cleanup_articles.py
```

### GitHub Actions Setup

1. **Set up repository secrets**:
   - Go to your repository Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `MONGODB_URI`: Your MongoDB connection string
     - `MONGODB_DATABASE`: Database name
     - `MONGODB_COLLECTION`: Collection name

2. **Configure the schedule**:
   - Edit `.github/workflows/daily-scraper.yml`
   - Modify the cron expression to your preferred time

3. **Manual trigger**:
   - Go to Actions tab in your repository
   - Select "Daily Article Scraper"
   - Click "Run workflow"

## Development

### Setting up development environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Format code
black src/ config/ main.py

# Lint code
flake8 src/ config/ main.py

# Check database statistics
bash scripts/manage.sh stats

# Manual cleanup
bash scripts/manage.sh cleanup
```

### Adding new sources

1. **RSS feeds**: Add to `config/settings.py` in the `RSS_FEEDS` dictionary
2. **Custom scrapers**: Add methods to `src/scraper.py`
3. **Configuration**: Update environment variables as needed

## Database Cleanup

The application includes an automated cleanup system that removes articles older than 2 months by default. This prevents the database from growing indefinitely and ensures optimal performance.

### Cleanup Features

- **Automatic cleanup**: Runs before each scraping session
- **Configurable retention**: Adjust with `CLEANUP_MONTHS_OLD` environment variable
- **Manual control**: Can be disabled with `AUTO_CLEANUP_ENABLED=false`
- **Safe operations**: Dry-run mode available for testing

### Cleanup Commands

```bash
# View database statistics
python scripts/cleanup_articles.py --stats
bash scripts/manage.sh stats

# Preview cleanup (dry run)
python scripts/cleanup_articles.py --dry-run

# Manual cleanup
python scripts/cleanup_articles.py
bash scripts/manage.sh cleanup

# Custom retention period
python scripts/cleanup_articles.py --months 3
```

### Configuration

Set cleanup behavior in your `.env` file:

```env
AUTO_CLEANUP_ENABLED=true    # Enable/disable automatic cleanup
CLEANUP_MONTHS_OLD=2         # Keep articles for 2 months
```

For detailed cleanup documentation, see `CLEANUP_GUIDE.md`.

## API Documentation

### ArticleScraper Class

Main scraping functionality:

```python
from src.scraper import ArticleScraper

scraper = ArticleScraper()
articles = scraper.scrape_daily_articles(target_count=20)
```

### DatabaseManager Class

MongoDB operations:

```python
from src.database import DatabaseManager

with DatabaseManager() as db:
    db.save_articles(articles)
    recent = db.get_recent_articles(days=7)
```

## Data Structure

Articles are stored with the following structure:

```json
{
  "_id": "https://example.com/article_20250706",
  "title": "Article Title",
  "url": "https://example.com/article",
  "published": "2025-07-06T10:30:00Z",
  "summary": "Article summary text",
  "source": "techcrunch.com",
  "tags": ["technology", "ai"],
  "scraped_at": "2025-07-06T13:22:46.123Z"
}
```

## Monitoring and Logs

- **Local logs**: Check `logs/scraper.log`
- **Database stats**: Run `python scripts/cleanup_articles.py --stats`
- **Management tools**: Use `bash scripts/manage.sh [command]`
- **GitHub Actions**: View logs in the Actions tab
- **MongoDB**: Query the database for article statistics

## Troubleshooting

### Common Issues

1. **MongoDB connection failed**:
   - Check your `MONGODB_URI` configuration
   - Ensure MongoDB is running and accessible
   - Verify network connectivity

2. **No articles found**:
   - Check internet connectivity
   - Some RSS feeds might be temporarily unavailable
   - Increase `MAX_RETRIES` in configuration

3. **Rate limiting**:
   - Increase `RATE_LIMIT_DELAY` to be more respectful to servers
   - Some sites might block requests; consider using proxies

4. **Database growing too large**:
   - Check if cleanup is enabled: `AUTO_CLEANUP_ENABLED=true`
   - Adjust retention period: `CLEANUP_MONTHS_OLD=2`
   - Run manual cleanup: `bash scripts/manage.sh cleanup`

5. **Old articles not being deleted**:
   - Verify cleanup configuration in `.env`
   - Check logs for cleanup errors
   - Run cleanup manually to test

### GitHub Actions Issues

1. **Secrets not configured**:
   - Ensure all required secrets are set in repository settings

2. **Workflow not running**:
   - Check the cron expression syntax
   - Ensure the repository is not dormant (GitHub disables workflows on inactive repos)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Search existing GitHub issues
3. Create a new issue with detailed information

## Acknowledgments

- Built with Python 3.11+
- Uses feedparser for RSS parsing
- Beautiful Soup for web scraping
- MongoDB for data storage
- GitHub Actions for automation
