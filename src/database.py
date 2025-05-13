import os
import logging
from pymongo import MongoClient, UpdateOne
from pymongo.errors import DuplicateKeyError, OperationFailure
from .params import MONGO_HOST, MONGO_POST


logger = logging.getLogger(__name__)


class MongoDBDatabase:
    def __init__(
        self,
        host: str = MONGO_HOST,
        database: str = "CV_RESUME",
        port: int = MONGO_POST,
        debug: bool = False,
    ):
        """Initialize the MongoDBDatabase class with the connection parameters"""
        self.host = host
        self.database = database
        self.port = port
        self.debug = debug
        self.client = None
        self.db = None

    def create_connection(self):
        """Create and return a MongoDB database connection"""
        try:
            self.client = MongoClient(f"mongodb://{self.host}:{self.port}/")
            self.db = self.client[self.database]
            logger.info(
                f"Successfully connected to the MongoDB database {self.database} on port {self.port}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
        return self.client

    def insert_data(self, collection: str, data: dict):
        """Insert a document into the specified collection"""
        if self.db is None:
            logger.error("No active database connection.")
            return

        try:
            collection_obj = self.db[collection]
            inserted = collection_obj.insert_one(data)
            logger.info(f"Document inserted with _id: {inserted.inserted_id}")
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error: {e}")
        except Exception as e:
            logger.error(f"Error inserting data into {collection}: {e}")

    def select_data(self, collection: str, query: dict = {}, projection: dict = None):
        """
        Select data using a query and return the result
        """
        if self.db is None:
            logger.error("No active database connection.")
            return None

        try:
            collection_obj = self.db[collection]
            result = collection_obj.find(query, projection)
            return list(result)
        except Exception as e:
            logger.error(f"Error querying data from {collection}: {e}")
            return None

    def update_data(self, collection: str, query: dict, update: dict):
        """
        Update data in the specified collection based on the query
        """
        if self.db is None:
            logger.error("No active database connection.")
            return

        try:
            collection_obj = self.db[collection]
            result = collection_obj.update_many(query, {"$set": update})
            logger.info(f"Updated {result.modified_count} documents in {collection}.")
        except OperationFailure as e:
            logger.error(f"Error updating data in {collection}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def delete_data(self, collection: str, query: dict):
        """
        Delete data from the specified collection based on the query
        """
        if self.db is None:
            logger.error("No active database connection.")
            return

        try:
            collection_obj = self.db[collection]
            result = collection_obj.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} documents from {collection}.")
        except Exception as e:
            logger.error(f"Error deleting data from {collection}: {e}")

    def close_connection(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")


if __name__ == "__main__":
    # Initialize the MongoDB database connection
    db = MongoDBDatabase(
        host="localhost",
        database="CV_RESUME",
        port=27017,
        debug=True,
    )

    # Create connection
    client = db.create_connection()

    if client:
        # Insert data
        data_to_insert = {
            "resume_id": "12345",
            "name": "John Doe",
            "created_at": "2025-05-13",
        }
        db.insert_data("resume", data_to_insert)

        # Select data
        query = {"resume_id": "12345"}
        result = db.select_data("resume", query)
        logger.info(f"Query result: {result}")

        # Update data
        update_data = {"name": "John Smith"}
        db.update_data("resume", {"resume_id": "12345"}, update_data)

        # Delete data
        db.delete_data("resume", {"resume_id": "12345"})

        # Close connection
        db.close_connection()
