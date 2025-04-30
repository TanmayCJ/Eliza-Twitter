from flask import Flask, request, jsonify
from datetime import datetime
from sqlalchemy.exc import ProgrammingError, OperationalError
from models import db, get_tweet_model, is_valid_sender, VALID_SENDERS, get_next_id
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Initialize database tables
    try:
        with app.app_context():
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully.")
            
            # Verify tables exist by querying table names
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                table_names = inspector.get_table_names()
                logger.info(f"Existing tables: {table_names}")
                
                # Check if our expected tables exist
                expected_tables = ['carbontruth_tweets', 'carbonrant_tweets', 'default_tweets']
                missing_tables = [table for table in expected_tables if table not in table_names]
                
                if missing_tables:
                    logger.warning(f"Missing tables: {missing_tables}. Attempting to create them...")
                    # Force table creation for specific models
                    for sender in VALID_SENDERS:
                        model = get_tweet_model(sender)
                        if model:
                            model.__table__.create(db.engine, checkfirst=True)
            except Exception as e:
                logger.error(f"Error verifying tables: {e}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        
    @app.route('/api/tweets', methods=['POST'])
    def create_tweet():
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        try:
            # Extract sender and tweetData from request
            sender = data.get('sender', 'default')
            tweet_data = data.get('tweetData')
            
            if not tweet_data:
                return jsonify({'error': 'No tweet data provided'}), 400
            
            # Validate sender
            if not is_valid_sender(sender):
                return jsonify({
                    'error': 'Invalid sender',
                    'valid_senders': VALID_SENDERS
                }), 400
                
            # Get appropriate tweet model based on sender
            TweetModel = get_tweet_model(sender)
            
            # Extract tweet data fields
            tweet_id = tweet_data.get('tweetID')
            date_str = tweet_data.get('date')
            time_str = tweet_data.get('time')
            content = tweet_data.get('content')
            tweet_link = tweet_data.get('tweetLnk', '')  # Extract the tweet link
            hashtags = tweet_data.get('hashtags', [])
            image_urls = tweet_data.get('imageUrl', [])
            
            # Validate required fields
            if not all([tweet_id, date_str, time_str, content]):
                return jsonify({'error': 'Missing required fields in tweetData'}), 400
                
            # Parse date and time
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                time = datetime.strptime(time_str, '%H:%M:%S').time()
            except ValueError as e:
                return jsonify({'error': f'Invalid date or time format: {str(e)}'}), 400
            
            # Ensure table exists before attempting to get next ID
            try:
                # Verify the table exists by checking metadata
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                table_name = TweetModel.__tablename__
                
                if table_name not in inspector.get_table_names():
                    logger.warning(f"Table {table_name} doesn't exist. Creating it now.")
                    # Create the specific table
                    TweetModel.__table__.create(db.engine, checkfirst=True)
                    logger.info(f"Table {table_name} created successfully.")
            except Exception as e:
                logger.error(f"Error checking/creating table {TweetModel.__tablename__}: {e}")
                return jsonify({'error': f'Error creating database table: {str(e)}'}), 500
            
            # Get next ID for this model
            next_id = get_next_id(TweetModel)
            
            # Create new tweet object with the appropriate model and set the ID
            tweet = TweetModel(
                id=next_id,
                tweet_id=tweet_id,
                date=date,
                time=time,
                content=content,
                tweet_link=tweet_link,  # Add the tweet link to the model
                hashtags=hashtags,
                image_urls=image_urls
            )
            
            # Save to database
            db.session.add(tweet)
            db.session.commit()
            
            return jsonify({
                'message': f'Tweet stored successfully in {sender} table',
                'tweet': tweet.to_dict()
            }), 201
            
        except (ProgrammingError, OperationalError) as e:
            db.session.rollback()
            logger.error(f"Database error: {e}")
            # Handle database connection/table not found errors
            try:
                with app.app_context():
                    # Get the model for this sender
                    TweetModel = get_tweet_model(sender)
                    # Create the specific table
                    TweetModel.__table__.create(db.engine, checkfirst=True)
                    logger.info(f"Created table {TweetModel.__tablename__} after error")
                return jsonify({'error': f'Database error: {str(e)}. Tables have been created, please try again.'}), 500
            except Exception as inner_e:
                logger.error(f"Failed to create tables after error: {inner_e}")
                return jsonify({'error': f'Critical database error: {str(inner_e)}'}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tweets', methods=['GET'])
    def get_tweets():
        # Get sender parameter
        sender = request.args.get('sender', 'default')
        
        # Validate sender
        if not is_valid_sender(sender):
            return jsonify({
                'error': 'Invalid sender',
                'valid_senders': VALID_SENDERS
            }), 400
        
        try:
            TweetModel = get_tweet_model(sender)
            tweets = TweetModel.query.all()
            return jsonify([tweet.to_dict() for tweet in tweets])
        except (ProgrammingError, OperationalError):
            # Handle case where table doesn't exist yet
            with app.app_context():
                db.create_all()  # Create tables if they don't exist
            return jsonify([])  # Return empty list since the table was just created
    
    @app.route('/api/tweets/<tweet_id>', methods=['GET'])
    def get_tweet(tweet_id):
        # Get sender parameter
        sender = request.args.get('sender', 'default')
        
        # Validate sender
        if not is_valid_sender(sender):
            return jsonify({
                'error': 'Invalid sender',
                'valid_senders': VALID_SENDERS
            }), 400
        
        try:
            TweetModel = get_tweet_model(sender)
            tweet = TweetModel.query.filter_by(tweet_id=tweet_id).first()
            
            if not tweet:
                return jsonify({'error': 'Tweet not found'}), 404
                
            return jsonify(tweet.to_dict())
        except (ProgrammingError, OperationalError):
            # Handle case where table doesn't exist yet
            with app.app_context():
                db.create_all()  # Create tables if they don't exist
            return jsonify({'error': 'Tweet not found'}), 404
    
    @app.route('/api/tweets/latest', methods=['GET'])
    def get_latest_tweet():
        # Get sender parameter
        sender = request.args.get('sender', 'default')
        
        # Validate sender
        if not is_valid_sender(sender):
            return jsonify({
                'error': 'Invalid sender',
                'valid_senders': VALID_SENDERS
            }), 400
        
        try:
            TweetModel = get_tweet_model(sender)
            
            # Ensure table exists before querying it
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                table_name = TweetModel.__tablename__
                
                if table_name not in inspector.get_table_names():
                    logger.warning(f"Table {table_name} doesn't exist. Creating it now.")
                    # Create the specific table
                    TweetModel.__table__.create(db.engine, checkfirst=True)
                    logger.info(f"Table {table_name} created successfully.")
                    # If we just created the table, there are no tweets
                    return jsonify({'message': f'No tweets found for sender: {sender} (table was just created)'}), 404
            except Exception as e:
                logger.error(f"Error checking/creating table {TweetModel.__tablename__}: {e}")
                return jsonify({'error': f'Error accessing database: {str(e)}'}), 500
                
            # Get the latest tweet ordered by id in descending order
            latest_tweet = TweetModel.query.order_by(TweetModel.id.desc()).first()
            
            if not latest_tweet:
                return jsonify({'error': f'No tweets found for sender: {sender}'}), 404
                
            return jsonify({
                'message': f'Latest tweet from {sender}',
                'tweet': latest_tweet.to_dict()
            }), 200
            
        except (ProgrammingError, OperationalError) as e:
            logger.error(f"Database error in get_latest_tweet: {e}")
            # Handle case where table doesn't exist yet
            try:
                with app.app_context():
                    # Get the model for this sender
                    TweetModel = get_tweet_model(sender)
                    # Create the specific table
                    TweetModel.__table__.create(db.engine, checkfirst=True)
                    logger.info(f"Created table {TweetModel.__tablename__} after error")
                return jsonify({'error': f'Database error: {str(e)}. Tables have been created, please try again.'}), 500
            except Exception as inner_e:
                logger.error(f"Failed to create tables after error: {inner_e}")
                return jsonify({'error': f'Critical database error: {str(inner_e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in get_latest_tweet: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tweets/latest_n', methods=['GET'])
    def get_latest_n_tweets():
        # Get sender and count parameters
        sender = request.args.get('sender', 'default')
        count = request.args.get('count', 5)  # Default to 5 tweets if count is not provided
        
        # Validate sender
        if not is_valid_sender(sender):
            return jsonify({
                'error': 'Invalid sender',
                'valid_senders': VALID_SENDERS
            }), 400
        
        try:
            count = int(count)
            if count <= 0:
                return jsonify({'error': 'Count must be a positive integer'}), 400
        except ValueError:
            return jsonify({'error': 'Count must be an integer'}), 400
        
        try:
            TweetModel = get_tweet_model(sender)
            
            # Ensure table exists before querying it
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                table_name = TweetModel.__tablename__
                
                if table_name not in inspector.get_table_names():
                    logger.warning(f"Table {table_name} doesn't exist. Creating it now.")
                    # Create the specific table
                    TweetModel.__table__.create(db.engine, checkfirst=True)
                    logger.info(f"Table {table_name} created successfully.")
                    # If we just created the table, there are no tweets
                    return jsonify({'message': f'No tweets found for sender: {sender} (table was just created)'}), 404
            except Exception as e:
                logger.error(f"Error checking/creating table {TweetModel.__tablename__}: {e}")
                return jsonify({'error': f'Error accessing database: {str(e)}'}), 500
                
            # Get the latest 'n' tweets ordered by id in descending order
            latest_tweets = TweetModel.query.order_by(TweetModel.id.desc()).limit(count).all()
            
            if not latest_tweets:
                return jsonify({'error': f'No tweets found for sender: {sender}'}), 404
                
            return jsonify({
                'tweets': [tweet.content for tweet in latest_tweets]  # Return only the content of the tweets
            }), 200
            
        except (ProgrammingError, OperationalError) as e:
            logger.error(f"Database error in get_latest_n_tweets: {e}")
            # Handle case where table doesn't exist yet
            try:
                with app.app_context():
                    # Get the model for this sender
                    TweetModel = get_tweet_model(sender)
                    # Create the specific table
                    TweetModel.__table__.create(db.engine, checkfirst=True)
                    logger.info(f"Created table {TweetModel.__tablename__} after error")
                return jsonify({'error': f'Database error: {str(e)}. Tables have been created, please try again.'}), 500
            except Exception as inner_e:
                logger.error(f"Failed to create tables after error: {inner_e}")
                return jsonify({'error': f'Critical database error: {str(inner_e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in get_latest_n_tweets: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/senders', methods=['GET'])
    def get_valid_senders():
        """Return a list of valid senders"""
        return jsonify({'valid_senders': VALID_SENDERS})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)