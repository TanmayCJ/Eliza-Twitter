import type { IAgentRuntime, UUID } from "@elizaos/core";
import { elizaLogger, generateText, ModelClass } from "@elizaos/core";
import type { ClientBase } from "./base";
import { fetchMediaData } from "./utils";
import type { MediaData } from "./types";
import dotenv from "dotenv";
import Together from "together-ai";
import OpenAI from "openai";

dotenv.config({ path: "../../../../.env" });

/**
 * Interface for tweet information
 */
export interface TweetInfo {
  text: string;
  raw: string;
  username: string;
  mediaData?: MediaData[];
}

const generateImage = true; 
const imageGenerationPercentage = 40;

/**
 * Converts a string to a UUID using a deterministic hashing approach
 * @param runtime The agent runtime
 * @param input String to convert to UUID
 * @returns UUID generated from the input string
 */
export function convertStringToUuid(
  runtime: IAgentRuntime,
  input: string
): UUID {
  // Use a temporary UUID derived from the input string
  // This is a simplified approach - you might need a proper UUID generation method
  return input as UUID;
}

/**
 * Hook handler for Twitter pre-post operations
 */
export class TwitterPrePostHookHandler {
  static generateImageAndContext(arg0: { topic: string; post: { content: any; }; agent: IAgentRuntime; }): { image: any; imageContext: any; } | PromiseLike<{ image: any; imageContext: any; }> {
      throw new Error("Method not implemented.");
  }
  /**
   * Process pre-post hook for tweets
   * @param runtime The agent runtime
   * @param tweetInfo The tweet information
   * @returns Media data if any was processed
   */
  static async processPrePostHook(
    runtime: IAgentRuntime,
    tweetInfo: TweetInfo
  ): Promise<MediaData[] | undefined> {
    try {
      // Check for hook enabled setting
        const hookEnabled = runtime.getSetting("TWITTER_PRE_POST_HOOK_ENABLED");
        //   const hookEnabled = "true"; // For testing purposes, set to true
        
      const agentKey = `${runtime.character.name}/imageUploadData`;
      const agentUploadData = await runtime.cacheManager.get<{ isImg: boolean, imgIds: string[] }>(agentKey);

      if (hookEnabled?.toLowerCase() !== "true" || !agentUploadData.isImg) {
        return tweetInfo.mediaData; // Return existing media data if hook is not enabled
      }

      // Add random chance for image generation (40%)
      if (generateImage && Math.random() * 100 > imageGenerationPercentage) {
        elizaLogger.log(`Random chance determined no image for this tweet (${imageGenerationPercentage}% chance)`);
        return tweetInfo.mediaData; // Skip image generation based on random chance
      }

      // Clone existing media data if any
      let mediaData = tweetInfo.mediaData ? [...tweetInfo.mediaData] : [];

      // const imagePath = runtime.getSetting("TWITTER_IMAGE_PATH");

          const imagePath = await this.fetchWebImage(runtime, tweetInfo.text, tweetInfo);   //TODO: Main image fetching function

        if (imagePath === "NO_IMAGE") {
          return tweetInfo.mediaData; // Return existing media data if no image is relevant
        }

      // Use web URL if provided, otherwise use local file path
      const imageSource = imagePath;

      if (imageSource) {
        elizaLogger.log(
          `Image source detected, will attach image: ${imageSource}`
        );

        // Determine if it's a web URL or local path
        const isWebUrl = imageSource.toLowerCase().startsWith("http");

        // Create media attachment from the image source
        const attachment = {
          url: imageSource,
          contentType: imageSource.toLowerCase().endsWith(".png")
            ? "image/png"
            : imageSource.toLowerCase().endsWith(".jpg") ||
              imageSource.toLowerCase().endsWith(".jpeg")
            ? "image/jpeg"
            : imageSource.toLowerCase().endsWith(".gif")
            ? "image/gif"
            : "image/jpeg", // Default to JPEG
          id: convertStringToUuid(
            runtime,
            `image-${Date.now()}-${Math.random()}`
          ),
          title: "",
          description: isWebUrl ? "Web image" : "Local image",
          source: "pre_post_hook",
          text: "",
        };

        // Convert attachment to MediaData
        try {
          const hookMediaData = await fetchMediaData([attachment]);
          if (hookMediaData && hookMediaData.length > 0) {
            // Append to the mediaData
            mediaData = [...mediaData, ...hookMediaData];
            elizaLogger.log(`Successfully loaded image from ${imageSource}`);
          }
        } catch (mediaError) {
          elizaLogger.error(
            `Error loading image from ${imageSource}:`,
            mediaError
          );
        }
      }

      // Store tweet information in cache for logging/debugging
      await runtime.cacheManager.set(
        `twitter/${tweetInfo.username}/pre_post_hook/${Date.now()}`,
        tweetInfo
      );

      elizaLogger.log("Pre-post hook completed");

      return mediaData.length > 0 ? mediaData : tweetInfo.mediaData;
    } catch (error) {
      elizaLogger.error("Error in pre-post hook:", error);
      return tweetInfo.mediaData; // Return original media data on error
    }
  }

