# scripts/gather_all_tweets.py
import sys
import os
import sqlite3
from typing import List, Optional
from datasets import load_dataset


class AllTweetGatherer:
    def __init__(self, db_path: str = "data/all_tweets.db", batch_size: int = 10000, max_tweets: Optional[int] = None):
        self.db_path = db_path
        self.batch_size = batch_size
        self.max_tweets = max_tweets
        self.total_processed = 0
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _setup_db(self):
        """
        Creates the tweets table in the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tweets (
                    id TEXT PRIMARY KEY,
                    user TEXT,
                    tweet TEXT,
                    likes INTEGER,
                    retweets INTEGER,
                    replies INTEGER,
                    quotes INTEGER
                )
            ''')

    def _insert_batch(self, batch: List[dict]):
        """
        Inserts a batch of tweets into the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            for tweet in batch:
                conn.execute('''
                    INSERT OR IGNORE INTO tweets (id, user, tweet, likes, retweets, replies, quotes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tweet.get("id"), tweet.get("user"), tweet.get("tweet"),
                    tweet.get("likes", 0), tweet.get("retweets", 0),
                    tweet.get("replies", 0), tweet.get("quotes", 0)
                ))
            conn.commit()

    def process(self):
        """
        Main processing logic to stream and store all tweets.
        """
        self._setup_db()
        print("🛰️  Streaming all tweets...")
        tweet_stream = load_dataset("enryu43/twitter100m_tweets", split="train", streaming=True)
        
        batch = []
        for tweet in tweet_stream:
            if self.max_tweets is not None and self.total_processed >= self.max_tweets:
                break

            self.total_processed += 1
            batch.append(tweet)

            if self.total_processed % self.batch_size == 0:
                self._insert_batch(batch)
                print(f"✅ Processed: {self.total_processed:,} tweets")
                batch.clear()

        if batch:
            self._insert_batch(batch)
            print(f"✅ Processed: {self.total_processed:,} tweets")

        print("🏁 Done gathering all tweets.")


if __name__ == "__main__":
    gatherer = AllTweetGatherer(db_path="../data/all_tweets.db", batch_size=10000, max_tweets=None)
    gatherer.process()