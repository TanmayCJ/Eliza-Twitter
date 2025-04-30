import re
import sqlite3


class TweetPreprocessor:
    def __init__(self, db_path: str = "data/tweets.db"):
        self.db_path = db_path

    def _clean_text(self, text: str) -> str:
        """
        Cleans tweet text for transformer input:
        - Removes URLs
        - Removes @mentions
        - Replaces line breaks with space
        - Removes extra whitespace
        """
        text = str(text)
        text = re.sub(r"http\S+|www\S+", "", text)   # remove URLs
        text = re.sub(r"@\w+", "", text)             # remove @mentions
        text = re.sub(r"\n", " ", text)              # replace newlines with space
        text = re.sub(r'\s+', ' ', text).strip()     # collapse multiple spaces
        return text


    def process(self):
        """
        Loads tweets from the database, cleans them using `_clean_text`,
        and stores the cleaned text into a new `clean_text` column in the same table.
        """
        print("🧹 Starting tweet cleaning for transformers...")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Ensure clean_text column exists
            cursor.execute("PRAGMA table_info(tweets)")
            columns = [col[1] for col in cursor.fetchall()]
            if "clean_text" not in columns:
                cursor.execute("ALTER TABLE tweets ADD COLUMN clean_text TEXT")

            # Fetch all tweets
            cursor.execute("SELECT id, tweet FROM tweets")
            rows = cursor.fetchall()

            for tweet_id, text in rows:
                cleaned = self._clean_text(text)
                cursor.execute(
                    "UPDATE tweets SET clean_text = ? WHERE id = ?", (cleaned, tweet_id)
                )

            conn.commit()
            print(f"✅ Cleaned and updated {len(rows):,} tweets.")


if __name__ == "__main__":
    preprocessor = TweetPreprocessor()
    preprocessor.process()

