from scripts.sustainable_tweets.gather_sustainable_users import UserLoader
from scripts.sustainable_tweets.gather_sustainable_tweets import TweetGatherer
from scripts.sustainable_tweets.preprocess_sustainable_tweets import TweetPreprocessor

def main():
    # Load users
    print("👥 Starting to gather users...")
    user_loader = UserLoader(db_path="data/tweets.db", batch_size=10000, max_users=1000000)
    user_loader.process()
    print("👥 User gathering completed.")

    # Gather tweets
    print("🐦 Starting to gather tweets...")
    tweet_gatherer = TweetGatherer(db_path="data/tweets.db", batch_size=10000, max_tweets=None)
    tweet_gatherer.process()
    print("🐦 Tweet gathering completed.")

    # Preprocess tweets
    print("🧹 Starting to preprocess tweets...")
    tweet_preprocessor = TweetPreprocessor(db_path="data/tweets.db")
    tweet_preprocessor.process()
    print("🧹 Tweet preprocessing completed.")

if __name__ == "__main__":
    main()