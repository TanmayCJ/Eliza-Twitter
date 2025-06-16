import { elizaLogger } from "@elizaos/core";

/**
 * TweetChecker class for verifying the safety and predicting the popularity of tweets
 * using external API services.
 */
export class TweetChecker {
  private readonly safetyApiUrl: string;
  private readonly popularityApiUrl: string;
  private readonly acceptedPopularityScore: number;

  /**
   * Creates a new TweetChecker instance
   * @param safetyApiUrl URL for the safety check API, defaults to localhost
   * @param popularityApiUrl URL for the popularity prediction API, defaults to localhost
   * @param acceptedPopularityScore The threshold score for considering a tweet popular, defaults to 10
   */
  constructor(
    safetyApiUrl: string = 'http://127.0.0.1:8000/api/safety/',
    popularityApiUrl: string = 'http://127.0.0.1:8000/api/popularity/',
    acceptedPopularityScore: number = 10
  ) {
    this.safetyApiUrl = safetyApiUrl;
    this.popularityApiUrl = popularityApiUrl;
    this.acceptedPopularityScore = acceptedPopularityScore;
  }

  /**
   * Checks if a tweet is safe (doesn't contain inappropriate content)
   * @param tweetContent The content of the tweet to check
   * @returns A promise resolving to a boolean indicating if the tweet is appropriate
   */
  public async checkTweetSafety(tweetContent: string): Promise<boolean> {
    try {
      const response = await fetch(this.safetyApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: tweetContent }),
      });

      if (!response.ok) {
        throw new Error(`Safety check failed with status: ${response.status}`);
      }

      const data = await response.json();
      // API returns is_appropriate as a boolean
      return data.text_safety_score.is_appropriate === true;
    } catch (error) {
      console.error('Error checking tweet safety:', error);
      // Default to false (unsafe) if the check fails
      return false;
    }
  }

  /**
   * Gets the raw popularity score of a tweet
   * @param tweetContent The content of the tweet to analyze
   * @returns A promise resolving to a number representing the predicted popularity score
   */
  public async getTweetPopularityScore(tweetContent: string): Promise<number> {
    try {
      const response = await fetch(this.popularityApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: tweetContent }),
      });

      if (!response.ok) {
        throw new Error(`Popularity check failed with status: ${response.status}`);
      }

      const data = await response.json();
      if (typeof data.predicted_score !== 'number') {
        elizaLogger.warn(`Unexpected popularity score format: ${JSON.stringify(data)}`);
        return 0; // Default score if format is unexpected
      }
      return data.predicted_score;
    } catch (error) {
      elizaLogger.error('Error checking tweet popularity:', error);
      return 0; // Default to 0 if check fails
    }
  }

  /**
   * Checks if a tweet is predicted to be popular based on a threshold
   * @param tweetContent The content of the tweet to analyze
   * @returns A promise resolving to an object containing the boolean result and the popularity score
   */
  public async checkTweetPopularity(tweetContent: string): Promise<{isPopular: boolean, score: number}> {
    try {
        const popularityScore = await this.getTweetPopularityScore(tweetContent);
        elizaLogger.info("Popularity score:", String(popularityScore));
      return {
        isPopular: popularityScore > this.acceptedPopularityScore,
        score: popularityScore
      };
    } catch (error) {
      console.error('Error checking tweet popularity threshold:', error);
      throw error;
    }
  }
}