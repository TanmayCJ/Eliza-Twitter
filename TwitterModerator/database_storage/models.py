from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class BaseTweet:
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    content = db.Column(db.Text, nullable=False)
    tweet_link = db.Column(db.String(255), nullable=True)  # Added tweet link field
    hashtags = db.Column(ARRAY(db.String), nullable=True)
    image_urls = db.Column(ARRAY(db.String), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tweetID': self.tweet_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'time': self.time.strftime('%H:%M:%S'),
            'content': self.content,
            'tweetLnk': self.tweet_link,  # Added to the response
            'hashtags': self.hashtags,
            'imageUrl': self.image_urls,
            'created_at': self.created_at
        }

# Function to get next ID for a model
def get_next_id(model):
    """
    Gets the next ID for a model by checking the last ID and incrementing it.
    If no records exist, starts with 1.
    """
    last_record = db.session.query(model).order_by(model.id.desc()).first()
    if last_record:
        return last_record.id + 1
    return 1

class CarbonTruthTweet(db.Model, BaseTweet):
    __tablename__ = 'carbontruth_tweets'
    
    def __repr__(self):
        return f'<CarbonTruthTweet {self.tweet_id}>'

class DefaultTweet(db.Model, BaseTweet):
    __tablename__ = 'default_tweets'
    
    def __repr__(self):
        return f'<DefaultTweet {self.tweet_id}>'

# List of valid senders
VALID_SENDERS = ['carbontruth', 'default', 'carbonrant']

# Map of sender names to their respective table models
SENDER_TABLE_MAP = {
    'carbontruth': CarbonTruthTweet,
    'default': DefaultTweet
}

# Function to check if sender is valid
def is_valid_sender(sender):
    return sender.lower() in VALID_SENDERS

# Function to get the appropriate model based on sender
def get_tweet_model(sender):
    if not is_valid_sender(sender):
        return None
    return SENDER_TABLE_MAP.get(sender.lower())