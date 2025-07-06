#!/usr/bin/env python3
"""
Daily Article URL Scraper
Scrapes articles from Medium and top news sites daily and stores them in MongoDB
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
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
        result = cleaner.purge_old_articles(months_old=Config.CLEANUP_MONTHS_OLD, dry_run=False)
        
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


def main():
    """Main function to run the article scraper."""
    setup_logging()
    
    logger.info("Starting daily article scraping...")
    
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
        json_filename = scraper.save_articles_json(articles)
        
        # Save to MongoDB
        with DatabaseManager() as db:
            if db.connect():
                # Create indexes if they don't exist
                db.create_indexes()
                
                # Save articles
                success = db.save_articles(articles)
                if success:
                    logger.info("Articles successfully saved to MongoDB")
                    
                    # Print statistics
                    total_count = db.get_article_count()
                    logger.info(f"Total articles in database: {total_count}")
                else:
                    logger.error("Failed to save articles to MongoDB")
            else:
                logger.error("Could not connect to MongoDB, articles saved to JSON only")
        
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