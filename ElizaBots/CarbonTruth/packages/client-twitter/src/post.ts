import type { Tweet } from "agent-twitter-client";
import * as fs from "fs";
import {
    composeContext,
    generateText,
    getEmbeddingZeroVector,
    type IAgentRuntime,
    ModelClass,
    stringToUuid,
    type TemplateType,
    type UUID,
    truncateToCompleteSentence,
    parseJSONObjectFromText,
    extractAttributes,
    cleanJsonResponse,
} from "@elizaos/core";
import { elizaLogger } from "@elizaos/core";
import type { ClientBase } from "./base.ts";
import { postActionResponseFooter } from "@elizaos/core";
import { generateTweetActions } from "@elizaos/core";
import { type IImageDescriptionService, ServiceType } from "@elizaos/core";
import { buildConversationThread, fetchMediaData } from "./utils.ts";
import { twitterMessageHandlerTemplate } from "./interactions.ts";
import { DEFAULT_MAX_TWEET_LENGTH } from "./environment.ts";
import {
    Client,
    Events,
    GatewayIntentBits,
    TextChannel,
    Partials,
} from "discord.js";
import type { State } from "@elizaos/core";
import type { ActionResponse } from "@elizaos/core";
import { MediaData } from "./types.ts";
import { TwitterPrePostHookHandler } from "./hooks.ts";
import { TweetChecker } from "./checks.ts";
import { TweetData, TweetDataSender } from "./database.ts";
const MAX_TIMELINES_TO_FETCH = 15;


//TODO: original tweet template
// const twitterPostTemplate = `
// # Areas of Expertise
// {{knowledge}}

// # About {{agentName}} (@{{twitterUserName}}):
// {{bio}}
// {{lore}}
// {{topics}}

// {{characterPostExamples}}

// {{postDirections}}

// # Task: Generate a post in the voice and style and perspective of {{agentName}} @{{twitterUserName}}.
// Write a post that is {{adjective}} about {{topic}} (without mentioning {{topic}} directly), from the perspective of {{agentName}}. Do not add commentary or acknowledge this request, just write the post.
// Your response should be 1, 2, or 3 sentences (choose the length at random).
// Your response should not contain any questions. Brief, concise statements only. The total character count MUST be less than {{maxTweetLength}}. No emojis. Use \\n\\n (double spaces) between statements if there are multiple statements in your response.`;

//TODO: //proper working template with Hastags
// const twitterPostTemplate = `
// # Areas of Expertise
// {{knowledge}}

// # About {{agentName}} (@{{twitterUserName}}):
// {{bio}}
// {{lore}}
// {{topics}}

// {{characterPostExamples}}

// {{postDirections}}

// {{providers}}

// # Task:
// If a news article is provided, generate a tweet summarizing the article within {{maxTweetLength}} characters. Do not include the article link in the tweet. Instead, reply to the tweet with the article link using 'Link: '. Do not add any additional context, commentary, or unrelated content.

// If no news article is provided, generate a post in the voice, style, and perspective of {{agentName}} (@{{twitterUserName}}).
// Write a post that is {{adjective}} about {{topic}} (without mentioning {{topic}} directly), from the perspective of {{agentName}}. Do not add commentary or acknowledge this request, just write the post.

// # Hashtags
// Include 2-4 relevant hashtags based on the topic, ensuring they fit within the total character limit of {{maxTweetLength}}. Place the hashtags at the end of the response.

// Your response should be 1, 2, or 3 sentences (choose at random).
// The total character count, including hashtags, MUST be less than {{maxTweetLength}} characters. No emojis. Use \n\n (double spaces) between statements if there are multiple statements in your response.

// # Interactivity
// Randomly decide whether the post is a statement or if it asks a question or invites opinions from users. If it's a question or opinion request, ensure it aligns with {{agentName}}'s voice and perspective.
// `;

const maxTweetLength = 160; // Default max tweet length

//TODO: Proper Working Template with hastags 2.0 FIXME:
// const twitterPostTemplate = `
// # Areas of Expertise
// {{knowledge}}

// # About {{agentName}} (@{{twitterUserName}}):
// {{bio}}
// {{lore}}
// {{topics}}

// {{characterPostExamples}}

// {{postDirections}}

// {{providers}}

// # Task:
// If a **news article** is provided, generate a **tweet summarizing the article** within ${maxTweetLength} characters.  
// - **Ensure the total character count includes hashtags and the article link.**  
// - **The article link must be at the end of the response, after the hashtags.**  
// - **Do not add any additional context, commentary, or unrelated content.**  

// If no news article is provided, generate a post in the **voice, style, and perspective** of {{agentName}} (@{{twitterUserName}}).  
// - Write a post that is **{{adjective}} about {{topic}}** (without mentioning {{topic}} directly), from the perspective of {{agentName}}.  
// - **Do not acknowledge this request or include a news link.**  
// - **Hashtags must still appear at the end of the response.**  

// # Hashtags  
// Include **2-3 relevant hashtags** ensuring the total character count **(including hashtags and the link)** does not exceed ${maxTweetLength} characters.  

// # Formatting Rules  
// ✅ **For news tweets:**
// [Summary of the article] #Hashtag1 #Hashtag2 #Hashtag3 **(ensure a space here)** [URL]

// ✅ **For non-news tweets:**
// [Post content in {{agentName}}'s voice. Tweet followed by hashtags] #Hashtag1 #Hashtag2 #Hashtag3


// ✅ **STRICT RULES:**  
// - **The total tweet, including hashtags and link, MUST be within ${maxTweetLength} characters.**  
// - **The article link MUST be at the end of the response, after the hashtags.**  
// - **Hashtags MUST be at the end, before the link.**  
// - **No emojis.**  
// - **Use "\\n\\n" (double spaces) between sentences if multiple sentences are used.**  
// - **Response should be 1, 2, or 3 sentences (choose randomly).**  

// # Example Output  
// ### **For a news tweet:**  
// New research shows ocean temperatures are rising faster than expected. The consequences for marine life and coastal communities could be devastating. #ClimateCrisis #SaveOurOceans #ActNow  https://tinyurl.com/ycypjjxx

// ### **For a non-news tweet:**
// Clean energy isn’t just about the future—it’s about survival. Every choice we make today determines the world we leave behind. #RenewableEnergy #Sustainability #Future

// # Interactivity  
// Randomly decide whether the post is a **statement**, a **question**, or an **opinion request**.  
// If it’s a question or opinion request, ensure it aligns with **{{agentName}}'s** voice and perspective.  
// `;

const twitterPostTemplate = `
# Areas of Expertise
{{knowledge}}

# About {{agentName}} (@{{twitterUserName}}):
{{bio}}
{{lore}}
{{topics}}

{{characterPostExamples}}

{{postDirections}}

{{providers}}

# Task:
If a **news article** is provided, generate a **tweet summarizing the article** within ${maxTweetLength} characters.  
- **The total character count MUST include hashtags and the article link.**  
- **The article link MUST appear AFTER the hashtags and be the FINAL part of the tweet.**  
- **DO NOT add any extra text, emojis, symbols, or commentary after the link.**  

If no news article is provided, generate a tweet based on the agent's **knowledge** about **{{topic}}**, using the voice and perspective of {{agentName}} (@{{twitterUserName}}).  
- **The post must be informative, engaging, or thought-provoking.**  
- **DO NOT acknowledge this instruction in the tweet.**  
- **Hashtags MUST be at the end, and after them, ABSOLUTELY NOTHING.**  

# Hashtag Rules  
- Include **2 to 3** relevant hashtags.  
- **DO NOT** place hashtags anywhere but the very end.  
- The **article link must follow the hashtags**, if a news article is provided.  
- **No content of any kind may follow the hashtags or the link.**

# Formatting Rules  
✅ **For news tweets:**  
[Summary of the article] #hashtag1 #hashtag2 #hashtag3 [link]  

✅ **For non-news tweets:**  
[Content based on topic knowledge] #hashtag1 #hashtag2 #hashtag3  

✅ **ABSOLUTE RULES:**  
- Tweet MUST NOT exceed ${maxTweetLength} characters including hashtags and link.  
- Article link MUST always be at the very end, AFTER hashtags.  
- Hashtags MUST be the final words if there's no link.  
- NO emojis.  
- Use "\\n\\n" (double space) between sentences if there are multiple sentences.  
- Tweet must contain 1 to 3 sentences (choose randomly).  
- DO NOT include the link if there is no article.  
- **AFTER THE LAST HASHTAG OR LINK, ABSOLUTELY NOTHING MUST FOLLOW.**  

# Example Output  
### **News Tweet:**  
New research shows ocean temperatures are rising faster than expected. The consequences for marine life and coastal communities could be devastating. #ClimateCrisis #SaveOurOceans https://example.com/
### **Non-news Tweet:**  
The shift to renewable energy isn't just about cutting emissions—it's about securing a sustainable future. Every step towards clean energy reduces long-term environmental harm. #RenewableEnergy #GreenFuture  

# Interactivity  
Randomly (but not often), choose whether the post is a **statement**, a **question**, or an **opinion request**, staying aligned with the tone and personality of {{agentName}}.
`;



  //TODO: //proper working template for news but without thoughts on news
//   const twitterPostTemplate = `
//   # Areas of Expertise
//   {{knowledge}}
  
//   # About {{agentName}} (@{{twitterUserName}}):
//   {{bio}}
//   {{lore}}
//   {{topics}}
  