  /**
   * Fetch a web image related to tweet content
   * @param runtime The agent runtime
   * @param tweetText The text content of the tweet
   * @param tweetInfo Additional tweet information
   * @returns URL of the fetched image or "NO_IMAGE" if no relevant image found
   */
  static async fetchWebImage(
    runtime: IAgentRuntime,
    tweetText: string,
    tweetInfo: TweetInfo
  ): Promise<string> {
      try {
        
          const PEXEL_API_KEY = runtime.getSetting("PEXEL_API_KEY") as string;
          if (!PEXEL_API_KEY) {
                elizaLogger.error("PEXEL_API_KEY is not defined in the environment variables.");
                throw new Error("PEXEL_API_KEY is not defined in the environment variables.");
        }
          
          const relevanceCheckTemplate = `
            Tweet: ${tweetText}

            Determine if attaching an image would be relevant and meaningful for this tweet.

            #rules
            - Respond with only one word: "yes" or "no".
            - "yes" if an image would enhance or visually support the tweet's message.
            - "no" if the tweet is abstract, textual, conversational, or better without an image.
            - Do not include any explanation, summary, or additional text.
            `;

            elizaLogger.log("Checking relevance of the image: " + relevanceCheckTemplate);
            const imageRelevanceCheck = await generateText({
                runtime,
                context: relevanceCheckTemplate,
                modelClass: ModelClass.SMALL,
                stop: ["\n"],
            });    
              
          if (imageRelevanceCheck.toLowerCase() !== "yes") {
              elizaLogger.log("Image relevance check failed, no image will be fetched.");
              return "NO_IMAGE"; // Return a placeholder if no image is relevant.
          }
          
          const imageKeyWordTemplate = `
          Tweet: ${tweetText}
          
          Imagine the most visually striking and meaningful scene that this tweet could inspire.
          
          Extract a single, imaginative visual concept as a **two-word keyword or phrase**, even if not explicitly stated in the tweet.
          
          #rules
          - Return exactly two words only.
          - Words must be strong visual nouns (e.g., "volcano", "satellite", "ocean", "robot").
          - You may interpret the tweet loosely, metaphorically, or symbolically to form the visual.
          - Avoid quoting or copying phrases from the tweet.
          - Abstract terms, verbs, or adjectives are only allowed if paired with a concrete visual noun (e.g., "glowing cave" is valid).
          - Convert compound or technical terms into their core visual parts (e.g., "urbanization" → "cityscape", "telecommunication tower" → "radio tower").
          - Avoid explanations, punctuation, or repeating parts of this prompt.
          - Use lowercase unless a proper noun is required.
          - If anything green is required, use just "greenery" .
          - If its realted to forest, use just "forest" .
          `;          
            
            const imageKeyWord = await generateText({
                runtime,
                context: imageKeyWordTemplate,
                modelClass: ModelClass.SMALL,
                stop: ["\n"],
            });     
            elizaLogger.log("Generating image keyword from tweet text...");
            elizaLogger.log("Image keyword:", imageKeyWord);

            const response = await fetch(`https://api.pexels.com/v1/search?query=${encodeURIComponent(imageKeyWord)}&per_page=1`, {
                headers: {
                  Authorization: PEXEL_API_KEY,
                },
              });
            
              if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.status}`);
              }
            
              const data = await response.json();
              if (data.photos.length === 0) {
                elizaLogger.log("No images found on Pexels, trying OpenAI image generation");
                return this.generateImageWithTogether(runtime, tweetText, tweetInfo);
           }
        
           const photos = data.photos; // Array of photo objects
            const agentKey = `${runtime.character.name}/imageUploadData`;
            let agentUploadData = await runtime.cacheManager.get<{ isImg: boolean, imgIds: string[] }>(agentKey);

            // Initialize if missing
            if (!agentUploadData) {
              agentUploadData = { isImg: true, imgIds: [] };
            }

            let selectedImageUrl: string | null = null;
            let selectedImageId: string | null = null;

            // Loop through photos to find an unused image
            for (const photo of photos) {
              const imageUrl = photo.src.original;
              const match = imageUrl.match(/\/photos\/(\d+)\//);
              const imageId = match ? match[1] : null;

              elizaLogger.log("Image ID:", imageId);

              if (imageId && !agentUploadData.imgIds.includes(imageId)) {

                const check = await this.fetchImageValidation(
                  runtime,
                  tweetText,
                  imageUrl
                );
                if (!check) {
                  elizaLogger.log("Image is not relevant, skipping...");
                  continue; // Skip this image if not relevant
                }
                selectedImageUrl = imageUrl;
                selectedImageId = imageId;
                break;
              }
        }

        if (!selectedImageUrl) {
          elizaLogger.log("No new image found or image not relevant, using OpenAI image generation");
          return this.generateImageWithTogether(runtime, tweetText, tweetInfo);
        }

        
        if (agentUploadData.imgIds.length > 100) {
          agentUploadData.imgIds = agentUploadData.imgIds.slice(-100);
        }

        if (selectedImageId) {
          agentUploadData.imgIds.push(selectedImageId);
          await runtime.cacheManager.set(agentKey, agentUploadData);
        }

        elizaLogger.log("Selected image URL:", selectedImageUrl);
        return selectedImageUrl as string; // Return the selected image URL or a placeholder if none found
        
      } catch (error) {
        elizaLogger.error("Error fetching image:", error);
        // Try OpenAI as a fallback if Pexels fails
        try {
          elizaLogger.log("Attempting OpenAI image generation as fallback");
          return await this.generateImageWithTogether(runtime, tweetText, tweetInfo);
        } catch (openaiError) {
          elizaLogger.error("OpenAI image generation fallback also failed:", openaiError);
          return "NO_IMAGE";
        }
    }
  }
  
  /**
   * Validates if an image is relevant to a tweet
   * @param runtime The agent runtime
   * @param tweetText The text content of the tweet
   * @param imageUrl URL of the image to validate
   * @returns Boolean indicating if the image is relevant
   */
  static async fetchImageValidation(
    runtime: IAgentRuntime,
    tweetText: string,
    imageUrl: string,
  ): Promise<boolean> {
    try {
      const imageDescPromptTemplate = `
        Here is the link of the image: ${imageUrl}

        Here is the tweet: ${tweetText}

        Now answer in yes or no, just one word, whether this image is a good representation of the mentioned tweet. The image does not need to represent the tweet exactly or literally, but it must be related to the tweet in some meaningful way and relevant to the message being conveyed. Is it okay to post the tweet with the given image?
      `;

      const imageDescPrompt = await generateText({
        runtime,
        context: imageDescPromptTemplate,
        modelClass: ModelClass.SMALL,
        stop: ["\n"],
      }) as string;

      elizaLogger.log("Image description prompt:", imageDescPrompt as string);
      if (imageDescPrompt.toLowerCase() !== "yes") {
        return false; // Return false if the image is not relevant
      }
      return true; // Return true if the image is relevant

    } catch (error) {
      elizaLogger.error("Error generating image description:", error as string);
      return false; // Return false if validation fails
    }
  }
  
  /**
   * Generates an image based on tweet content using Together AI
   * @param runtime The agent runtime
   * @param tweetText The text content to generate an image for
   * @param tweetInfo Additional tweet information
   * @param imageType The type of image to generate (chart, infographic, etc.)
   * @returns URL to the generated image or "NO_IMAGE" if generation fails
   */
  static async generateImageWithTogether(
    runtime: IAgentRuntime,
    tweetText: string,
    tweetInfo: TweetInfo,
    imageType: 'chart' | 'infographic' | 'photo' = 'photo',
  ): Promise<string> {
    try {
        const TOGETHER_API_KEY = runtime.getSetting("TOGETHER_API_KEY") as string;
        if (!TOGETHER_API_KEY) {
            throw new Error("TOGETHER_API_KEY is not defined in the environment variables.");
      }
      const together = new Together({
        apiKey: TOGETHER_API_KEY,
      });

      const imageGenerationPromptTemplate = `Given the following tweet, write a concise and creative prompt for generating a realistic image that captures the tweet's mood, theme, and key details. Use vivid and imaginative language while staying true to the tweet's context. And Dont include watermarks. Tweet: ${tweetText}`;
      
      elizaLogger.log("Image generation prompt:", imageGenerationPromptTemplate as string);

      const imageGenerationPrompt = await generateText({
        runtime,
        context: imageGenerationPromptTemplate,
        modelClass: ModelClass.MEDIUM,
        stop: ["\n"],
      }) as string;

      const response = await together.images.create({
        prompt: imageGenerationPrompt,
        model: "black-forest-labs/FLUX.1-schnell",
        steps: 4,
      });
      if (!response || !response.data || response.data.length === 0) {
        throw new Error("No image generated");
      }
      // @ts-ignore
      const imageUrl = response.data[0].url;
      return imageUrl;
    } catch (error) {
      elizaLogger.error("Error generating image:", error as string);
      return "NO_IMAGE"; // Return a placeholder if image generation fails
    }
  }

  /**
   * Generates an image using OpenAI DALL-E model based on tweet content
   * @param runtime The agent runtime
   * @param tweetText The text content to generate an image for
   * @param tweetInfo Additional tweet information
   * @returns URL to the generated image or "NO_IMAGE" if generation fails
   */
  static async generateImageWithOpenAI(
    runtime: IAgentRuntime,
    tweetText: string,
    tweetInfo: TweetInfo,
  ): Promise<string> {
    try {
      const OPENAI_API_KEY = runtime.getSetting("OPENAI_API_KEY") as string;
      if (!OPENAI_API_KEY) {
        elizaLogger.error("OPENAI_API_KEY is not defined in the environment variables.");
        throw new Error("OPENAI_API_KEY is not defined in the environment variables.");
      }
      
      const openai = new OpenAI({
        apiKey: OPENAI_API_KEY,
      });

      const imageGenerationPromptTemplate = `Given the following tweet, write a concise and creative prompt for generating a realistic image that captures the tweet's mood, theme, and key details. Use vivid and imaginative language while staying true to the tweet's context. Avoid requesting text or watermarks in the image. Tweet: ${tweetText}`;
      
      elizaLogger.log("OpenAI image generation prompt template:", imageGenerationPromptTemplate);

      const imageGenerationPrompt = await generateText({
        runtime,
        context: imageGenerationPromptTemplate,
        modelClass: ModelClass.MEDIUM,
        stop: ["\n"],
      }) as string;

      elizaLogger.log("OpenAI image generation prompt:", imageGenerationPrompt);

      // Generate image with OpenAI
      const response = await openai.images.generate({
        model: "dall-e-3", // Using DALL-E 3 for high-quality images
        prompt: imageGenerationPrompt as string,
        size: "1024x1024", // Standard size
        quality: "standard",
        n: 1, // Generate one image
      });

      if (!response || !response.data || response.data.length === 0) {
        throw new Error("No image generated by OpenAI");
      }
      
      const imageUrl = response.data[0].url;
      if (!imageUrl) {
        throw new Error("No image URL returned by OpenAI");
      }
      
      elizaLogger.log("OpenAI image URL:", imageUrl);
      return imageUrl;
    } catch (error) {
      elizaLogger.error("Error generating image with OpenAI:", error);
      return "NO_IMAGE"; // Return a placeholder if image generation fails
    }
  }
}
