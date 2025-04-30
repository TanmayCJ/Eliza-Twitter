import sqlite3
from datetime import datetime
import json
from flask import Flask
from models import db, CarbonSustainAITweet
from config import Config  # Import Config, not app

def create_app():
    # Create the Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def migrate_tweets():
    app = create_app()  # Create the app here
    
    # Connect to the SQLite database
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tweets from app_tweet table
    cursor.execute('SELECT * FROM app_tweet')
    tweets = cursor.fetchall()
    
    # Initialize Flask app context
    with app.app_context():
        # Create the new table
        db.create_all()
        
        # Process each tweet
        for tweet in tweets:
            # Parse the created_at timestamp
            created_dt = datetime.strptime(tweet['created_at'], '%Y-%m-%d %H:%M:%S')
            
            # Process hashtags
            hashtags = []
            if tweet['hashtags']:
                try:
                    hashtags = json.loads(tweet['hashtags'])
                    # Extract just the tag names from the hashtag objects
                    if isinstance(hashtags[0], dict) and 'tag' in hashtags[0]:
                        hashtags = [h['tag'] for h in hashtags]
                except:
                    hashtags = tweet['hashtags'].split(',') if tweet['hashtags'] else []
            
            # Create new tweet object
            new_tweet = CarbonSustainAITweet(
                tweet_id=tweet['tweet_id'],
                date=created_dt.date(),
                time=created_dt.time(),
                content=tweet['text'],  # Map 'text' to 'content'
                tweet_link=f"https://twitter.com/i/web/status/{tweet['tweet_id']}",
                hashtags=hashtags,
                image_urls=None,
                created_at=created_dt
            )
            
            # Add to database
            db.session.add(new_tweet)
        
        # Commit all changes
        db.session.commit()
    
    # Close connection
    conn.close()
    print(f"Successfully migrated {len(tweets)} tweets to carbonsustainai_tweets table")

if __name__ == "__main__":
    migrate_tweets()