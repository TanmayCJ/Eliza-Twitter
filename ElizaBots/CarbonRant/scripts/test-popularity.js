// test-popularity.js
// A script to test the tweet popularity checking functionality

const { checkTweetPopularity } = require('../packages/client-twitter/src/popularity.ts');

// Sample tweets to test
const sampleTweets = [
  "Climate change is real and we need to act now. #ClimateAction",
  "Just planted 50 trees in my community! Every small action counts. #Sustainability",
  "I'm bored today, whatever.",
  "Exciting news! Our renewable energy project just reached 1 million homes powered by solar. This is how we make a difference! #CleanEnergy #Sustainability"
];

// Run the test
async function testPopularity() {
  console.log("Testing Twitter popularity scores...\n");
  
  for (const tweet of sampleTweets) {
    console.log(`Testing tweet: "${tweet}"`);
    const result = await checkTweetPopularity(tweet);
    
    if (!result) {
      console.log("Failed to get popularity score\n");
      continue;
    }
    
    // We don't need to log anything here as the function already outputs formatted results
    console.log("\n");
  }
  
  console.log("Test complete!");
}

testPopularity().catch(console.error);
