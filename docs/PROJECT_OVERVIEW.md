# Project Structure Overview

## Daily Article Scraper - Professional Python Project

This document provides an overview of the project structure and how to use it.

## 📁 Directory Structure

```
daily-article-scrapper/
│
├── 📋 Project Files
│   ├── README.md                    # Comprehensive project documentation
│   ├── requirements.txt             # Production dependencies
│   ├── requirements-dev.txt         # Development dependencies
│   ├── setup.py                     # Package setup configuration
│   ├── pyproject.toml              # Modern Python project configuration
│   ├── setup.cfg                   # Linting and type checking configuration
│   ├── Makefile                    # Common development tasks
│   ├── .gitignore                  # Git ignore patterns
│   ├── .env.example                # Environment variables template
│   └── .env                        # Your local environment variables
│
├── 🗂️ Source Code
│   ├── main.py                     # Main application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Configuration management
│   └── src/
│       ├── __init__.py
│       ├── scraper.py              # Core scraping logic
│       └── database.py             # MongoDB operations
│
├── 🧪 Testing
│   ├── tests/
│   │   ├── conftest.py             # Test configuration and fixtures
│   │   └── test_scraper.py         # Scraper unit tests
│
├── 🔧 Automation & Deployment
│   ├── .github/
│   │   └── workflows/
│   │       └── daily-scraper.yml   # GitHub Actions workflow
│
├── 📜 Scripts & Utilities
│   ├── scripts/
│   │   ├── setup.sh                # Development environment setup
│   │   ├── status_check.py         # Project health check
│   │   ├── cleanup_articles.py     # Database cleanup utility
│   │   └── manage.sh               # Project management utility
│
├── 📊 Runtime Data (Generated)
│   ├── venv/                       # Python virtual environment
│   ├── logs/                       # Application logs
│   ├── data/                       # Data storage directory
│   ├── backups/                    # Article backups directory
│   └── articles_YYYYMMDD.json      # Daily article backup files
│
├── 📚 Documentation
│   ├── CLEANUP_GUIDE.md            # Database cleanup documentation
│   └── PROJECT_OVERVIEW.md         # This file
```

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Clone and navigate to project
git clone <your-repo-url>
cd daily-article-scrapper

# Set up development environment
bash scripts/setup.sh --dev

# Or use the management script
bash scripts/manage.sh setup
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your MongoDB configuration
nano .env
```

### 3. Run the Scraper
```bash
# Activate virtual environment
source venv/bin/activate

# Run once
python main.py

# Or use management script
bash scripts/manage.sh run
```

## 🛠️ Development Commands

Using the management script (`scripts/manage.sh`):
- `setup` - Set up development environment
- `status` - Check project health
- `run` - Run the article scraper
- `test` - Run unit tests
- `lint` - Check code quality
- `format` - Format code with Black and isort
- `clean` - Clean temporary files
- `install` - Install dependencies
- `update` - Update dependencies
- `backup` - Create backup of articles
- `cleanup` - Clean up old articles (2+ months)
- `stats` - Show database statistics
- `logs` - Show recent logs

Using Make commands:
- `make setup` - Set up development environment
- `make test` - Run tests with coverage
- `make lint` - Run linting
- `make format` - Format code
- `make run` - Run the scraper
- `make clean` - Clean temporary files

## 🤖 GitHub Actions Setup

1. **Repository Secrets** (Settings → Secrets and variables → Actions):
   - `MONGODB_URI` - Your MongoDB connection string
   - `MONGODB_DATABASE` - Database name
   - `MONGODB_COLLECTION` - Collection name

2. **Workflow Schedule**:
   - Current: Daily at 8:00 AM UTC
   - Edit `.github/workflows/daily-scraper.yml` to modify

3. **Manual Trigger**:
   - Go to Actions tab → "Daily Article Scraper" → "Run workflow"

## 📊 Features

### Core Functionality
- ✅ Multi-source article scraping (Medium, TechCrunch, HackerNews, etc.)
- ✅ MongoDB integration with deduplication
- ✅ Automatic database cleanup (configurable retention)
- ✅ JSON backup for reliability
- ✅ Rate limiting and error handling
- ✅ Comprehensive logging

### Developer Experience
- ✅ Professional project structure
- ✅ Virtual environment management
- ✅ Automated testing framework
- ✅ Code formatting (Black, isort)
- ✅ Linting (flake8, mypy)
- ✅ Management scripts

### DevOps & Automation
- ✅ GitHub Actions CI/CD
- ✅ Automated daily scraping
- ✅ Log collection and artifact storage
- ✅ Environment variable management

## 🔧 Configuration Options

### Environment Variables (.env)
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

### Customization
- **Add new sources**: Edit `config/settings.py`
- **Modify scraping logic**: Update `src/scraper.py`
- **Database operations**: Modify `src/database.py`
- **Scheduling**: Edit `.github/workflows/daily-scraper.yml`

## 📈 Data Flow

1. **Cleanup** (`scripts/cleanup_articles.py`) removes articles older than 2 months (configurable)
2. **Scraper** (`src/scraper.py`) fetches articles from multiple RSS feeds
3. **Processing** removes duplicates, sorts by date, limits to target count
4. **Storage** saves to MongoDB (primary) and JSON file (backup)
5. **Logging** tracks all operations with detailed logs
6. **GitHub Actions** runs daily and stores artifacts

## 🔍 Monitoring

### Local Development
- **Logs**: `logs/scraper.log`
- **Articles**: `articles_YYYYMMDD.json`
- **Status**: `bash scripts/manage.sh status`
- **Database Stats**: `bash scripts/manage.sh stats`
- **Cleanup**: `bash scripts/manage.sh cleanup`

### Production (GitHub Actions)
- **Workflow logs**: Actions tab in GitHub
- **Artifacts**: Downloaded logs and JSON files
- **Notifications**: Configure via GitHub notifications

## 🚨 Troubleshooting

### Common Issues
1. **Import errors**: Ensure virtual environment is activated
2. **MongoDB connection**: Check URI and service status
3. **No articles found**: Check internet connectivity and RSS feeds
4. **Rate limiting**: Some sites may temporarily block requests
5. **Database growing too large**: Check cleanup configuration
6. **Old articles not being cleaned**: Verify `AUTO_CLEANUP_ENABLED=true`

### Getting Help
1. Check logs in `logs/scraper.log`
2. Run `bash scripts/manage.sh status`
3. Check database stats: `bash scripts/manage.sh stats`
4. Review GitHub Actions logs
5. Check MongoDB connectivity
6. Read cleanup guide: `CLEANUP_GUIDE.md`

## 📋 Next Steps

### Immediate
- [ ] Configure MongoDB connection
- [ ] Set up GitHub Actions secrets
- [ ] Test the complete workflow

## 🎯 Success Metrics

- ✅ Project structure follows Python best practices
- ✅ Code is modular and maintainable
- ✅ Automated testing and linting
- ✅ Production-ready deployment
- ✅ Comprehensive documentation
- ✅ Error handling and logging
- ✅ GitHub Actions automation
- ✅ Database cleanup and optimization
- ✅ Monitoring and statistics tools
