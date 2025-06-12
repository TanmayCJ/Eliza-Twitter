import { elizaLogger } from "@elizaos/core";
import fetch from "node-fetch";

/**
 * Interface for popularity check response from ElizaServices API
 */
export interface PopularityCheckResult {
  predicted_score: number;
  explanation: string;
  cleaned_text: string;
}

/**
 * Checks the popularity score of a tweet text using the ElizaServices API
 * 
 * @param tweetText The tweet text to evaluate
 * @returns A popularity score and explanation, or null if the check fails
 */
export async function checkTweetPopularity(tweetText: string): Promise<{
  score: number;
  explanation: string;
  originalText: string;
} | null> {
  try {
    elizaLogger.log(`🔍 Checking popularity for tweet: "${tweetText.substring(0, 50)}${tweetText.length > 50 ? '...' : ''}"`);
    
    // Call the ElizaServices API
    const response = await fetch("http://127.0.0.1:8000/api/popularity/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: tweetText,
      }),
    });

    if (!response.ok) {
      elizaLogger.error(`❌ Popularity check failed with status: ${response.status}`);
      return null;
    }
    
    const data = await response.json() as PopularityCheckResult;
    
    // Format the score to 2 decimal places
    const formattedScore = data.predicted_score.toFixed(2);
    
    // Make the terminal output more eye-catching with a box display and colors
    // Color codes: \x1b[36m = cyan, \x1b[32m = green, \x1b[33m = yellow, \x1b[0m = reset
    console.log("\n" + "\x1b[36m" + "=".repeat(80) + "\x1b[0m");
    
    // Color the score based on its value
    let scoreColor = "\x1b[31m"; // Red for low scores
    if (data.predicted_score >= 70) {
        scoreColor = "\x1b[32m"; // Green for high scores
    } else if (data.predicted_score >= 40) {
        scoreColor = "\x1b[33m"; // Yellow for medium scores
    }
    
    console.log(`📊 TWEET POPULARITY SCORE: ${scoreColor}${formattedScore}/100\x1b[0m`);
    console.log("\x1b[36m" + "-".repeat(80) + "\x1b[0m");
    console.log(`💬 TWEET: "\x1b[33m${tweetText}\x1b[0m"`);
    console.log("\x1b[36m" + "-".repeat(80) + "\x1b[0m");
    console.log(`📝 EXPLANATION: \x1b[32m${data.explanation}\x1b[0m`);
    console.log("\x1b[36m" + "=".repeat(80) + "\x1b[0m\n");

    return {
      score: data.predicted_score,
      explanation: data.explanation,
      originalText: tweetText,
    };
  } catch (error) {
    elizaLogger.error(`Error checking tweet popularity:`, error);
    return null;
  }
}
