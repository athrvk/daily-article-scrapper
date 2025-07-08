"""Database operations for MongoDB."""

import hashlib
import logging
import traceback
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
            logger.info("🔌 Attempting to connect to MongoDB...")
            logger.info(f"Database: {self.database_name}, Collection: {self.collection_name}")
            
            self.client = MongoClient(
                self.uri, 
                serverSelectionTimeoutMS=10000,  # Increased timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test the connection
            logger.info("Testing MongoDB connection...")
            self.client.admin.command('ismaster')
            
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Verify collection access
            logger.info("Verifying collection access...")
            self.collection.count_documents({})
            
            logger.info(f"✅ Successfully connected to MongoDB: {self.database_name}.{self.collection_name}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: Connection error")
            logger.error("Check MongoDB URI, network connectivity, and authentication")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {type(e).__name__}")
            logger.error("Verify MongoDB configuration and network access")
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def _serialize_datetime_fields(self, article: Dict[str, Any]) -> None:
        """Serialize datetime objects to ISO format strings for MongoDB."""
        for key, value in article.items():
            if isinstance(value, datetime):
                article[key] = value.isoformat()
    
    def save_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """Save articles to MongoDB."""
        if self.collection is None:
            logger.error("❌ No database connection available")
            return False
        
        try:
            logger.info(f"📝 Preparing to save {len(articles)} articles to MongoDB...")
            
            # Process articles one by one for better error tracking
            processed_articles = []
            for i, article in enumerate(articles):
                try:
                    # Make a copy to avoid modifying original
                    processed_article = dict(article)
                    
                    # Add metadata
                    scraped_at = datetime.utcnow()
                    processed_article['scraped_at'] = scraped_at
                    
                    # Create safe ID
                    url = str(processed_article.get('url', ''))
                    if not url:
                        logger.warning(f"Article {i} has no URL, skipping")
                        continue
                    
                    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]
                    date_str = scraped_at.strftime('%Y%m%d')
                    processed_article['_id'] = f"{url_hash}_{date_str}"
                    
                    # Clean up data types
                    if 'tags' in processed_article and not isinstance(processed_article['tags'], list):
                        processed_article['tags'] = []
                    
                    if 'published' in processed_article and not processed_article['published']:
                        processed_article['published'] = scraped_at.isoformat()
                    
                    # Ensure all datetime objects are serialized for MongoDB
                    self._serialize_datetime_fields(processed_article)
                    
                    processed_articles.append(processed_article)
                    
                except Exception as e:
                    logger.error(f"Error processing article {i}: {type(e).__name__} - {str(e)}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_articles)} articles")
            
            if not processed_articles:
                logger.warning("⚠️ No valid articles to save")
                return False
            
            # Save articles one by one with graceful error handling
            success_count = 0
            error_count = 0
            
            for i, article in enumerate(processed_articles):
                try:
                    # Try to insert the article first
                    self.collection.insert_one(article)
                    success_count += 1
                    logger.debug(f"✅ Successfully inserted article {i+1}/{len(processed_articles)}")
                    
                except Exception as insert_error:
                    # If insert fails (likely duplicate), try upsert without _id field
                    try:
                        # Create a copy without the _id field for upsert
                        article_for_update = {k: v for k, v in article.items() if k != '_id'}
                        
                        result = self.collection.replace_one(
                            {'url': article['url']},
                            article_for_update,
                            upsert=True
                        )
                        if result.upserted_id:
                            success_count += 1
                            logger.debug(f"✅ Upserted article {i+1}/{len(processed_articles)} (new)")
                        elif result.modified_count > 0:
                            success_count += 1
                            logger.debug(f"✅ Updated article {i+1}/{len(processed_articles)} (existing)")
                        else:
                            logger.debug(f"ℹ️ Article {i+1}/{len(processed_articles)} unchanged")
                            success_count += 1  # Count as success since it exists
                            
                    except Exception as upsert_error:
                        error_count += 1
                        logger.warning(
                            f"⚠️ Failed to save article {i+1}/{len(processed_articles)}: "
                            f"{type(upsert_error).__name__} - {str(upsert_error)}"
                        )
                        logger.debug(f"Article URL: {article.get('url', 'N/A')}")
                        continue
            
            logger.info(f"✅ Database operations completed: {success_count} successful, {error_count} failed")
            
            # Return True if we saved at least some articles
            return success_count > 0
                
        except Exception as e:
            logger.error(f"❌ Unexpected error saving articles: {type(e).__name__} - {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            # Create indexes - make URL index unique but handle duplicates gracefully
            self.collection.create_index("url", unique=True, background=True)
            self.collection.create_index("scraped_at", background=True)
            self.collection.create_index("source", background=True)
            self.collection.create_index("published", background=True)
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {type(e).__name__}")
            # Don't fail if indexes already exist or have conflicts
            logger.info("Continuing without index creation...")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
