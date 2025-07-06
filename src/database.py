"""Database operations for MongoDB."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config.settings import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB operations for article storage."""
    
    def __init__(self, uri: str = None, database: str = None, collection: str = None):
        """Initialize database connection."""
        self.uri = uri or Config.MONGODB_URI
        self.database_name = database or Config.MONGODB_DATABASE
        self.collection_name = collection or Config.MONGODB_COLLECTION
        self.client: Optional[MongoClient] = None
        self.database = None
        self.collection = None
        
    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ismaster')
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.database_name}")
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def save_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """Save articles to MongoDB."""
        if self.collection is None:
            logger.error("No database connection available")
            return False
        
        try:
            # Add metadata to each article
            for article in articles:
                article['scraped_at'] = datetime.utcnow()
                article['_id'] = f"{article['url']}_{article['scraped_at'].strftime('%Y%m%d')}"
            
            # Use upsert to avoid duplicates
            operations = []
            for article in articles:
                operations.append({
                    'updateOne': {
                        'filter': {'url': article['url']},
                        'update': {'$set': article},
                        'upsert': True
                    }
                })
            
            if operations:
                result = self.collection.bulk_write(operations)
                logger.info(
                    f"Saved {result.upserted_count} new articles, "
                    f"updated {result.modified_count} existing articles"
                )
                return True
            else:
                logger.warning("No articles to save")
                return False
                
        except OperationFailure as e:
            logger.error(f"MongoDB operation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving articles: {e}")
            return False
    
    def get_recent_articles(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent articles from the database."""
        if self.collection is None:
            logger.error("No database connection available")
            return []
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cursor = self.collection.find(
                {'scraped_at': {'$gte': cutoff_date}}
            ).sort('scraped_at', -1).limit(limit)
            
            articles = list(cursor)
            logger.info(f"Retrieved {len(articles)} recent articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {e}")
            return []
    
    def get_article_count(self) -> int:
        """Get total count of articles in the database."""
        if self.collection is None:
            return 0
        
        try:
            count = self.collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error counting articles: {e}")
            return 0
    
    def create_indexes(self):
        """Create database indexes for better performance."""
        if self.collection is None:
            logger.error("No database connection available")
            return
        
        try:
            # Create indexes
            self.collection.create_index("url", unique=True)
            self.collection.create_index("scraped_at")
            self.collection.create_index("source")
            self.collection.create_index("published")
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
