import { elizaLogger } from "@elizaos/core";
import fetch from "node-fetch";
import type { IAgentRuntime } from "@elizaos/core";
import * as dotenv from "dotenv";

dotenv.config();

export interface Tweet {
    id: string;
    text: string;
    created_at: string;
    author_id: string;
    username?: string;
    
}

const DEFAULT_API_URL = process.env.ELIZA_LATEST_TWEETS_API || null;


export async function fetchLatestTweetsFromEliza(runtime?: IAgentRuntime) {
    try {
        const runtimeUrl = runtime?.getSetting?.("ELIZA_LATEST_TWEETS_API");
        const apiUrl = runtimeUrl || DEFAULT_API_URL;

        if (!apiUrl) {
            elizaLogger.error("Missing ELIZA_LATEST_TWEETS_API in settings or .env");
            return [];
        }

        elizaLogger.log(`🔍 Fetching latest tweets from ElizaServices API`);
        
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            elizaLogger.error(`❌ Latest tweets fetch failed with status: ${response.status}`);
            return [];
        }
        
        const data = await response.json();
        elizaLogger.log(`✅ Successfully fetched ${Array.isArray(data) ? data.length : 1} tweet(s) from ElizaServices API`);
        
        const verbose = runtime?.getSetting("ELIZA_LATEST_TWEETS_VERBOSE_OUTPUT")?.toLowerCase() === "true";
        
        if (verbose) {
            elizaLogger.log("📊 Latest tweets data:", data);
        }
        
        return data;
    } catch (error) {
        elizaLogger.error("Error fetching latest tweets from ElizaServices:", error);
        return [];
    }
}
