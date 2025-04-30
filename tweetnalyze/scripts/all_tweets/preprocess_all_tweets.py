import re
import sqlite3
import time
from typing import List, Tuple
from datetime import datetime, timedelta
import atexit
import os
import signal
import sys
import json
from pathlib import Path


def _process_chunk(chunk: List[Tuple]) -> List[Tuple]:
    """
    Process a chunk of tweets sequentially
    """
    results = []
    for row in chunk:
        tweet_id, text, likes, retweets, replies, quotes = row
        # Clean the text
        clean_text = str(text)
        clean_text = re.sub(r"http\S+|www\S+", "", clean_text)
        clean_text = re.sub(r"@\w+", "", clean_text)
        clean_text = re.sub(r"\n", " ", clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        # Extract hashtags
        hashtags = re.findall(r"#(\w+)", text)
        text_without_hashtags = re.sub(r"#(\w+)", "", clean_text)
        results.append((
            tweet_id,
            clean_text,
            tweet_id,
            ",".join(hashtags),
            text_without_hashtags,
            likes, retweets, replies, quotes
        ))
    return results


class AllTweetPreprocessorAndHashtags:
    def __init__(self, db_path: str = "data/all_tweets.db", batch_size: int = 50000):
        self.db_path = db_path
        self.batch_size = batch_size
        self.start_time = None
        self.last_progress_time = None
        self.conn = None
        self.checkpoint_file = Path(db_path).parent / "preprocessing_checkpoint.json"
        atexit.register(self.cleanup)

    def cleanup(self):
        """Clean up database connections"""
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
                print("\n🧹 Cleaned up database connection.")
            except:
                pass

    def _execute_with_retry(self, cursor, sql, params=None, max_retries=5, delay=1):
        for attempt in range(max_retries):
            try:
                return cursor.execute(sql, params or ())
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                    continue
                raise

    def _setup_tables(self, conn):
        print("🔧 Setting up tables and optimizations...")
        cursor = conn.cursor()
        # Performance optimizations
        self._execute_with_retry(cursor, "PRAGMA journal_mode=WAL")
        self._execute_with_retry(cursor, "PRAGMA synchronous=NORMAL")
        self._execute_with_retry(cursor, "PRAGMA cache_size=-2000000")
        self._execute_with_retry(cursor, "PRAGMA temp_store=MEMORY")
        # Add clean_text column if missing
        cursor.execute("PRAGMA table_info(tweets)")
        cols = [c[1] for c in cursor.fetchall()]
        if "clean_text" not in cols:
            self._execute_with_retry(cursor, "ALTER TABLE tweets ADD COLUMN clean_text TEXT")
        # Create hashtags table
        self._execute_with_retry(cursor, '''
            CREATE TABLE IF NOT EXISTS hashtags (
                tweet_id TEXT PRIMARY KEY,
                hashtags TEXT,
                text_without_hashtags TEXT,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                quotes INTEGER
            )
        ''')
        self._execute_with_retry(cursor, 'CREATE INDEX IF NOT EXISTS idx_tweets_id ON tweets(id)')
        conn.commit()
        print("✅ Table setup complete!")

    def _print_progress_stats(self, conn, total_processed: int, total_count: int):
        current_time = time.time()
        progress = (total_processed / total_count) * 100
        elapsed = current_time - self.start_time
        if total_processed > 0:
            avg_speed = total_processed / elapsed
            rem = total_count - total_processed
            eta_time = datetime.now() + timedelta(seconds=rem / avg_speed)
            cursor = conn.cursor()
            self._execute_with_retry(cursor, """
                SELECT COUNT(*) as total_hashtags,
                       SUM(CASE WHEN hashtags != '' THEN 1 ELSE 0 END) as tweets_with_hashtags
                FROM hashtags
            """)
            total_hashtags, with_tags = cursor.fetchone()
            print(f"\nProcessed {total_processed}/{total_count} tweets ({progress:.1f}%)")
            print(f"Speed: {avg_speed:.1f} tweets/s, Elapsed: {timedelta(seconds=int(elapsed))}")
            print(f"ETA: {eta_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Tweets with hashtags: {with_tags}/{total_processed} ({with_tags/total_processed*100:.1f}%)\n")
            self.last_progress_time = current_time

    def _save_checkpoint(self, total_processed: int, last_tweet_id: str = None):
        checkpoint = {"total_processed": total_processed, "last_tweet_id": last_tweet_id, "timestamp": datetime.now().isoformat()}
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.checkpoint_file.with_suffix('.tmp')
        with open(tmp, 'w') as f:
            json.dump(checkpoint, f)
        tmp.replace(self.checkpoint_file)
        print(f"💾 Saved checkpoint: {total_processed} tweets processed")

    def _load_checkpoint(self) -> Tuple[int, str]:
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file) as f:
                    cp = json.load(f)
                print(f"📋 Resuming from checkpoint at {cp['timestamp']}")
                return cp.get('total_processed', 0), cp.get('last_tweet_id')
            except:
                print("⚠️  Invalid checkpoint, restarting.")
        return 0, None

    def process(self):
        """Sequentially process all tweets"""
        print("📁 Connecting to database...")
        for i in range(5):
            try:
                self.conn = sqlite3.connect(self.db_path, timeout=60.0)
                break
            except sqlite3.OperationalError:
                time.sleep(i+1)
        print("✅ Connected!")
        processed, last_id = self._load_checkpoint()
        self.start_time = time.time()
        self.last_progress_time = self.start_time

        with self.conn:
            self._setup_tables(self.conn)
            cur = self.conn.cursor()
            total = cur.execute("SELECT COUNT(*) FROM tweets").fetchone()[0]
            print(f"Total tweets: {total}")
            if total == 0:
                print("No tweets to process.")
                return

            while True:
                if last_id:
                    cur.execute(
                        "SELECT t.id, t.tweet, t.likes, t.retweets, t.replies, t.quotes "
                        "FROM tweets t LEFT JOIN hashtags h ON t.id = h.tweet_id "
                        "WHERE (t.clean_text IS NULL OR h.tweet_id IS NULL) AND t.id > ? "
                        "ORDER BY t.id LIMIT ?", (last_id, self.batch_size))
                else:
                    cur.execute(
                        "SELECT t.id, t.tweet, t.likes, t.retweets, t.replies, t.quotes "
                        "FROM tweets t LEFT JOIN hashtags h ON t.id = h.tweet_id "
                        "WHERE t.clean_text IS NULL OR h.tweet_id IS NULL "
                        "ORDER BY t.id LIMIT ?", (self.batch_size,))
                rows = cur.fetchall()
                if not rows:
                    break
                last_id = rows[-1][0]
                results = _process_chunk(rows)
                cur.execute("BEGIN TRANSACTION")
                try:
                    for r in results:
                        cur.execute("UPDATE tweets SET clean_text = ? WHERE id = ?", (r[1], r[0]))
                        cur.execute(
                            "INSERT OR REPLACE INTO hashtags"
                            " (tweet_id, hashtags, text_without_hashtags, likes, retweets, replies, quotes)"
                            " VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (r[2], r[3], r[4], r[5], r[6], r[7], r[8])
                        )
                    self.conn.commit()
                    processed += len(rows)
                    self._save_checkpoint(processed, last_id)
                except Exception:
                    self.conn.rollback()
                    raise
                now = time.time()
                if now - self.last_progress_time >= 60:
                    self._print_progress_stats(self.conn, processed, total)
                else:
                    print(f"Processed {processed}/{total} tweets")

            self._print_progress_stats(self.conn, processed, total)
            print("🏁 Processing complete.")
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()


if __name__ == "__main__":
    print("⚠️  Close other DB connections before running.")
    processor = AllTweetPreprocessorAndHashtags(db_path="../data/all_tweets.db", batch_size=50000)
    def handler(signum, frame):
        print("\n🛑 Interrupted. Cleaning up...")
        processor.cleanup()
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)
    try:
        processor.process()
    except Exception as e:
        print(f"❌ Error: {e}")
        processor.cleanup()
        raise