//   # News: {{providers}}

//   # Task: Generate a tweet in the voice and style of {{agentName}} (@{{twitterUserName}}), incorporating the provided news.
  
//     A new article **{{providers}}** highlights an important topic. **PRIORITY: Generate a tweet that directly incorporates and comments on this news.** Ensure the post reflects {{agentName}}'s perspective while remaining relevant to the news. Do not explicitly mention {{topic}} unless it is crucial for understanding the news.
  
//   Your response should be 1, 2, or 3 sentences (choose the length at random).
//   Your response should not contain any questions. Brief, concise statements only. The total character count MUST be less than {{maxTweetLength}} characters. Use \\n\\n (double spaces) between statements if there are multiple statements in your response.
   
//   Post Examples = {{characterPostExamples}}
  
//   {{postDirections}}
  
//   # Task: Generate a tweet in the voice and style of {{agentName}} (@{{twitterUserName}}), incorporating the provided news.
  
//   Write a tweet that is {{adjective}} about the news, from the perspective of {{agentName}}. Do not add commentary or acknowledge this request, just write the post keeping in reference the news provided. Also share your views on the news in **one sentence**.
  
//   Your response should be 1, 2, or 3 sentences (choose the length at random).
//   Never start the tweet with "As a 'something'", etc.
//   Your response should not contain any questions. Brief, concise statements only. The total character count MUST be less than {{maxTweetLength}}. Use \\n\\n (double spaces) between statements if there are multiple statements in your response. Don't place the tweet within quotes.
  
//   # If no news is provided:
//   If there is no news provided, generate a tweet based on {{knowledge}}, {{topics}}, and previous tweets (Post Examples). Previous tweets are attached as a reference to understand the way {{agentName}} tweets. The tweet should still align with the views of {{agentName}} and be concise, clear, and engaging. Follow the same rules for length and format. News is the first priority; if news exists, prioritize it over all other factors. Do not start the tweet with quotes.
//   `;

// const twitterPostTemplate = `# Areas of Expertise
// {{knowledge}}

// # About {{agentName}} (@{{twitterUserName}}):
// {{bio}}
// {{lore}}
// {{topics}}

// # News: {{providers}}

// # Task: Generate a tweet in the voice and style of {{agentName}} (@{{twitterUserName}}), incorporating the provided news.

// A new article from **{{providers}}** highlights an important topic. **PRIORITY: Generate a tweet that directly incorporates and comments on this news.** Ensure the post reflects {{agentName}}'s perspective while remaining relevant to the news. Do not explicitly mention {{topic}} unless it is crucial for understanding the news.

// Your response should be 1, 2, or 3 sentences (choose the length at random).
// Your response should not contain any questions. Brief, concise statements only. The total character count MUST be less than 400 characters. Use \n\n (double spaces) between statements if there are multiple statements in your response.
 
// Post Examples = {{characterPostExamples}}

// {{postDirections}}

// # Task: Generate a tweet in the voice and style of {{agentName}} (@{{twitterUserName}}), incorporating the provided news.

// Write a tweet that is {{adjective}} about the news, from the perspective of {{agentName}}. Do not add commentary or acknowledge this request, just write the post keeping in reference to the news provided. Also share your views on the news in **one sentence**.

// Your response should be 1, 2, or 3 sentences (choose the length at random).
// Never start the tweet with "As a 'something'", etc.
// Your response should not contain any questions. Brief, concise statements only. The total character count MUST be less than 400. Use \n\n (double spaces) between statements if there are multiple statements in your response. Don't place the tweet within quotes.

// **If the news provided includes a link, append the link to the end of the tweet in the format: \n\nlink: https://example.com/news**

// # If no news is provided:
// If there is no news provided, generate a tweet based on {{knowledge}}, {{topics}}, and previous tweets (Post Examples). Previous tweets are attached as a reference to understand the way {{agentName}} tweets. The tweet should still align with the views of {{agentName}} and be concise, clear, and engaging. Follow the same rules for length and format. News is the first priority; if news exists, prioritize it over all other factors. Do not start the tweet with quotes.`;


export const twitterActionTemplate =
    `
# INSTRUCTIONS: Determine actions for {{agentName}} (@{{twitterUserName}}) based on:
{{bio}}
{{postDirections}}

Guidelines:
- ONLY engage with content that DIRECTLY relates to character's core interests
- Direct mentions are priority IF they are on-topic
- Skip ALL content that is:
  - Off-topic or tangentially related
  - From high-profile accounts unless explicitly relevant
  - Generic/viral content without specific relevance
  - Political/controversial unless central to character
  - Promotional/marketing unless directly relevant

Actions (respond only with tags):
[LIKE] - Perfect topic match AND aligns with character (9.8/10)
[RETWEET] - Exceptional content that embodies character's expertise (9.5/10)
[QUOTE] - Can add substantial domain expertise (9.5/10)
[REPLY] - Can contribute meaningful, expert-level insight (9.5/10)

Tweet:
{{currentTweet}}

# Respond with qualifying action tags only. Default to NO action unless extremely confident of relevance.` +
    postActionResponseFooter;

interface PendingTweet {
    tweetTextForPosting: string;
    roomId: UUID;
    rawTweetContent: string;
    discordMessageId: string;
    channelId: string;
    timestamp: number;
}

type PendingTweetApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export class TwitterPostClient {
    client: ClientBase;
    runtime: IAgentRuntime;
    twitterUsername: string;
    private isProcessing = false;
    private lastProcessTime = 0;
    private stopProcessingActions = false;
    private isDryRun: boolean;
    private discordClientForApproval: Client;
    private approvalRequired = false;
    private discordApprovalChannelId: string;
    private approvalCheckInterval: number;

    constructor(client: ClientBase, runtime: IAgentRuntime) {
        this.client = client;
        this.runtime = runtime;
        this.twitterUsername = this.client.twitterConfig.TWITTER_USERNAME;
        this.isDryRun = this.client.twitterConfig.TWITTER_DRY_RUN;

        // Log configuration on initialization
        elizaLogger.log("Twitter Client Configuration:");
        elizaLogger.log(`- Username: ${this.twitterUsername}`);
        elizaLogger.log(
            `- Dry Run Mode: ${this.isDryRun ? "enabled" : "disabled"}`
        );

        elizaLogger.log(
            `- Enable Post: ${this.client.twitterConfig.ENABLE_TWITTER_POST_GENERATION ? "enabled" : "disabled"}`
        );

        elizaLogger.log(
            `- Post Interval: ${this.client.twitterConfig.POST_INTERVAL_MIN}-${this.client.twitterConfig.POST_INTERVAL_MAX} minutes`
        );
        elizaLogger.log(
            `- Action Processing: ${
                this.client.twitterConfig.ENABLE_ACTION_PROCESSING
                    ? "enabled"
                    : "disabled"
            }`
        );
        elizaLogger.log(
            `- Action Interval: ${this.client.twitterConfig.ACTION_INTERVAL} minutes`
        );
        elizaLogger.log(
            `- Post Immediately: ${
                this.client.twitterConfig.POST_IMMEDIATELY
                    ? "enabled"
                    : "disabled"
            }`
        );
        elizaLogger.log(
            `- Search Enabled: ${
                this.client.twitterConfig.TWITTER_SEARCH_ENABLE
                    ? "enabled"
                    : "disabled"
            }`
        );

        const targetUsers = this.client.twitterConfig.TWITTER_TARGET_USERS;
        if (targetUsers) {
            elizaLogger.log(`- Target Users: ${targetUsers}`);
        }

        if (this.isDryRun) {
            elizaLogger.log(
                "Twitter client initialized in dry run mode - no actual tweets should be posted"
            );
        }

        // Initialize Discord webhook
        const approvalRequired: boolean =
            this.runtime
                .getSetting("TWITTER_APPROVAL_ENABLED")
                ?.toLocaleLowerCase() === "true";
        if (approvalRequired) {
            const discordToken = this.runtime.getSetting(
                "TWITTER_APPROVAL_DISCORD_BOT_TOKEN"
            );
            const approvalChannelId = this.runtime.getSetting(
                "TWITTER_APPROVAL_DISCORD_CHANNEL_ID"
            );

            const APPROVAL_CHECK_INTERVAL =
                Number.parseInt(
                    this.runtime.getSetting("TWITTER_APPROVAL_CHECK_INTERVAL")
                ) || 5 * 60 * 1000; // 5 minutes

            this.approvalCheckInterval = APPROVAL_CHECK_INTERVAL;

            if (!discordToken || !approvalChannelId) {
                throw new Error(
                    "TWITTER_APPROVAL_DISCORD_BOT_TOKEN and TWITTER_APPROVAL_DISCORD_CHANNEL_ID are required for approval workflow"
                );
            }

            this.approvalRequired = true;
            this.discordApprovalChannelId = approvalChannelId;

            // Set up Discord client event handlers
            this.setupDiscordClient();
        }
    }

    private setupDiscordClient() {
        this.discordClientForApproval = new Client({
            intents: [
                GatewayIntentBits.Guilds,
                GatewayIntentBits.GuildMessages,
                GatewayIntentBits.MessageContent,
                GatewayIntentBits.GuildMessageReactions,
            ],
            partials: [Partials.Channel, Partials.Message, Partials.Reaction],
        });
        this.discordClientForApproval.once(
            Events.ClientReady,
            (readyClient) => {
                elizaLogger.log(
                    `Discord bot is ready as ${readyClient.user.tag}!`
                );

                // Generate invite link with required permissions
                const invite = `https://discord.com/api/oauth2/authorize?client_id=${readyClient.user.id}&permissions=274877991936&scope=bot`;
                // 274877991936 includes permissions for:
                // - Send Messages
                // - Read Messages/View Channels
                // - Read Message History

                elizaLogger.log(
                    `Use this link to properly invite the Twitter Post Approval Discord bot: ${invite}`
                );
            }
        );
        // Login to Discord
        this.discordClientForApproval.login(
            this.runtime.getSetting("TWITTER_APPROVAL_DISCORD_BOT_TOKEN")
        );
    }

    async start() {
        if (!this.client.profile) {
            await this.client.init();
        }

        const generateNewTweetLoop = async () => {
            const lastPost = await this.runtime.cacheManager.get<{
                timestamp: number;
            }>("twitter/" + this.twitterUsername + "/lastPost");

            const lastPostTimestamp = lastPost?.timestamp ?? 0;
            const minMinutes = this.client.twitterConfig.POST_INTERVAL_MIN;
            const maxMinutes = this.client.twitterConfig.POST_INTERVAL_MAX;
            const randomMinutes =
                Math.floor(Math.random() * (maxMinutes - minMinutes + 1)) +
                minMinutes;
            const delay = randomMinutes * 60 * 1000;

            if (Date.now() > lastPostTimestamp + delay) {
                await this.generateNewTweet();
            }

            setTimeout(() => {
                generateNewTweetLoop(); // Set up next iteration
            }, delay);

            elizaLogger.log(`Next tweet scheduled in ${randomMinutes} minutes`);
        };

        const processActionsLoop = async () => {
            const actionInterval = this.client.twitterConfig.ACTION_INTERVAL; // Defaults to 5 minutes

            while (!this.stopProcessingActions) {
                try {
                    const results = await this.processTweetActions();
                    if (results) {
                        elizaLogger.log(`Processed ${results.length} tweets`);
                        elizaLogger.log(
                            `Next action processing scheduled in ${actionInterval} minutes`
                        );
                        // Wait for the full interval before next processing
                        await new Promise(
                            (resolve) =>
                                setTimeout(resolve, actionInterval * 60 * 1000) // now in minutes
                        );
                    }
                } catch (error) {
                    elizaLogger.error(
                        "Error in action processing loop:",
                        error
                    );
                    // Add exponential backoff on error
                    await new Promise((resolve) => setTimeout(resolve, 30000)); // Wait 30s on error
                }
            }
        };

        if (this.client.twitterConfig.POST_IMMEDIATELY) {
            await this.generateNewTweet();
        }

        if (this.client.twitterConfig.ENABLE_TWITTER_POST_GENERATION) {
            generateNewTweetLoop();
            elizaLogger.log("Tweet generation loop started");
        }

        if (this.client.twitterConfig.ENABLE_ACTION_PROCESSING) {
            processActionsLoop().catch((error) => {
                elizaLogger.error(
                    "Fatal error in process actions loop:",
                    error
                );
            });
        }

        // Start the pending tweet check loop if enabled
        if (this.approvalRequired) this.runPendingTweetCheckLoop();
    }

    private runPendingTweetCheckLoop() {
        setInterval(async () => {
            await this.handlePendingTweet();
        }, this.approvalCheckInterval);
    }

    createTweetObject(
        tweetResult: any,
        client: any,
        twitterUsername: string
    ): Tweet {
        return {
            id: tweetResult.rest_id,
            name: client.profile.screenName,
            username: client.profile.username,
            text: tweetResult.legacy.full_text,
            conversationId: tweetResult.legacy.conversation_id_str,
            createdAt: tweetResult.legacy.created_at,
            timestamp: new Date(tweetResult.legacy.created_at).getTime(),
            userId: client.profile.id,
            inReplyToStatusId: tweetResult.legacy.in_reply_to_status_id_str,
            permanentUrl: `https://twitter.com/${twitterUsername}/status/${tweetResult.rest_id}`,
            hashtags: [],
            mentions: [],
            photos: [],
            thread: [],
            urls: [],
            videos: [],
        } as Tweet;
    }

    async processAndCacheTweet(
        runtime: IAgentRuntime,
        client: ClientBase,
        tweet: Tweet,
        roomId: UUID,
        rawTweetContent: string,
        store: boolean = true
    ) {
        // Cache the last post details
        await runtime.cacheManager.set(
            `twitter/${client.profile.username}/lastPost`,
            {
                id: tweet.id,
                timestamp: Date.now(),
            }
        );

        // Cache the tweet
        await client.cacheTweet(tweet);

        // Log the posted tweet
        elizaLogger.log(`Tweet posted:\n ${tweet.permanentUrl}`);

        // Print collected tweet information
        if (store) { 
            this.storeTweetInfo(tweet, rawTweetContent, runtime);
        }

        // Ensure the room and participant exist
        await runtime.ensureRoomExists(roomId);
        await runtime.ensureParticipantInRoom(runtime.agentId, roomId);

        // Create a memory for the tweet
        await runtime.messageManager.createMemory({
            id: stringToUuid(tweet.id + "-" + runtime.agentId),
            userId: runtime.agentId,
            agentId: runtime.agentId,
            content: {
                text: rawTweetContent.trim(),
                url: tweet.permanentUrl,
                source: "twitter",
            },
            roomId,
            embedding: getEmbeddingZeroVector(),
            createdAt: tweet.timestamp,
        });
    }

    //FIXME: Add a method to handle the approval process for tweets
    /**
     * Collects and prints detailed tweet information including permalink, date/time, content, URLs, hashtags, and images
     * Also stores the tweet record in the PostgreSQL database
     * 
     * @param tweet The Tweet object to print information for
     * @param rawTweetContent The original raw content of the tweet
     */
    storeTweetInfo(tweet: Tweet, rawTweetContent: string, runtime: IAgentRuntime) {
        const date = new Date(tweet.timestamp);
        const formattedDate = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        const formattedTime = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });

        const divider = "=".repeat(50);
        
        let infoOutput = `\n${divider}\n`;
        infoOutput += `TWEET INFORMATION:\n`;
        infoOutput += `${tweet.id}`
        infoOutput += `${divider}\n`;
        infoOutput += `Permalink: ${tweet.permanentUrl}\n`;
        infoOutput += `Date: ${formattedDate}\n`;
        infoOutput += `Time: ${formattedTime}\n`;
        infoOutput += `Content: ${tweet.text}\n`;
        
            // Try to extract hashtags from text using regex
            const hashtagRegex = /#(\w+)/g;
            const extractedHashtags = [];
            let match;
            while ((match = hashtagRegex.exec(tweet.text)) !== null) {
                extractedHashtags.push(match[1]);
            }
            if (extractedHashtags.length > 0) {
                infoOutput += `Hashtags: ${extractedHashtags.join(', ')}\n`;
            }
        
        // Add photos/images if present
        const imageArray = []
        if (tweet.photos && tweet.photos.length > 0) {
            infoOutput += `Images: \n  ${tweet.photos.map(photo => photo.url).join('\n  ')}\n`;
            imageArray.push(...tweet.photos.map(photo => photo.url));
        }
        
        infoOutput += `${divider}\n`;
        
        // Log the collected information
        elizaLogger.info(infoOutput);
        
        const tweetDataPG: TweetData = {
            sender: "carbontruth",
            tweetData: {
                tweetID: String(tweet.id),
                date: String(formattedDate),
                time: String(formattedTime),
                tweetLnk: String(tweet.permanentUrl),
                content: String(tweet.text),
                hashtags: extractedHashtags,
                imageUrl: imageArray,
            }
        };
        const tweetSender = new TweetDataSender();

        elizaLogger.log(`Tweet Data: ${JSON.stringify(tweetDataPG)}`);

        (async () => {
            try {
                const id = await tweetSender.sendTweetObject(tweetDataPG);
              if (id !== null) {
                elizaLogger.log(`Tweet inserted with DB ID: ${id}`);
              } else {
                elizaLogger.log('Tweet already exists or was not inserted.');
              }
            } catch (error) {
                elizaLogger.error('Error inserting tweet:', String(error));
            }
          })();
          
        // Store the tweet in PostgreSQL database
        // this.storeTweetInDatabase(tweet, formattedDate, formattedTime, runtime)
        //     .catch(error => {
        //         elizaLogger.error(`Failed to store tweet in database: ${error}`);
        //     });
    }

    /**
     * Creates a Twitter thread by splitting content into multiple tweets and posting them in sequence
     * Each tweet will be numbered (e.g., 1/6, 2/6, etc.)
     * 
     * @param content The full content to be split into multiple tweets
     * @param totalParts Optional - specify the exact number of tweets in the thread, otherwise calculated automatically
     * @returns Array of tweet IDs that were posted as part of the thread
     */
    async createTwitterThread(
        runtime: IAgentRuntime,
        content: string, 
        roomId: UUID,
        totalParts?: number
    ): Promise<string[]> {
        elizaLogger.log("Creating Twitter thread");
        
        // Maximum content length per tweet, accounting for the thread indicator (e.g., " 1/6")
        const maxContentPerTweet = this.client.twitterConfig.MAX_TWEET_LENGTH - 10;
        
        // Split content into reasonable chunks while preserving sentence structure
        const parts = await this.splitContentForThread(runtime, content, maxContentPerTweet, totalParts);
        const actualTotalParts = parts.length;
        
        // Array to store the IDs of all tweets in the thread
        const tweetIds: string[] = [];
        let previousTweetId: string | undefined = undefined;

        let storeTweetIfThread = true;
        
        // Post each part as a tweet in the thread
        for (let i = 0; i < parts.length; i++) {
            const partNumber = i + 1;
            const threadIndicator = ` ${partNumber}/${actualTotalParts}`;
            
            // Add the thread indicator to the tweet content
            let tweetContent = parts[i].trim();
            
            // // Check if we need to append the thread indicator or if it's already embedded in content
            // if (!tweetContent.includes(`${partNumber}/${actualTotalParts}`)) {
            //     // Determine the best place to add the indicator - either at the beginning or end
            //     if (tweetContent.startsWith("@") || Math.random() > 0.7) {
            //         // For replies or randomly, place at the end
            //         tweetContent = `${tweetContent} ${threadIndicator}`;
            //     } else {
            //         // Otherwise, place at the beginning
            //         tweetContent = `${threadIndicator} ${tweetContent}`;
            //     }
            // }
            
            elizaLogger.log(`Posting thread part ${partNumber}/${actualTotalParts}: ${tweetContent}`);
            
            try {
                // Post this tweet in the thread - if not the first tweet, use the previous tweet ID as reply-to
                let result;
                
                if (tweetContent.length > DEFAULT_MAX_TWEET_LENGTH) {
                    result = await this.handleNoteTweet(this.client, tweetContent, previousTweetId);
                } else {
                    result = await this.sendStandardTweet(this.client, tweetContent, previousTweetId);
                }
                
                if (!result) {
                    elizaLogger.error(`Failed to post tweet ${partNumber}/${actualTotalParts}`);
                    continue;
                }
                
                const tweet = this.createTweetObject(result, this.client, this.twitterUsername);
                
                // Store the ID for the next tweet in the thread
                previousTweetId = tweet.id;
                tweetIds.push(tweet.id);
                
                // Update the tweet text to match the final version that was posted
                tweet.text = tweetContent;
                
                // Process and cache the tweet
                await this.processAndCacheTweet(
                    this.runtime,
                    this.client,
                    tweet,
                    roomId,
                    tweetContent,
                    storeTweetIfThread
                );
                
                storeTweetIfThread = false;
                // Add a short delay between tweets to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 3000)); // 3 second delay
                
            } catch (error) {
                elizaLogger.error(`Error posting tweet ${partNumber}/${actualTotalParts}:`, error);
                break; // Stop posting remaining tweets if an error occurs
            }
        }
        
        return tweetIds;
    }

    /**
     * Splits a long piece of content into smaller chunks suitable for tweets
     * Tries to split at sentence boundaries when possible
     * 
     * @param content The full content to split
     * @param maxLength Maximum length for each chunk
     * @param totalParts Optional - force content to be split into exactly this many parts
     * @returns Array of content chunks ready to be tweeted
     */
 async splitContentForThread(
        runtime: IAgentRuntime,
        content: string, 
        maxLength: number,
        totalParts?: number
    ): Promise<string[]> {
        // If the content already fits in one tweet, return it as a single part
        if (content.length <= maxLength && (!totalParts || totalParts <= 1)) {
            return [content];
        }

        const threadPrompt = `Tweet: {${content}}
        Here is a tweet. Create a Twitter thread with ${totalParts} tweets that:

-In 1/ always include the link from the tweet and dont include the link in every thread, just the first thread
-Explain its significance
-Describe how it could affect us
-Talk about benefits or positive effects on Earth
-Output should be a JSON array of tweets
-At the end of each thread dont mention 1/6, 2/6 just at start mention 1/, 2/

example output: {
        "tweets": ["1/ 🌥️ Did you know? Modern solar panels can now generate electricity even on cloudy days. This advancement marks a huge step forward for clean energy reliability.",
    "2/ The ability to function in low-light conditions means solar energy can be harnessed more consistently—reducing our dependence on fossil fuels even in less sunny regions.",
    "3/ This is a game-changer for urban areas and countries with frequent cloud cover. Solar power is no longer just for deserts—it's now for everyone, everywhere.",
    "4/ On a global scale, this tech boosts our fight against climate change. More uptime = more clean energy = fewer emissions.",
    "5/ As solar becomes more efficient and widespread, we inch closer to a sustainable, decentralized, and eco-friendly energy future. Bright days ahead—even when it’s cloudy. ☁️⚡"]}
`;
        
        const threadTweets = await generateText({
            runtime,
            context: threadPrompt,
            modelClass: ModelClass.MEDIUM,
            stop: ["\n"]
        });

        elizaLogger.log(`Thread prompt: `, threadTweets);
        console.log(threadTweets);

        const threadTweetsString = threadTweets.toString();

        // elizaLogger.log(`Thread tweets: ${threadTweetsString}`);

        const match = threadTweetsString.match(/{[\s\S]*}/);

        elizaLogger.log(`Matched JSON: ${String(match) as string}`);

        const jsonContent = match[0];
        const data = JSON.parse(jsonContent);

        elizaLogger.log(`Parsed JSON: ${String(data) as string}`);

        // Map the tweets to an array of strings using a for loop
        const chunks: string[] = [];
        for (let i = 0; i < data.tweets.length; i++) {
            const tweet = data.tweets[i];
            if (typeof tweet === 'string') {
                chunks.push(tweet.trim());
            }
        }
        
        elizaLogger.log(`Split content into ${chunks.length} parts`);
        elizaLogger.log(String(chunks) as string);
        // if (totalParts && totalParts > 0) {
        //     // If total parts is specified, try to divide content evenly
        //     const avgChunkSize = Math.ceil(content.length / totalParts);
            
        //     let startPos = 0;
        //     for (let i = 0; i < totalParts; i++) {
        //         const isLastChunk = i === totalParts - 1;
        //         if (isLastChunk) {
        //             // For the last chunk, just take all remaining content
        //             chunks.push(content.substring(startPos));
        //         } else {
        //             // Calculate end position for this chunk
        //             let endPos = startPos + avgChunkSize;
                    
        //             // Try to find a good breaking point (end of sentence or paragraph)
        //             let breakPos = this.findBreakPoint(content, endPos, startPos);
                    
        //             // Extract the chunk and add it to our array
        //             const chunk = content.substring(startPos, breakPos).trim();
        //             chunks.push(chunk);
                    
        //             // Update the start position for the next chunk
        //             startPos = breakPos;
        //         }
        //     }
        // } else {
        //     // No specific part count requested, so split based on max length
        //     let currentPos = 0;
            
        //     while (currentPos < content.length) {
        //         // If remaining content fits in one tweet, add it and finish
        //         if (content.length - currentPos <= maxLength) {
        //             chunks.push(content.substring(currentPos));
        //             break;
        //         }
                
        //         // Find a good breaking point
        //         let breakPos = this.findBreakPoint(content, currentPos + maxLength, currentPos);
                
        //         // Extract the chunk and add it to our array
        //         const chunk = content.substring(currentPos, breakPos).trim();
        //         chunks.push(chunk);
                
        //         // Move to the next chunk
        //         currentPos = breakPos;
        //     }
        // }
        
        return chunks;
    }
    
    /**
     * Finds a good point to break text, preferring end of sentences or paragraphs
     * 
     * @param text The text to analyze
     * @param targetPos The ideal position to break at
     * @param startPos The starting position of the current chunk
     * @returns The position to break the text
     */
    private findBreakPoint(text: string, targetPos: number, startPos: number): number {
        // Make sure we don't go past the end of the text
        const maxPos = Math.min(targetPos, text.length);
        
        // Look for paragraph breaks first (they're the cleanest breaks)
        for (let i = maxPos; i > startPos + 10; i--) {
            if (text[i] === '\n' && text[i-1] === '\n') {
                return i + 1; // Position after the double newline
            }
        }
        
        // Look for sentence endings (.!?)
        const sentenceEndRegex = /[.!?]\s/;
        for (let i = maxPos; i > startPos + 10; i--) {
            if (i < text.length - 1 && sentenceEndRegex.test(text.substring(i-1, i+1))) {
                return i + 1; // Position after the sentence end and space
            }
        }
        
        // Look for other reasonable breaks like commas, semicolons, or single newlines
        const otherBreakRegex = /[,;:]\s|\n/;
        for (let i = maxPos; i > startPos + 10; i--) {
            if (i < text.length - 1 && otherBreakRegex.test(text.substring(i-1, i+1))) {
                return i + 1; // Position after the break character and space
            }
        }
        
        // If no good breaks found, look for any space
        for (let i = maxPos; i > startPos + 10; i--) {
            if (text[i] === ' ') {
                return i + 1; // Position after the space
            }
        }
        
        // If we still haven't found a break point, just break at the max position
        return maxPos;
    }

    /**
     * Generates and posts a thread of tweets from a long piece of content.
     * Creates a sequence of numbered tweets that form a coherent thread.
     * 
     * @param threadContent The full content to be split into a thread
     * @param totalParts Optional - specify exactly how many tweets to split the content into
     * @returns Array of tweet IDs in the thread
     */
    async generateTwitterThread(runtime: IAgentRuntime, threadContent: string, totalParts?: number): Promise<string[]> {
        elizaLogger.log("Generating Twitter thread");

        try {
            const roomId = stringToUuid(
                "twitter_thread_room-" + this.client.profile.username
            );
            
            await this.runtime.ensureUserExists(
                this.runtime.agentId,
                this.client.profile.username,
                this.runtime.character.name,
                "twitter"
            );
            
            if (this.isDryRun) {
                // Just log what would have been posted
                const parts = await this.splitContentForThread(runtime,
                    threadContent, 
                    this.client.twitterConfig.MAX_TWEET_LENGTH - 10,
                    totalParts
                );
                
                elizaLogger.info(`Dry run: would have posted Twitter thread with ${parts.length} tweets`);
                parts.forEach((part, i) => {
                    elizaLogger.info(`Tweet ${i+1}/${parts.length}: ${part}`);
                });
                
                return [];
            } else if (this.approvalRequired) {
                // For now, send the entire thread for approval as one unit
                elizaLogger.log("Sending thread for approval");
                const threadPreview = threadContent.substring(0, 500) + 
                    (threadContent.length > 500 ? "..." : "") + 
                    `\n\n[Will be posted as a thread of approximately ${totalParts || Math.ceil(threadContent.length / 240)} tweets]`;
                
                await this.sendForApproval(threadPreview, roomId, threadContent);
                elizaLogger.log("Thread sent for approval");
                return [];
            } else {
                // Post the thread directly
                return await this.createTwitterThread(this.runtime, threadContent, roomId, totalParts);
            }
        } catch (error) {
            elizaLogger.error("Error generating Twitter thread:", String(error) as string);
            return [];
        }
    }

    async handleNoteTweet(
        client: ClientBase,
        content: string,
        tweetId?: string,
        mediaData?: MediaData[]
    ) {
        try {
            const noteTweetResult = await client.requestQueue.add(
                async () =>
                    await client.twitterClient.sendNoteTweet(
                        content,
                        tweetId,
                        mediaData
                    )
            );

            if (noteTweetResult.errors && noteTweetResult.errors.length > 0) {
                // Note Tweet failed due to authorization. Falling back to standard Tweet.
                const truncateContent = truncateToCompleteSentence(
                    content,
                    this.client.twitterConfig.MAX_TWEET_LENGTH
                );
                return await this.sendStandardTweet(
                    client,
                    truncateContent,
                    tweetId
                );
            } else {
                return noteTweetResult.data.notetweet_create.tweet_results
                    .result;
            }
        } catch (error) {
            throw new Error(`Note Tweet failed: ${error}`);
        }
    }

    async sendStandardTweet(
        client: ClientBase,
        content: string,
        tweetId?: string,
        mediaData?: MediaData[]
    ) {
        try {
            const standardTweetResult = await client.requestQueue.add(
                async () =>
                    await client.twitterClient.sendTweet(
                        content,
                        tweetId,
                        mediaData
                    )
            );
            const body = await standardTweetResult.json();
            if (!body?.data?.create_tweet?.tweet_results?.result) {
                elizaLogger.error("Error sending tweet; Bad response:", body);
                return;
            }
            return body.data.create_tweet.tweet_results.result;
        } catch (error) {
            elizaLogger.error("Error sending standard Tweet:", error);
            throw error;
        }
    }

    async postTweet(
        runtime: IAgentRuntime,
        client: ClientBase,
        tweetTextForPosting: string,
        roomId: UUID,
        rawTweetContent: string,
        twitterUsername: string,
        mediaData?: MediaData[]
    ) {
        
        try {
            // elizaLogger.log(`Posting new tweet:\n`);

            const containsLink = await TwitterPrePostHookHandler.tweetContainsUrl(
                tweetTextForPosting
            );

            if (!containsLink) {
                tweetTextForPosting = await TwitterPrePostHookHandler.addFactReferenceToTweet(
                    runtime,
                    tweetTextForPosting,
                );
            }

            const time = Date.now();
            const currentTime = new Date(time).toLocaleString("en-US", {
                timeZone: "IST",
            });
            elizaLogger.log(`Current UTC time: ${currentTime as string}`);

            const fixTweet = `Time: ${currentTime as string}
Tweet: ${tweetTextForPosting}

* Reformat this tweet with the following guidelines in mind:
* 1. ALWAYS preserve any URLs or shortened links from tinyurl.com (e.g., https://tinyurl.com/xyz) exactly as they appear.
* 2. REMOVE any other links that are not from tinyurl.com.
* 3. Use a variety of natural formats:
    - Sometimes write as one flowing sentence.
    - Other times break it into parts, like:
        Some part of the tweet.\n

        Mid part of the tweet.\n

        Final thought, link, or hashtags.
* 4. Vary the total length of tweets — aim to keep the total length under 280 characters.
* 5. Optionally start with a casual greeting about 20% of the time, based on the current time. Avoid using phrases like "Hey" or "Hey, it's 8:00 PM."
* 6. The casual greeting should be relevant to the content of the tweet and not generic, but only in about 20% of cases.
* 7. Limit the number of hashtags to a maximum of 2.
* 8. Prefer turning relevant keywords already present in the tweet into hashtags, rather than adding new ones.
* 9. Place hashtags naturally — either integrated into the sentence or grouped at the end (with proper spacing).
* 10. Ensure links are easy to find — preferably near the end, but not strictly required.
* 11. Keep the tweet’s total character count at or under 280 characters.
* 12. Preserve the original meaning and core message of the tweet.
* 13. Make the tone feel conversational and authentic — vary sentence style and rhythm from tweet to tweet, but always aim for conciseness.
`;

            elizaLogger.info("Fixing Tweet:\n" + (fixTweet as string));
            
            const fixedTweet = await generateText({
                runtime,
                context: fixTweet,
                modelClass: ModelClass.MEDIUM,
                stop: ["\n"],
            });   

            elizaLogger.info("Fixed Tweet:\n" + (fixedTweet as string));

            tweetTextForPosting = fixedTweet.trim();

            try {
                const tweetInfo = {
                    text: tweetTextForPosting,
                    raw: rawTweetContent,
                    username: twitterUsername,
                    mediaData: mediaData
                };

                //FIXME: Add a check for the tweet length and truncate if necessary
                // Perform tweet safety and popularity checks
                const tweetChecker = new TweetChecker();
                
                try {
                    // Check for tweet safety
                    const isSafe = await tweetChecker.checkTweetSafety(tweetTextForPosting);
                    elizaLogger.info(`Tweet safety check result: ${isSafe ? 'SAFE' : 'UNSAFE'}`);
                    
                    // If the tweet is not safe, regenerate it
                    if (!isSafe) {
                        elizaLogger.warn(`Tweet failed safety check - Regenerating safer content`);
                        tweetTextForPosting = await TwitterPrePostHookHandler.regenerateTweetForSafety(
                            runtime,
                            tweetTextForPosting,
                            client
                        );
                        // Update the tweet info with the new text
                        tweetInfo.text = tweetTextForPosting;
                    }
                    
                    // Check for tweet popularity
                    const popularityResult = await tweetChecker.checkTweetPopularity(tweetTextForPosting);
                    const { isPopular, score: popularityScore } = popularityResult;
                    
                    // If the tweet is not likely to be popular, regenerate it
                    if (!isPopular && popularityScore < 10) {
                        elizaLogger.warn(`Tweet might not be engaging enough - Regenerating for better engagement`);
                        tweetTextForPosting = await TwitterPrePostHookHandler.regenerateTweetForPopularity(
                            runtime,
                            tweetTextForPosting,
                            popularityScore,
                            client
                        );
                        // Update the tweet info with the new text
                        tweetInfo.text = tweetTextForPosting;
                    }
                    
                    // Log combined result
                    if (isSafe && isPopular) {
                        elizaLogger.info(`Tweet passed both safety and popularity checks ✅`);
                    } else if (!isSafe) {
                        elizaLogger.warn(`Tweet failed safety check ❌ - Content has been regenerated`);
                    } else if (!isPopular) {
                        elizaLogger.warn(`Tweet might not be popular enough ⚠️ - Content has been improved`);
                    }
                } catch (checkError) {
                    elizaLogger.error("Error during tweet safety/popularity checks:", checkError);
                    // Continue with posting even if checks fail
                }
                
                // Process the pre-post hook and get updated media data if any
                const updatedMediaData = await TwitterPrePostHookHandler.processPrePostHook(runtime, tweetInfo);
                if (updatedMediaData) {
                    mediaData = updatedMediaData;
                }
                
                // Ensure tweetInfo has the latest content for logging
                tweetInfo.text = tweetTextForPosting;
                
            } catch (hookError) {
                // Continue with posting even if hook fails
                elizaLogger.error("Error in pre-post hook:", hookError);
            }

            let result;

            const thread = true;
            if (!thread) {
            if (tweetTextForPosting.length > DEFAULT_MAX_TWEET_LENGTH) {
                result = await this.handleNoteTweet(
                    client,
                    tweetTextForPosting,
                    undefined,
                    mediaData
                );
            } else {
                result = await this.sendStandardTweet(
                    client,
                    tweetTextForPosting,
                    undefined,
                    mediaData
                );
            }

            const tweet = this.createTweetObject(
                result,
                client,
                twitterUsername
            );
            
            // Update the tweet text to match the final version that was posted
            tweet.text = tweetTextForPosting;
           
                await this.processAndCacheTweet(
                    runtime,
                    client,
                    tweet,
                    roomId,
                    tweetTextForPosting // Use the modified tweet text as the raw content
                );
            }
            else {
                this.generateTwitterThread(runtime, String(tweetTextForPosting) as string, 6);
            }
        } catch (error) {
            elizaLogger.error("Error sending tweet:", error as string);
        }
    }

    /**
     * Generates and posts a new tweet. If isDryRun is true, only logs what would have been posted.
     */
    async generateNewTweet() {
        elizaLogger.log("Generating new tweet");

        try {
            const roomId = stringToUuid(
                "twitter_generate_room-" + this.client.profile.username
            );
            await this.runtime.ensureUserExists(
                this.runtime.agentId,
                this.client.profile.username,
                this.runtime.character.name,
                "twitter"
            );

            const topics = this.runtime.character.topics.join(", ");
            const maxTweetLength = this.client.twitterConfig.MAX_TWEET_LENGTH;
            const state = await this.runtime.composeState(
                {
                    userId: this.runtime.agentId,
                    roomId: roomId,
                    agentId: this.runtime.agentId,
                    content: {
                        text: topics || "",
                        action: "TWEET",
                    },
                },
                {
                    twitterUserName: this.client.profile.username,
                    maxTweetLength,
                }
            );

            const context = composeContext({
                state,
                template:
                    this.runtime.character.templates?.twitterPostTemplate ||
                    twitterPostTemplate,
            });

            elizaLogger.debug("generate post prompt:\n" + context);

            const response = await generateText({
                runtime: this.runtime,
                context,
                modelClass: ModelClass.SMALL,
            });

            const rawTweetContent = cleanJsonResponse(response);

            // First attempt to clean content
            let tweetTextForPosting = null;
            let mediaData = null;

            // Try parsing as JSON first
            const parsedResponse = parseJSONObjectFromText(rawTweetContent);
            if (parsedResponse?.text) {
                tweetTextForPosting = parsedResponse.text;
            } else {
                // If not JSON, use the raw text directly
                tweetTextForPosting = rawTweetContent.trim();
            }

            if (
                parsedResponse?.attachments &&
                parsedResponse?.attachments.length > 0
            ) {
                mediaData = await fetchMediaData(parsedResponse.attachments);
            }

            // Try extracting text attribute
            if (!tweetTextForPosting) {
                const parsingText = extractAttributes(rawTweetContent, [
                    "text",
                ]).text;
                if (parsingText) {
                    tweetTextForPosting = truncateToCompleteSentence(
                        extractAttributes(rawTweetContent, ["text"]).text,
                        this.client.twitterConfig.MAX_TWEET_LENGTH
                    );
                }
            }

            // Use the raw text
            if (!tweetTextForPosting) {
                tweetTextForPosting = rawTweetContent;
            }

            // Truncate the content to the maximum tweet length specified in the environment settings, ensuring the truncation respects sentence boundaries.
            if (maxTweetLength) {
                tweetTextForPosting = truncateToCompleteSentence(
                    tweetTextForPosting,
                    maxTweetLength
                );
            }

            const removeQuotes = (str: string) =>
                str.replace(/^['"](.*)['"]$/, "$1");

            const fixNewLines = (str: string) => str.replaceAll(/\\n/g, "\n\n"); //ensures double spaces

            // Final cleaning
            tweetTextForPosting = removeQuotes(
                fixNewLines(tweetTextForPosting)
            );

            if (this.isDryRun) {
                elizaLogger.info(
                    `Dry run: would have posted tweet: ${tweetTextForPosting}`
                );
                return;
            }

            try {
                if (this.approvalRequired) {
                    // Send for approval instead of posting directly
                    elizaLogger.log(
                        `Sending Tweet For Approval:\n ${tweetTextForPosting}`
                    );
                    await this.sendForApproval(
                        tweetTextForPosting,
                        roomId,
                        rawTweetContent
                    );
                    elizaLogger.log("Tweet sent for approval");
                } else {
                    elizaLogger.log(
                        `Posting new tweet:\n ${tweetTextForPosting}`
                    );
                    this.postTweet(
                        this.runtime,
                        this.client,
                        tweetTextForPosting,
                        roomId,
                        rawTweetContent,
                        this.twitterUsername,
                        mediaData
                    );
                }
            } catch (error) {
                elizaLogger.error("Error sending tweet:", error as string);
            }
        } catch (error) {
            elizaLogger.error("Error generating new tweet:", error);
        }
    }

    private async generateTweetContent(
        tweetState: any,
        options?: {
            template?: TemplateType;
            context?: string;
        }
    ): Promise<string> {
        const context = composeContext({
            state: tweetState,
            template:
                options?.template ||
                this.runtime.character.templates?.twitterPostTemplate ||
                twitterPostTemplate,
        });

        const response = await generateText({
            runtime: this.runtime,
            context: options?.context || context,
            modelClass: ModelClass.SMALL,
        });

        elizaLogger.log("generate tweet content response:\n" + response);

        // First clean up any markdown and newlines
        const cleanedResponse = cleanJsonResponse(response);

        // Try to parse as JSON first
        const jsonResponse = parseJSONObjectFromText(cleanedResponse);
        if (jsonResponse.text) {
            const truncateContent = truncateToCompleteSentence(
                jsonResponse.text,
                this.client.twitterConfig.MAX_TWEET_LENGTH
            );
            return truncateContent;
        }
        if (typeof jsonResponse === "object") {
            const possibleContent =
                jsonResponse.content ||
                jsonResponse.message ||
                jsonResponse.response;
            if (possibleContent) {
                const truncateContent = truncateToCompleteSentence(
                    possibleContent,
                    this.client.twitterConfig.MAX_TWEET_LENGTH
                );
                return truncateContent;
            }
        }

        let truncateContent = null;
        // Try extracting text attribute
        const parsingText = extractAttributes(cleanedResponse, ["text"]).text;
        if (parsingText) {
            truncateContent = truncateToCompleteSentence(
                parsingText,
                this.client.twitterConfig.MAX_TWEET_LENGTH
            );
        }

        if (!truncateContent) {
            // If not JSON or no valid content found, clean the raw text
            truncateContent = truncateToCompleteSentence(
                cleanedResponse,
                this.client.twitterConfig.MAX_TWEET_LENGTH
            );
        }

        return truncateContent;
    }

    /**
     * Processes tweet actions (likes, retweets, quotes, replies). If isDryRun is true,
     * only simulates and logs actions without making API calls.
     */
    private async processTweetActions() {
        if (this.isProcessing) {
            elizaLogger.log("Already processing tweet actions, skipping");
            return null;
        }

        try {
            this.isProcessing = true;
            this.lastProcessTime = Date.now();

            elizaLogger.log("Processing tweet actions");

            await this.runtime.ensureUserExists(
                this.runtime.agentId,
                this.twitterUsername,
                this.runtime.character.name,
                "twitter"
            );

            const timelines = await this.client.fetchTimelineForActions(
                MAX_TIMELINES_TO_FETCH
            );
            const maxActionsProcessing =
                this.client.twitterConfig.MAX_ACTIONS_PROCESSING;
            const processedTimelines = [];

            for (const tweet of timelines) {
                try {
                    // Skip if we've already processed this tweet
                    const memory =
                        await this.runtime.messageManager.getMemoryById(
                            stringToUuid(tweet.id + "-" + this.runtime.agentId)
                        );
                    if (memory) {
                        elizaLogger.log(
                            `Already processed tweet ID: ${tweet.id}`
                        );
                        continue;
                    }

                    const roomId = stringToUuid(
                        tweet.conversationId + "-" + this.runtime.agentId
                    );

                    const tweetState = await this.runtime.composeState(
                        {
                            userId: this.runtime.agentId,
                            roomId,
                            agentId: this.runtime.agentId,
                            content: { text: "", action: "" },
                        },
                        {
                            twitterUserName: this.twitterUsername,
                            currentTweet: `ID: ${tweet.id}\nFrom: ${tweet.name} (@${tweet.username})\nText: ${tweet.text}`,
                        }
                    );

                    const actionContext = composeContext({
                        state: tweetState,
                        template:
                            this.runtime.character.templates
                                ?.twitterActionTemplate ||
                            twitterActionTemplate,
                    });

                    const actionResponse = await generateTweetActions({
                        runtime: this.runtime,
                        context: actionContext,
                        modelClass: ModelClass.SMALL,
                    });

                    if (!actionResponse) {
                        elizaLogger.log(
                            `No valid actions generated for tweet ${tweet.id}`
                        );
                        continue;
                    }
                    processedTimelines.push({
                        tweet: tweet,
                        actionResponse: actionResponse,
                        tweetState: tweetState,
                        roomId: roomId,
                    });
                } catch (error) {
                    elizaLogger.error(
                        `Error processing tweet ${tweet.id}:`,
                        error
                    );
                    continue;
                }
            }

            const sortProcessedTimeline = (arr: typeof processedTimelines) => {
                return arr.sort((a, b) => {
                    // Count the number of true values in the actionResponse object
                    const countTrue = (obj: typeof a.actionResponse) =>
                        Object.values(obj).filter(Boolean).length;

                    const countA = countTrue(a.actionResponse);
                    const countB = countTrue(b.actionResponse);

                    // Primary sort by number of true values
                    if (countA !== countB) {
                        return countB - countA;
                    }

                    // Secondary sort by the "like" property
                    if (a.actionResponse.like !== b.actionResponse.like) {
                        return a.actionResponse.like ? -1 : 1;
                    }

                    // Tertiary sort keeps the remaining objects with equal weight
                    return 0;
                });
            };
            // Sort the timeline based on the action decision score,
            // then slice the results according to the environment variable to limit the number of actions per cycle.
            const sortedTimelines = sortProcessedTimeline(
                processedTimelines
            ).slice(0, maxActionsProcessing);

            return this.processTimelineActions(sortedTimelines); // Return results array to indicate completion
        } catch (error) {
            elizaLogger.error("Error in processTweetActions:", error);
            throw error;
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Processes a list of timelines by executing the corresponding tweet actions.
     * Each timeline includes the tweet, action response, tweet state, and room context.
     * Results are returned for tracking completed actions.
     *
     * @param timelines - Array of objects containing tweet details, action responses, and state information.
     * @returns A promise that resolves to an array of results with details of executed actions.
     */
    private async processTimelineActions(
        timelines: {
            tweet: Tweet;
            actionResponse: ActionResponse;
            tweetState: State;
            roomId: UUID;
        }[]
    ): Promise<
        {
            tweetId: string;
            actionResponse: ActionResponse;
            executedActions: string[];
        }[]
    > {
        const results = [];
        for (const timeline of timelines) {
            const { actionResponse, tweetState, roomId, tweet } = timeline;
            try {
                const executedActions: string[] = [];
                // Execute actions
                if (actionResponse.like) {
                    if (this.isDryRun) {
                        elizaLogger.info(
                            `Dry run: would have liked tweet ${tweet.id}`
                        );
                        executedActions.push("like (dry run)");
                    } else {
                        try {
                            await this.client.twitterClient.likeTweet(tweet.id);
                            executedActions.push("like");
                            elizaLogger.log(`Liked tweet ${tweet.id}`);
                        } catch (error) {
                            elizaLogger.error(
                                `Error liking tweet ${tweet.id}:`,
                                error
                            );
                        }
                    }
                }

                if (actionResponse.retweet) {
                    if (this.isDryRun) {
                        elizaLogger.info(
                            `Dry run: would have retweeted tweet ${tweet.id}`
                        );
                        executedActions.push("retweet (dry run)");
                    } else {
                        try {
                            await this.client.twitterClient.retweet(tweet.id);
                            executedActions.push("retweet");
                            elizaLogger.log(`Retweeted tweet ${tweet.id}`);
                        } catch (error) {
                            elizaLogger.error(
                                `Error retweeting tweet ${tweet.id}:`,
                                error
                            );
                        }
                    }
                }

                if (actionResponse.quote) {
                    try {
                        // Build conversation thread for context
                        const thread = await buildConversationThread(
                            tweet,
                            this.client
                        );
                        const formattedConversation = thread
                            .map(
                                (t) =>
                                    `@${t.username} (${new Date(
                                        t.timestamp * 1000
                                    ).toLocaleString()}): ${t.text}`
                            )
                            .join("\n\n");

                        // Generate image descriptions if present
                        const imageDescriptions = [];
                        if (tweet.photos?.length > 0) {
                            elizaLogger.log(
                                "Processing images in tweet for context"
                            );
                            for (const photo of tweet.photos) {
                                const description = await this.runtime
                                    .getService<IImageDescriptionService>(
                                        ServiceType.IMAGE_DESCRIPTION
                                    )
                                    .describeImage(photo.url);
                                imageDescriptions.push(description);
                            }
                        }

                        // Handle quoted tweet if present
                        let quotedContent = "";
                        if (tweet.quotedStatusId) {
                            try {
                                const quotedTweet =
                                    await this.client.twitterClient.getTweet(
                                        tweet.quotedStatusId
                                    );
                                if (quotedTweet) {
                                    quotedContent = `\nQuoted Tweet from @${quotedTweet.username}:\n${quotedTweet.text}`;
                                }
                            } catch (error) {
                                elizaLogger.error(
                                    "Error fetching quoted tweet:",
                                    error
                                );
                            }
                        }

                        // Compose rich state with all context
                        const enrichedState = await this.runtime.composeState(
                            {
                                userId: this.runtime.agentId,
                                roomId: stringToUuid(
                                    tweet.conversationId +
                                        "-" +
                                        this.runtime.agentId
                                ),
                                agentId: this.runtime.agentId,
                                content: {
                                    text: tweet.text,
                                    action: "QUOTE",
                                },
                            },
                            {
                                twitterUserName: this.twitterUsername,
                                currentPost: `From @${tweet.username}: ${tweet.text}`,
                                formattedConversation,
                                imageContext:
                                    imageDescriptions.length > 0
                                        ? `\nImages in Tweet:\n${imageDescriptions
                                              .map(
                                                  (desc, i) =>
                                                      `Image ${i + 1}: ${desc}`
                                              )
                                              .join("\n")}`
                                        : "",
                                quotedContent,
                            }
                        );

                        const quoteContent = await this.generateTweetContent(
                            enrichedState,
                            {
                                template:
                                    this.runtime.character.templates
                                        ?.twitterMessageHandlerTemplate ||
                                    twitterMessageHandlerTemplate,
                            }
                        );

                        if (!quoteContent) {
                            elizaLogger.error(
                                "Failed to generate valid quote tweet content"
                            );
                            return;
                        }

                        elizaLogger.log(
                            "Generated quote tweet content:",
                            quoteContent
                        );
                        // Check for dry run mode
                        if (this.isDryRun) {
                            elizaLogger.info(
                                `Dry run: A quote tweet for tweet ID ${tweet.id} would have been posted with the following content: "${quoteContent}".`
                            );
                            executedActions.push("quote (dry run)");
                        } else {
                            // Send the tweet through request queue
                            const result = await this.client.requestQueue.add(
                                async () =>
                                    await this.client.twitterClient.sendQuoteTweet(
                                        quoteContent,
                                        tweet.id
                                    )
                            );

                            const body = await result.json();

                            if (
                                body?.data?.create_tweet?.tweet_results?.result
                            ) {
                                elizaLogger.log(
                                    "Successfully posted quote tweet"
                                );
                                executedActions.push("quote");

                                // Cache generation context for debugging
                                await this.runtime.cacheManager.set(
                                    `twitter/quote_generation_${tweet.id}.txt`,
                                    `Context:\n${enrichedState}\n\nGenerated Quote:\n${quoteContent}`
                                );
                            } else {
                                elizaLogger.error(
                                    "Quote tweet creation failed:",
                                    body
                                );
                            }
                        }
                    } catch (error) {
                        elizaLogger.error(
                            "Error in quote tweet generation:",
                            error
                        );
                    }
                }

                if (actionResponse.reply) {
                    try {
                        await this.handleTextOnlyReply(
                            tweet,
                            tweetState,
                            executedActions
                        );
                    } catch (error) {
                        elizaLogger.error(
                            `Error replying to tweet ${tweet.id}:`,
                            error
                        );
                    }
                }

                // Add these checks before creating memory
                await this.runtime.ensureRoomExists(roomId);
                await this.runtime.ensureUserExists(
                    stringToUuid(tweet.userId),
                    tweet.username,
                    tweet.name,
                    "twitter"
                );
                await this.runtime.ensureParticipantInRoom(
                    this.runtime.agentId,
                    roomId
                );

                if (!this.isDryRun) {
                    // Then create the memory
                    await this.runtime.messageManager.createMemory({
                        id: stringToUuid(tweet.id + "-" + this.runtime.agentId),
                        userId: stringToUuid(tweet.userId),
                        content: {
                            text: tweet.text,
                            url: tweet.permanentUrl,
                            source: "twitter",
                            action: executedActions.join(","),
                        },
                        agentId: this.runtime.agentId,
                        roomId,
                        embedding: getEmbeddingZeroVector(),
                        createdAt: tweet.timestamp * 1000,
                    });
                }

                results.push({
                    tweetId: tweet.id,
                    actionResponse: actionResponse,
                    executedActions,
                });
            } catch (error) {
                elizaLogger.error(`Error processing tweet ${tweet.id}:`, error);
                continue;
            }
        }

        return results;
    }

    /**
     * Handles text-only replies to tweets. If isDryRun is true, only logs what would
     * have been replied without making API calls.
     */
    private async handleTextOnlyReply(
        tweet: Tweet,
        tweetState: any,
        executedActions: string[]
    ) {
        try {
            // Build conversation thread for context
            const thread = await buildConversationThread(tweet, this.client);
            const formattedConversation = thread
                .map(
                    (t) =>
                        `@${t.username} (${new Date(
                            t.timestamp * 1000
                        ).toLocaleString()}): ${t.text}`
                )
                .join("\n\n");

            // Generate image descriptions if present
            const imageDescriptions = [];
            if (tweet.photos?.length > 0) {
                elizaLogger.log("Processing images in tweet for context");
                for (const photo of tweet.photos) {
                    const description = await this.runtime
                        .getService<IImageDescriptionService>(
                            ServiceType.IMAGE_DESCRIPTION
                        )
                        .describeImage(photo.url);
                    imageDescriptions.push(description);
                }
            }

            // Handle quoted tweet if present
            let quotedContent = "";
            if (tweet.quotedStatusId) {
                try {
                    const quotedTweet =
                        await this.client.twitterClient.getTweet(
                            tweet.quotedStatusId
                        );
                    if (quotedTweet) {
                        quotedContent = `\nQuoted Tweet from @${quotedTweet.username}:\n${quotedTweet.text}`;
                    }
                } catch (error) {
                    elizaLogger.error("Error fetching quoted tweet:", error);
                }
            }

            // Compose rich state with all context
            const enrichedState = await this.runtime.composeState(
                {
                    userId: this.runtime.agentId,
                    roomId: stringToUuid(
                        tweet.conversationId + "-" + this.runtime.agentId
                    ),
                    agentId: this.runtime.agentId,
                    content: { text: tweet.text, action: "" },
                },
                {
                    twitterUserName: this.twitterUsername,
                    currentPost: `From @${tweet.username}: ${tweet.text}`,
                    formattedConversation,
                    imageContext:
                        imageDescriptions.length > 0
                            ? `\nImages in Tweet:\n${imageDescriptions
                                  .map((desc, i) => `Image ${i + 1}: ${desc}`)
                                  .join("\n")}`
                            : "",
                    quotedContent,
                }
            );

            // Generate and clean the reply content
            const replyText = await this.generateTweetContent(enrichedState, {
                template:
                    this.runtime.character.templates
                        ?.twitterMessageHandlerTemplate ||
                    twitterMessageHandlerTemplate,
            });

            if (!replyText) {
                elizaLogger.error("Failed to generate valid reply content");
                return;
            }

            if (this.isDryRun) {
                elizaLogger.info(
                    `Dry run: reply to tweet ${tweet.id} would have been: ${replyText}`
                );
                executedActions.push("reply (dry run)");
                return;
            }

            elizaLogger.debug("Final reply text to be sent:", replyText);

            let result;

            if (replyText.length > DEFAULT_MAX_TWEET_LENGTH) {
                result = await this.handleNoteTweet(
                    this.client,
                    replyText,
                    tweet.id
                );
            } else {
                result = await this.sendStandardTweet(
                    this.client,
                    replyText,
                    tweet.id
                );
            }

            if (result) {
                elizaLogger.log("Successfully posted reply tweet");
                executedActions.push("reply");

                // Cache generation context for debugging
                await this.runtime.cacheManager.set(
                    `twitter/reply_generation_${tweet.id}.txt`,
                    `Context:\n${enrichedState}\n\nGenerated Reply:\n${replyText}`
                );
            } else {
                elizaLogger.error("Tweet reply creation failed");
            }
        } catch (error) {
            elizaLogger.error("Error in handleTextOnlyReply:", error);
        }
    }

    async stop() {
        this.stopProcessingActions = true;
    }

    private async sendForApproval(
        tweetTextForPosting: string,
        roomId: UUID,
        rawTweetContent: string
    ): Promise<string | null> {
        try {
            const embed = {
                title: "New Tweet Pending Approval",
                description: tweetTextForPosting,
                fields: [
                    {
                        name: "Character",
                        value: this.client.profile.username,
                        inline: true,
                    },
                    {
                        name: "Length",
                        value: tweetTextForPosting.length.toString(),
                        inline: true,
                    },
                ],
                footer: {
                    text: "Reply with '👍' to post or '❌' to discard, This will automatically expire and remove after 24 hours if no response received",
                },
                timestamp: new Date().toISOString(),
            };

            const channel = await this.discordClientForApproval.channels.fetch(
                this.discordApprovalChannelId
            );

            if (!channel || !(channel instanceof TextChannel)) {
                throw new Error("Invalid approval channel");
            }

            const message = await channel.send({ embeds: [embed] });

            // Store the pending tweet
            const pendingTweetsKey = `twitter/${this.client.profile.username}/pendingTweet`;
            const currentPendingTweets =
                (await this.runtime.cacheManager.get<PendingTweet[]>(
                    pendingTweetsKey
                )) || [];
            // Add new pending tweet
            currentPendingTweets.push({
                tweetTextForPosting,
                roomId,
                rawTweetContent,
                discordMessageId: message.id,
                channelId: this.discordApprovalChannelId,
                timestamp: Date.now(),
            });

            // Store updated array
            await this.runtime.cacheManager.set(
                pendingTweetsKey,
                currentPendingTweets
            );

            return message.id;
        } catch (error) {
            elizaLogger.error(
                "Error Sending Twitter Post Approval Request:",
                error
            );
            return null;
        }
    }

    private async checkApprovalStatus(
        discordMessageId: string
    ): Promise<PendingTweetApprovalStatus> {
        try {
            // Fetch message and its replies from Discord
            const channel = await this.discordClientForApproval.channels.fetch(
                this.discordApprovalChannelId
            );

            elizaLogger.log(`channel ${JSON.stringify(channel)}`);

            if (!(channel instanceof TextChannel)) {
                elizaLogger.error("Invalid approval channel");
                return "PENDING";
            }

            // Fetch the original message and its replies
            const message = await channel.messages.fetch(discordMessageId);

            // Look for thumbs up reaction ('👍')
            const thumbsUpReaction = message.reactions.cache.find(
                (reaction) => reaction.emoji.name === "👍"
            );

            // Look for reject reaction ('❌')
            const rejectReaction = message.reactions.cache.find(
                (reaction) => reaction.emoji.name === "❌"
            );

            // Check if the reaction exists and has reactions
            if (rejectReaction) {
                const count = rejectReaction.count;
                if (count > 0) {
                    return "REJECTED";
                }
            }

            // Check if the reaction exists and has reactions
            if (thumbsUpReaction) {
                // You might want to check for specific users who can approve
                // For now, we'll return true if anyone used thumbs up
                const count = thumbsUpReaction.count;
                if (count > 0) {
                    return "APPROVED";
                }
            }

            return "PENDING";
        } catch (error) {
            elizaLogger.error("Error checking approval status:", error);
            return "PENDING";
        }
    }

    private async cleanupPendingTweet(discordMessageId: string) {
        const pendingTweetsKey = `twitter/${this.client.profile.username}/pendingTweet`;
        const currentPendingTweets =
            (await this.runtime.cacheManager.get<PendingTweet[]>(
                pendingTweetsKey
            )) || [];

        // Remove the specific tweet
        const updatedPendingTweets = currentPendingTweets.filter(
            (tweet) => tweet.discordMessageId !== discordMessageId
        );

        if (updatedPendingTweets.length === 0) {
            await this.runtime.cacheManager.delete(pendingTweetsKey);
        } else {
            await this.runtime.cacheManager.set(
                pendingTweetsKey,
                updatedPendingTweets
            );
        }
    }

    private async handlePendingTweet() {
        elizaLogger.log("Checking Pending Tweets...");
        const pendingTweetsKey = `twitter/${this.client.profile.username}/pendingTweet`;
        const pendingTweets =
            (await this.runtime.cacheManager.get<PendingTweet[]>(
                pendingTweetsKey
            )) || [];

        for (const pendingTweet of pendingTweets) {
            // Check if tweet is older than 24 hours
            const isExpired =
                Date.now() - pendingTweet.timestamp > 24 * 60 * 60 * 1000;

            if (isExpired) {
                elizaLogger.log("Pending tweet expired, cleaning up");

                // Notify on Discord about expiration
                try {
                    const channel =
                        await this.discordClientForApproval.channels.fetch(
                            pendingTweet.channelId
                        );
                    if (channel instanceof TextChannel) {
                        const originalMessage = await channel.messages.fetch(
                            pendingTweet.discordMessageId
                        );
                        await originalMessage.reply(
                            "This tweet approval request has expired (24h timeout)."
                        );
                    }
                } catch (error) {
                    elizaLogger.error(
                        "Error sending expiration notification:",
                        error
                    );
                }

                await this.cleanupPendingTweet(pendingTweet.discordMessageId);
                return;
            }

            // Check approval status
            elizaLogger.log("Checking approval status...");
            const approvalStatus: PendingTweetApprovalStatus =
                await this.checkApprovalStatus(pendingTweet.discordMessageId);

            if (approvalStatus === "APPROVED") {
                elizaLogger.log("Tweet Approved, Posting");
                await this.postTweet(
                    this.runtime,
                    this.client,
                    pendingTweet.tweetTextForPosting,
                    pendingTweet.roomId,
                    pendingTweet.rawTweetContent,
                    this.twitterUsername
                );

                // Notify on Discord about posting
                try {
                    const channel =
                        await this.discordClientForApproval.channels.fetch(
                            pendingTweet.channelId
                        );
                    if (channel instanceof TextChannel) {
                        const originalMessage = await channel.messages.fetch(
                            pendingTweet.discordMessageId
                        );
                        await originalMessage.reply(
                            "Tweet has been posted successfully! ✅"
                        );
                    }
                } catch (error) {
                    elizaLogger.error(
                        "Error sending post notification:",
                        error
                    );
                }

                await this.cleanupPendingTweet(pendingTweet.discordMessageId);
            } else if (approvalStatus === "REJECTED") {
                elizaLogger.log("Tweet Rejected, Cleaning Up");
                await this.cleanupPendingTweet(pendingTweet.discordMessageId);
                // Notify about Rejection of Tweet
                try {
                    const channel =
                        await this.discordClientForApproval.channels.fetch(
                            pendingTweet.channelId
                        );
                    if (channel instanceof TextChannel) {
                        const originalMessage = await channel.messages.fetch(
                            pendingTweet.discordMessageId
                        );
                        await originalMessage.reply(
                            "Tweet has been rejected! ❌"
                        );
                    }
                } catch (error) {
                    elizaLogger.error(
                        "Error sending rejection notification:",
                        error
                    );
                }
            }
        }
    }
}
