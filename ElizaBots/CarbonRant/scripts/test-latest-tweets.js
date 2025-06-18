// test-latest-tweets.js
// A script to test the latest tweets API integration

const { fetchLatestTweetsFromEliza } = require('../packages/client-twitter/src/latest_tweet.ts');

// Run the test
async function testLatestTweets() {
  console.log("Testing Latest Tweets API...\n");
  
  try {
    // Test with environment variable
    process.env.ELIZA_LATEST_TWEETS_API = "http://127.0.0.1:8000/api/tweets/latest/?sender=carbontruth";
    process.env.ELIZA_LATEST_TWEETS_VERBOSE_OUTPUT = "true";
    
    console.log(`API URL: ${process.env.ELIZA_LATEST_TWEETS_API}`);
    console.log("Fetching tweets...");
    
    const response = await fetchLatestTweetsFromEliza();
    
    console.log("API Response:", JSON.stringify(response, null, 2));
    
    // Check if we need to handle both single objects and arrays
    let tweets = response;
    if (!Array.isArray(response) && response) {
      tweets = [response]; // Convert single object to array for consistency
      console.log("Converted single tweet object to array for processing");
    }
    
    if (!tweets) {
      console.log("No tweets returned or API call failed\n");
    } else if (Array.isArray(tweets) && tweets.length === 0) {
      console.log("API returned an empty array");
    } else if (Array.isArray(tweets)) {
      console.log(`Processing ${tweets.length} tweets`);
      
      // Format tweets for the template
      const formattedTweets = tweets.map(tweet => ({
        text: tweet.content || tweet.text,
        created_at: tweet.created_at,
        id: tweet.tweet_id || tweet.id,
        author_id: tweet.author_id || "unknown",
        username: tweet.username || "CarbonTruths",
      }));
      
      console.log("\nFormatted tweets for template:");
      console.log(JSON.stringify(formattedTweets, null, 2));
      
      // This is how it would be used in the template context
      console.log("\nTemplate usage example:");
      formattedTweets.forEach((tweet, i) => {
        console.log(`Tweet ${i+1}: ${tweet.text.substring(0, 50)}...`);
      });
    }
  } catch (error) {
    console.error("Error testing latest tweets:", error);
  }
  
  console.log("\nTest complete!");
}

testLatestTweets().catch(console.error);
