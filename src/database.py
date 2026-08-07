"""Database operations for MongoDB."""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
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
            logger.info(
                f"Database: {self.database_name}, Collection: {self.collection_name}"
            )

            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=10000,  # Increased timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
            )

            # Test the connection
            logger.info("Testing MongoDB connection...")
            self.client.admin.command("ismaster")

            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]

            # Verify collection access
            logger.info("Verifying collection access...")
            self.collection.count_documents({})

            logger.info(
                f"✅ Successfully connected to MongoDB: {self.database_name}.{self.collection_name}"
            )
            return True

        except ConnectionFailure:
            logger.error("❌ Failed to connect to MongoDB: Connection error")
            logger.error("Check MongoDB URI, network connectivity, and authentication")
            return False
        except Exception as e:
            logger.error(
                f"❌ Unexpected error connecting to MongoDB: {type(e).__name__}"
            )
            logger.error("Verify MongoDB configuration and network access")
            return False

    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def save_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """Save articles to MongoDB, upserting on URL."""
        if self.collection is None:
            logger.error("❌ No database connection available")
            return False

        logger.info(f"📝 Saving {len(articles)} articles to MongoDB...")

        # Stored as a BSON date (not an ISO string) so date-range queries
        # like cleanup and get_recent_articles actually match.
        scraped_at = datetime.now(timezone.utc)
        success_count = 0
        error_count = 0

        for article in articles:
            url = str(article.get("url", ""))
            if not url:
                logger.warning("Skipping article without URL")
                continue

            document = dict(article)
            document["scraped_at"] = scraped_at
            if not isinstance(document.get("tags"), list):
                document["tags"] = []
            if not document.get("published"):
                document["published"] = scraped_at.isoformat()

            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
            try:
                # Upsert on URL so re-scraping the same article updates the
                # existing document instead of accumulating daily duplicates.
                self.collection.update_one(
                    {"url": url},
                    {"$set": document, "$setOnInsert": {"_id": url_hash}},
                    upsert=True,
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.warning(
                    f"⚠️ Failed to save article {url}: {type(e).__name__} - {str(e)}"
                )

        logger.info(
            f"✅ Database operations completed: {success_count} successful, {error_count} failed"
        )
        return success_count > 0

    def get_recent_articles(
        self, days: int = 7, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve recent articles from the database."""
        if self.collection is None:
            logger.error("No database connection available")
            return []

        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            # scraped_at is a BSON date, but documents written by older
            # versions stored it as a naive ISO string — match both types.
            query = {
                "$or": [
                    {"scraped_at": {"$gte": cutoff_date}},
                    {
                        "scraped_at": {
                            "$gte": cutoff_date.replace(tzinfo=None).isoformat()
                        }
                    },
                ]
            }
            cursor = self.collection.find(query).sort("scraped_at", -1).limit(limit)

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
