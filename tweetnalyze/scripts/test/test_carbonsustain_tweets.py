import sqlite3
import requests
import json
from typing import Dict, List, Tuple
import time

def get_tweets_from_db(db_path: str) -> List[Tuple]:
    """Fetch all tweets from the source database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Assuming the table has a 'text' and 'likes' column
    cursor.execute("SELECT text, like_count FROM app_tweet")
    tweets = cursor.fetchall()
    
    conn.close()
    return tweets

def get_popularity_score(text: str) -> float:
    """Get popularity score from the API endpoint."""
    url = "http://127.0.0.1:8000/api/popularity/"
    payload = {"text": text}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('predicted_score', 0.0)
    except requests.exceptions.RequestException as e:
        print(f"Error getting popularity score: {e}")
        return 0.0

def get_safety_score(text: str) -> float:
    """Get safety score from the API endpoint."""
    url = "http://127.0.0.1:8000/api/safety/"
    payload = {"text": text}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('is_appropriate', 0.0)
    except requests.exceptions.RequestException as e:
        print(f"Error getting safety score: {e}")
        return 0.0

def create_results_db(db_path: str):
    """Create the results database with required schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tweet_results (
        text TEXT,
        likes INTEGER,
        popularity_score REAL,
        safety_score REAL
    )
    """)
    
    conn.commit()
    conn.close()

def store_results(db_path: str, results: List[Dict]):
    """Store the results in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for result in results:
        cursor.execute("""
        INSERT INTO tweet_results (text, likes, popularity_score, safety_score)
        VALUES (?, ?, ?, ?)
        """, (result['text'], result['likes'], result['popularity_score'], result['safety_score']))
    
    conn.commit()
    conn.close()

def process_tweets(source_db: str, target_db: str):
    """Main function to process all tweets and store results."""
    # Create the results database
    create_results_db(target_db)
    
    # Get all tweets
    tweets = get_tweets_from_db(source_db)
    results = []
    
    print(f"Processing {len(tweets)} tweets...")
    
    for i, (tweet_text, likes) in enumerate(tweets, 1):
        print(f"Processing tweet {i}/{len(tweets)}")
        
        # Get scores from APIs
        popularity_score = get_popularity_score(tweet_text)
        safety_score = get_safety_score(tweet_text)
        
        results.append({
            'text': tweet_text,
            'likes': likes,
            'popularity_score': popularity_score,
            'safety_score': safety_score
        })
        
        # Add a small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    # Store results
    store_results(target_db, results)
    print("Processing complete!")

if __name__ == "__main__":
    source_db = "../../data/carbon_sustain_tweets_impression.sqlite3"
    target_db = "../../data/test.db"
    process_tweets(source_db, target_db)