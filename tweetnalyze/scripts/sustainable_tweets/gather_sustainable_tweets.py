# scripts/gather_tweets.py
import sys
import os
import re
import sqlite3
from typing import List, Optional
from datasets import load_dataset


class TweetGatherer:
    def __init__(self, db_path: str = "data/tweets.db", batch_size: int = 10000, max_tweets: Optional[int] = None):
        self.db_path = db_path
        self.batch_size = batch_size
        self.max_tweets = max_tweets
        self.total_checked = 0
        self.total_matched = 0
        self.regex = self._compile_keywords()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _compile_keywords(self) -> re.Pattern:
        """
        Compiles a list of sustainability, climate, and AI-related keywords into a single regular expression.
        The regex uses word boundaries to match whole words/phrases only.

        Returns:
            re.Pattern: A compiled regex pattern (case-insensitive) for detecting if any of the keywords
                        appear in a tweet.
        """
        keywords = [
            "carbon", "carbon footprint", "carbon neutral", "carbon offset", 
            "carbon dioxide", "CO2", "CO2 emissions", "emissions", "net zero", 
            "greenhouse gas", "greenhouse gases", "sustainability", "sustainable", 
            "environmental impact", "eco-friendly", "climate change", "climate crisis", 
            "global warming", "green energy", "renewable energy", "green tech", 
            "circular economy", "low carbon", "decarbonization", "AI for good", 
            "AI sustainability", "green AI", "AI climate", "ML for sustainability", 
            "AI carbon tracking", "AI carbon monitoring", "climate AI", 
            "carbon analytics", "carbon prediction", "smart grid", "energy optimization", 
            "renewables", "solar energy", "wind energy", "hydropower", 
            "energy efficiency", "energy saving", "electric vehicle", "EV", 
            "clean energy", "sustainable energy", "zero emissions"
        ]
        pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
        return re.compile(pattern, re.IGNORECASE)


    def _setup_db(self):
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
        self._setup_db()
        print("🛰️  Streaming tweets...")
        tweet_stream = load_dataset("enryu43/twitter100m_tweets", split="train", streaming=True)
        batch = []
        for tweet in tweet_stream:
            if self.max_tweets is not None and self.total_checked >= self.max_tweets:
                break

            self.total_checked += 1

            if "tweet" in tweet and self.regex.search(tweet["tweet"]):
                batch.append(tweet)
                self.total_matched += 1

            if self.total_checked % self.batch_size == 0:
                self._insert_batch(batch)
                print(f"✅ Checked: {self.total_checked:,} | Matched: {self.total_matched:,}")
                batch.clear()


        if batch:
            self._insert_batch(batch)
            print(f"✅ Checked: {self.total_checked:,} | Matched: {self.total_matched:,}")

    


if __name__ == "__main__":
    gatherer = TweetGatherer(db_path="../data/tweets.db", batch_size=10000, max_tweets=None)
    gatherer.process()
