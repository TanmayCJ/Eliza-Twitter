import sqlite3
import re
from typing import List, Dict

class HashtagGatherer:
    def __init__(self, db_path: str = "data/tweets.db"):
        self.db_path = db_path

    def _setup_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DROP TABLE IF EXISTS hashtags')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS hashtags (
                    hashtags TEXT,
                    text_without_hashtags TEXT,
                    likes INTEGER,
                    retweets INTEGER,
                    replies INTEGER,
                    quotes INTEGER
                )
            ''')

    def _extract_hashtags(self, text: str) -> Dict[str, str]:
        hashtags = re.findall(r"#(\w+)", text)
        text_without_hashtags = re.sub(r"#(\w+)", "", text)
        return {"hashtags": ",".join(hashtags), "text_without_hashtags": text_without_hashtags}

    def process(self):
        self._setup_db()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tweet, clean_text, likes, retweets, replies, quotes FROM tweets")
            rows = cursor.fetchall()

            for row in rows:
                result = self._extract_hashtags(row[0])
                cursor.execute('''
                    INSERT INTO hashtags (hashtags, text_without_hashtags, likes, retweets, replies, quotes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (result["hashtags"], row[1], row[2], row[3], row[4], row[5]))
            conn.commit()

if __name__ == "__main__":
    gatherer = HashtagGatherer(db_path="../data/all_tweets.db")
    gatherer.process() 