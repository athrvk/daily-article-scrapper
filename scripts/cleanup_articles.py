#!/usr/bin/env python3
"""
Article Database Cleanup Script
Purges articles older than specified months from MongoDB
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

# Add the project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database import DatabaseManager
from config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ArticleCleaner:
    """Handles cleanup of old articles from the database."""
    
    def __init__(self, config: Config = None):
        """Initialize the cleaner with configuration."""
        self.config = config or Config()
        self.db_manager = DatabaseManager()
    
    def purge_old_articles(self, months_old: int = 2, dry_run: bool = False) -> dict:
        """
        Purge articles older than specified months.
        
        Args:
            months_old: Number of months back to keep articles
            dry_run: If True, only count articles without deleting
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=months_old * 30)
            logger.info(f"Purging articles older than {cutoff_date.strftime('%Y-%m-%d')}")
            
            # Connect to database
            if not self.db_manager.connect():
                logger.error("Failed to connect to database")
                return {"success": False, "error": "Database connection failed"}
            
            # Count articles to be deleted
            filter_query = {"scraped_at": {"$lt": cutoff_date}}
            articles_count = self.db_manager.collection.count_documents(filter_query)
            
            if articles_count == 0:
                logger.info("No articles found older than specified date")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No old articles to delete"
                }
            
            logger.info(f"Found {articles_count} articles older than {months_old} months")
            
            if dry_run:
                logger.info("DRY RUN: Would delete these articles")
                
                # Get sample of articles that would be deleted
                sample_articles = list(
                    self.db_manager.collection.find(
                        filter_query,
                        {"title": 1, "source": 1, "scraped_at": 1}
                    ).limit(5)
                )
                
                logger.info("Sample articles that would be deleted:")
                for article in sample_articles:
                    logger.info(f"  - {article.get('title', 'No title')} "
                              f"({article.get('source', 'Unknown')}) "
                              f"- {article.get('scraped_at', 'No date')}")
                
                return {
                    "success": True,
                    "would_delete_count": articles_count,
                    "dry_run": True,
                    "sample_articles": sample_articles
                }
            
            # Delete old articles
            logger.info(f"Deleting {articles_count} old articles...")
            delete_result = self.db_manager.collection.delete_many(filter_query)
            
            logger.info(f"Successfully deleted {delete_result.deleted_count} articles")
            
            # Get updated statistics
            total_remaining = self.db_manager.get_article_count()
            
            return {
                "success": True,
                "deleted_count": delete_result.deleted_count,
                "total_remaining": total_remaining,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Deleted {delete_result.deleted_count} articles older than {months_old} months"
            }
            
        except Exception as e:
            logger.error(f"Error during purge operation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self.db_manager.disconnect()
    
    def get_database_stats(self) -> dict:
        """Get statistics about the database."""
        try:
            if not self.db_manager.connect():
                return {"error": "Database connection failed"}
            
            # Total count
            total_count = self.db_manager.get_article_count()
            
            # Count by time periods
            now = datetime.utcnow()
            
            # Last 7 days
            week_ago = now - timedelta(days=7)
            last_week_count = self.db_manager.collection.count_documents(
                {"scraped_at": {"$gte": week_ago}}
            )
            
            # Last 30 days
            month_ago = now - timedelta(days=30)
            last_month_count = self.db_manager.collection.count_documents(
                {"scraped_at": {"$gte": month_ago}}
            )
            
            # Older than 2 months
            two_months_ago = now - timedelta(days=60)
            old_articles_count = self.db_manager.collection.count_documents(
                {"scraped_at": {"$lt": two_months_ago}}
            )
            
            # Sources breakdown
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            sources = list(self.db_manager.collection.aggregate(pipeline))
            
            return {
                "total_articles": total_count,
                "last_week": last_week_count,
                "last_month": last_month_count,
                "older_than_2_months": old_articles_count,
                "top_sources": sources,
                "database": self.config.MONGODB_DATABASE,
                "collection": self.config.MONGODB_COLLECTION
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
        finally:
            self.db_manager.disconnect()


def main():
    """Main function to run the cleanup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old articles from database")
    parser.add_argument(
        "--months", 
        type=int, 
        default=2, 
        help="Number of months back to keep articles (default: 2)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Only show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show database statistics"
    )
    
    args = parser.parse_args()
    
    cleaner = ArticleCleaner()
    
    if args.stats:
        logger.info("Getting database statistics...")
        stats = cleaner.get_database_stats()
        
        if "error" in stats:
            logger.error(f"Error getting stats: {stats['error']}")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        print(f"Total articles: {stats['total_articles']:,}")
        print(f"Last week: {stats['last_week']:,}")
        print(f"Last month: {stats['last_month']:,}")
        print(f"Older than 2 months: {stats['older_than_2_months']:,}")
        print(f"Database: {stats['database']}")
        print(f"Collection: {stats['collection']}")
        
        print(f"\nTop sources:")
        for source in stats['top_sources']:
            print(f"  {source['_id']}: {source['count']:,} articles")
        print("="*60)
        
    else:
        logger.info(f"Starting cleanup operation...")
        logger.info(f"Months to keep: {args.months}")
        logger.info(f"Dry run: {args.dry_run}")
        
        result = cleaner.purge_old_articles(
            months_old=args.months,
            dry_run=args.dry_run
        )
        
        if result["success"]:
            if args.dry_run:
                count = result.get('would_delete_count', result.get('deleted_count', 0))
                print(f"\n✅ DRY RUN: Would delete {count} articles")
            else:
                print(f"\n✅ SUCCESS: {result['message']}")
                if "total_remaining" in result:
                    print(f"📊 Total articles remaining: {result['total_remaining']:,}")
        else:
            print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
