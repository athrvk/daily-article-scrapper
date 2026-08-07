#!/usr/bin/env python3
"""
Daily Article URL Scraper
Scrapes articles from Medium and top news sites daily and stores them in MongoDB
"""

import sys
import logging
from pathlib import Path

from src.scraper import ArticleScraper
from src.database import DatabaseManager
from config.settings import Config


# Configure logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger(__name__)


def cleanup_old_articles():
    """Run cleanup of old articles before scraping."""
    try:
        # Check if auto cleanup is enabled
        if not Config.AUTO_CLEANUP_ENABLED:
            logger.info("Auto cleanup is disabled, skipping cleanup")
            return

        logger.info("Running cleanup of old articles...")

        # Import cleanup functionality
        from scripts.cleanup_articles import ArticleCleaner

        cleaner = ArticleCleaner()
        result = cleaner.purge_old_articles(
            months_old=Config.CLEANUP_MONTHS_OLD, dry_run=False
        )

        if result["success"]:
            if result.get("deleted_count", 0) > 0:
                logger.info(f"Cleanup completed: {result['message']}")
            else:
                logger.info("No old articles to clean up")
        else:
            logger.warning(f"Cleanup failed: {result.get('error', 'Unknown error')}")

    except ImportError:
        logger.warning("Cleanup script not available, skipping cleanup")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
        # Don't fail the main process if cleanup fails


def validate_environment():
    """Validate required environment variables."""
    logger.info("🔍 Validating environment configuration...")

    # Check MongoDB configuration (without exposing sensitive data)
    has_uri = bool(Config.MONGODB_URI and Config.MONGODB_URI.strip())
    logger.info(f"MongoDB URI: {'✅ Configured' if has_uri else '❌ Not set'}")
    logger.info(f"MongoDB Database: {Config.MONGODB_DATABASE}")
    logger.info(f"MongoDB Collection: {Config.MONGODB_COLLECTION}")
    logger.info(f"Target Article Count: {Config.TARGET_ARTICLE_COUNT}")
    logger.info(f"Auto Cleanup Enabled: {Config.AUTO_CLEANUP_ENABLED}")

    # Validate required settings
    if not has_uri or Config.MONGODB_URI == "mongodb://localhost:27017/":
        logger.warning(
            "⚠️ MongoDB URI appears to be default/local - check if production URI is configured"
        )

    if not Config.MONGODB_DATABASE:
        logger.error("❌ MongoDB database name not configured")
        return False

    if not Config.MONGODB_COLLECTION:
        logger.error("❌ MongoDB collection name not configured")
        return False

    logger.info("✅ Environment validation completed")
    return True


def main():
    """Main function to run the article scraper."""
    setup_logging()

    logger.info("🚀 Starting daily article scraping...")

    # Validate environment first
    if not validate_environment():
        logger.error("❌ Environment validation failed")
        sys.exit(1)

    try:
        # Run cleanup of old articles first
        cleanup_old_articles()

        # Initialize scraper
        scraper = ArticleScraper()

        # Scrape articles
        articles = scraper.scrape_daily_articles()

        if not articles:
            logger.warning("No articles found")
            return

        # Print articles to console
        scraper.print_articles(articles)

        # Save to JSON file (backup)
        scraper.save_articles_json(articles)

        # Save to MongoDB
        logger.info("💾 Attempting to save articles to MongoDB...")
        with DatabaseManager() as db:
            if db.connect():
                logger.info("🔗 MongoDB connection established")

                # Create indexes if they don't exist
                logger.info("📊 Creating/updating database indexes...")
                db.create_indexes()

                # Save articles
                logger.info(f"💾 Saving {len(articles)} articles to database...")
                success = db.save_articles(articles)

                if success:
                    logger.info("✅ Articles successfully saved to MongoDB")

                    # Print statistics
                    total_count = db.get_article_count()
                    logger.info(f"📈 Total articles in database: {total_count}")
                else:
                    logger.error("❌ Failed to save articles to MongoDB")
            else:
                logger.error(
                    "❌ Could not connect to MongoDB - check connection settings"
                )
                logger.error("📁 Articles saved to JSON backup only")
                logger.error("🔧 Troubleshooting tips:")
                logger.error("   - Verify MONGODB_URI is correct")
                logger.error("   - Check if MongoDB server is accessible")
                logger.error("   - Ensure network connectivity")
                logger.error("   - Validate authentication credentials")

        # Print URLs for easy access
        print(f"\n{'='*60}")
        print("ARTICLE URLS:")
        print(f"{'='*60}")
        urls = scraper.get_urls_only(articles)
        for i, url in enumerate(urls, 1):
            print(f"{i:2d}. {url}")

        logger.info(f"Successfully processed {len(articles)} articles")

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
