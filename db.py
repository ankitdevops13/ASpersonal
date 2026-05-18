import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Database:
    def __init__(self, database_url: str):
        try:
            self.client = MongoClient(database_url)
            # Extract database name from the URL or use a default
            # For mongodb+srv, the database name is often part of the path or specified in the connection string
            # For simplicity, let's assume the database name is the last part of the path or a default
            db_name = database_url.split('/')[-1].split('?')[0] if '/' in database_url else "your_bot_db"
            if not db_name or db_name.startswith('mongodb'): # Fallback if parsing fails
                db_name = "your_bot_db" # Default if not found in URL
            self.db = self.client[db_name]
            self.sudo_users_collection = self.db["sudo_users"]

            # Ensure unique index on user_id to prevent duplicates
            self.sudo_users_collection.create_index([("user_id", pymongo.ASCENDING)], unique=True)

            # Test connection
            self.client.admin.command('ping')
            logging.info(f"MongoDB database '{db_name}' connected successfully.")
        except ConnectionFailure as e:
            logging.error(f"Could not connect to MongoDB: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred during MongoDB initialization: {e}")
            raise

    def add_sudo_user(self, user_id: int, username: str = None) -> bool:
        """Adds a user to the sudo list."""
        try:
            user_data = {"user_id": user_id}
            if username:
                user_data["username"] = username
            self.sudo_users_collection.insert_one(user_data)
            logging.info(f"User {user_id} added to sudo list.")
            return True
        except DuplicateKeyError:
            logging.info(f"User {user_id} is already a sudo user.")
            return False
        except Exception as e:
            logging.error(f"Error adding sudo user {user_id}: {e}")
            return False

    def remove_sudo_user(self, user_id: int) -> bool:
        """Removes a user from the sudo list."""
        try:
            result = self.sudo_users_collection.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                logging.info(f"User {user_id} removed from sudo list.")
                return True
            logging.info(f"User {user_id} not found in sudo list.")
            return False
        except Exception as e:
            logging.error(f"Error removing sudo user {user_id}: {e}")
            return False

    def get_sudo_users(self) -> list[int]:
        """Returns a list of all sudo user IDs."""
        try:
            users = self.sudo_users_collection.find({}, {"user_id": 1, "_id": 0}) # Project only user_id
            return [user["user_id"] for user in users]
        except Exception as e:
            logging.error(f"Error getting sudo users: {e}")
            return []

    def is_sudo_user(self, user_id: int) -> bool:
        """Checks if a user is a sudo user."""
        try:
            return self.sudo_users_collection.find_one({"user_id": user_id}) is not None
        except Exception as e:
            logging.error(f"Error checking sudo status for user {user_id}: {e}")
            return False

# Global database instance (will be initialized in main.py)
db = None
