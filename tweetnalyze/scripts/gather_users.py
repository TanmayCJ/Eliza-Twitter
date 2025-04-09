# scripts/load_users.py

import os
import sqlite3
from datasets import load_dataset
from typing import Optional, List


class UserLoader:
    def __init__(self, db_path: str = "data/tweets.db", batch_size: int = 10000, max_users: Optional[int] = None):
        self.db_path = db_path
        self.batch_size = batch_size
        self.max_users = max_users
        self.total_inserted = 0

        # Ensure parent directory exists (like gather_tweets.py)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _setup_db(self):
        """
        Creates the 'users' table if it doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user TEXT PRIMARY KEY,
                    followers INTEGER
                )
            ''')

    def _insert_batch(self, batch: List[dict]):
        """
        Inserts a batch of user records into the 'users' table.
        """
        with sqlite3.connect(self.db_path) as conn:
            for user in batch:
                conn.execute('''
                    INSERT OR IGNORE INTO users (user, followers)
                    VALUES (?, ?)
                ''', (user["user"], user.get("followers", 0)))
            conn.commit()

    def process(self):
        """
        Main logic to stream user data, filter, and store in SQLite DB.
        """
        self._setup_db()
        print("👥 Streaming users...")

        user_stream = load_dataset("enryu43/twitter100m_users", split="train", streaming=True)

        batch = []
        for user in user_stream:
            if self.max_users and self.total_inserted >= self.max_users:
                break

            batch.append(user)
            self.total_inserted += 1

            if self.total_inserted % self.batch_size == 0:
                self._insert_batch(batch)
                print(f"✅ Inserted: {self.total_inserted:,} users")
                batch.clear()

        if batch:
            self._insert_batch(batch)
            print(f"✅ Inserted: {self.total_inserted:,} users")

        print("🏁 Done loading users.")


if __name__ == "__main__":
    loader = UserLoader(db_path="data/tweets.db", batch_size=10000, max_users=1000000)
    loader.process()
