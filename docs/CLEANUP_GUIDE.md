# 🧹 Article Cleanup System

## Overview

The Daily Article Scraper now includes an automated cleanup system that purges articles older than 2 months before each scraping session. This prevents the database from growing indefinitely and ensures optimal performance.

## Features

### ✅ **Automatic Cleanup**
- Runs before each daily scraping session
- Removes articles older than 2 months (configurable)
- Can be disabled via environment variable
- Graceful failure handling (scraping continues even if cleanup fails)

### ✅ **Manual Cleanup Tools**
- Standalone cleanup script with dry-run option
- Database statistics and monitoring
- Flexible retention period configuration

### ✅ **Integration**
- Seamlessly integrated into existing workflow
- Works with GitHub Actions
- Logging and monitoring included

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Cleanup Configuration
AUTO_CLEANUP_ENABLED=true      # Enable/disable automatic cleanup
CLEANUP_MONTHS_OLD=2           # Number of months to retain articles
```

### Default Settings
- **Retention Period**: 2 months
- **Auto Cleanup**: Enabled
- **Runs**: Before each scraping session

## Usage

### 1. Automatic Cleanup (Recommended)

Cleanup runs automatically when you execute the main scraper:

```bash
# Cleanup will run automatically before scraping
python main.py

# Or using the management script
bash scripts/manage.sh run
```

### 2. Manual Cleanup

#### View Database Statistics
```bash
# Show database stats
python scripts/cleanup_articles.py --stats
# Or
bash scripts/manage.sh stats
```

#### Dry Run (Preview)
```bash
# See what would be deleted without actually deleting
python scripts/cleanup_articles.py --dry-run
```

#### Manual Cleanup
```bash
# Clean up articles older than 2 months
python scripts/cleanup_articles.py

# Custom retention period (3 months)
python scripts/cleanup_articles.py --months 3

# Or using management script
bash scripts/manage.sh cleanup
```

## Data Flow

```
1. Daily Scraper Starts
2. Cleanup Check (if AUTO_CLEANUP_ENABLED=true)
3. Connect to MongoDB
4. Find articles older than CLEANUP_MONTHS_OLD
5. Delete old articles (if any)
6. Log cleanup results
7. Continue with article scraping
8. Save new articles to database
```

## Cleanup Logic

### What Gets Deleted
- Articles where `scraped_at` < (current_date - CLEANUP_MONTHS_OLD * 30 days)
- Uses the `scraped_at` field (when the article was added to database)
- NOT the `published` field (when the article was originally published)

### Safety Features
- **Dry Run Mode**: Preview deletions without actually deleting
- **Graceful Failure**: If cleanup fails, scraping continues normally
- **Logging**: All cleanup operations are logged
- **Configurable**: Can be disabled or adjusted per environment

## Database Statistics

The stats command shows:
- Total articles in database
- Articles from last 7 days
- Articles from last 30 days  
- Articles older than 2 months
- Top sources by article count

Example output:
```
============================================================
DATABASE STATISTICS
============================================================
Total articles: 2,450
Last week: 140
Last month: 620
Older than 2 months: 850
Database: article_scraper
Collection: articles

Top sources:
  medium.com: 980 articles
  techcrunch.com: 450 articles
  dev.to: 320 articles
  hnrss.org: 280 articles
  ...
============================================================
```

## GitHub Actions Integration

The cleanup system works automatically with GitHub Actions:

```yaml
env:
  AUTO_CLEANUP_ENABLED: true
  CLEANUP_MONTHS_OLD: 2
  # ... other environment variables
```

## Monitoring

### Logs
Cleanup operations are logged with these messages:
- `"Running cleanup of old articles..."`
- `"Cleanup completed: Deleted X articles older than Y months"`
- `"No old articles to clean up"`
- `"Cleanup failed: [error message]"`

### Log Locations
- **Local**: `logs/scraper.log`
- **GitHub Actions**: Workflow logs and uploaded artifacts

## Examples

### Example 1: Check Database Status
```bash
cd /path/to/daily-article-scrapper
source venv/bin/activate
python scripts/cleanup_articles.py --stats
```

### Example 2: Preview Cleanup
```bash
# See what would be deleted
python scripts/cleanup_articles.py --dry-run --months 3
```

### Example 3: Custom Cleanup
```bash
# Keep only 1 month of articles
python scripts/cleanup_articles.py --months 1
```

### Example 4: Disable Auto Cleanup
```env
# In .env file
AUTO_CLEANUP_ENABLED=false
```

## Troubleshooting

### Common Issues

**1. Cleanup fails but scraping continues**
- This is normal behavior - cleanup failure doesn't stop scraping
- Check logs for specific error messages
- Verify MongoDB connection

**2. No articles being deleted**
- Database might not have articles older than retention period
- Use `--stats` to see age distribution of articles
- Check if `scraped_at` field exists in older records

**3. Cleanup taking too long**
- Large number of old articles (>10,000)
- Consider running manual cleanup during off-peak hours
- MongoDB indexes help with performance

### Manual Recovery

If you need to manually clean up or restore:

```bash
# Backup before major cleanup
bash scripts/manage.sh backup

# Manual cleanup with custom date
python scripts/cleanup_articles.py --months 6

# Check results
python scripts/cleanup_articles.py --stats
```

## Performance Impact

### Database Size Management
- Prevents unlimited database growth
- Improves query performance
- Reduces storage costs (especially important for cloud databases)

### Cleanup Performance
- Uses indexed queries (`scraped_at` field is indexed)
- Bulk delete operations for efficiency
- Minimal impact on daily scraping performance

## Best Practices

1. **Monitor Regularly**: Check database stats weekly
2. **Backup Important Data**: Create backups before major cleanups
3. **Adjust Retention**: Increase retention period for important historical data
4. **Test Changes**: Use dry-run mode when changing retention periods
5. **Monitor Logs**: Watch for cleanup failures or unusual patterns
