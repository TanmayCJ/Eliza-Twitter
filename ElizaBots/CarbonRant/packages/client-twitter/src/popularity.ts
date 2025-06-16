
import { elizaLogger } from "@elizaos/core";
import fetch from "node-fetch";
import type { IAgentRuntime } from "@elizaos/core";
import * as dotenv from "dotenv";

dotenv.config();

export interface PopularityCheckResult {
  predicted_score: number;
  explanation: string;
  cleaned_text: string;
}

interface PopularityCheckResponse {
  score: number;
  explanation: string;
  originalText: string;
}

const DEFAULT_API_URL = process.env.TWITTER_POPULARITY_API_URL || null;

// Utility: print verbose output without colors
function printVerbose(score: number, text: string, explanation: string) {
  const formattedScore = score.toFixed(2);
  console.log("\n" + "=".repeat(80));
  console.log(`📊 TWEET POPULARITY SCORE: ${formattedScore}/100`);
  console.log("-".repeat(80));
  console.log(`💬 TWEET: "${text}"`);
  console.log("-".repeat(80));
  console.log(`📝 EXPLANATION: ${explanation}`);
  console.log("=".repeat(80) + "\n");
}

export async function checkTweetPopularity(
  tweetText: string,
  runtime?: IAgentRuntime
): Promise<PopularityCheckResponse | null> {
  try {
    const runtimeUrl = runtime?.getSetting?.("TWITTER_POPULARITY_API_URL");
    const apiUrl = runtimeUrl || DEFAULT_API_URL;

    if (!apiUrl) {
      elizaLogger.error("Missing TWITTER_POPULARITY_API_URL in settings or .env");
      return null;
    }

    elizaLogger.log(`🔍 Checking popularity for tweet: "${tweetText.slice(0, 50)}${tweetText.length > 50 ? '...' : ''}"`);

    const res = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: tweetText }),
    });

    if (!res.ok) {
      elizaLogger.error(`❌ Popularity check failed with status: ${res.status}`);
      return null;
    }

    const data = await res.json() as PopularityCheckResult;
    const { predicted_score, explanation } = data;
    const formattedScore = predicted_score.toFixed(2);
    const verbose = runtime?.getSetting("TWITTER_POPULARITY_VERBOSE_OUTPUT")?.toLowerCase() == "true";

    if (verbose) {
      printVerbose(predicted_score, tweetText, explanation);
    } else {
      elizaLogger.log(`📊 Tweet popularity: ${formattedScore}/100 - ${explanation.slice(0, 100)}${explanation.length > 100 ? "..." : ""}`);
    }

    return { score: predicted_score, explanation, originalText: tweetText };
  } catch (err) {
    elizaLogger.error("Error checking tweet popularity:", err);
    return null;
  }
}
