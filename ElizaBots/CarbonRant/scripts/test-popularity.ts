import { checkTweetPopularity } from "../packages/client-twitter/src/popularity";

async function testPopularity() {
  console.log("Testing tweet popularity check function...");
  
  const testTweets = [
    "Climate change is accelerating faster than ever. We must act now! #ClimateAction",
    "Just had lunch today. Whatever.",
    "Amazing news! Canada passed a bill banning single-use plastics nationwide! A huge win for our oceans. #ClimateSolutions"
  ];
  
  for (const tweet of testTweets) {
    console.log(`\nChecking tweet: "${tweet}"`);
    const result = await checkTweetPopularity(tweet);
    if (!result) {
      console.log("Failed to check popularity. Is ElizaServices running?");
    }
    // Wait a second between requests to avoid overwhelming the API
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

testPopularity()
  .then(() => console.log("Test complete!"))
  .catch(err => console.error("Error during test:", err));