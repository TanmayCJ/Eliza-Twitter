import { elizaLogger } from "@elizaos/core";

import { IAgentRuntime } from "@elizaos/core";
/**
 * Tweet data nested interface matching the expected structure
 */
export interface TweetDataContent {
    tweetID: string;
    date: string; // Format: YYYY-MM-DD
    time: string; // Format: HH:MM:SS
    tweetLnk: string
    content: string;
    hashtags?: string[]; // Optional
    imageUrl?: string[]; // Optional
}

/**
 * Full tweet data structure with sender and nested tweetData
 */
export interface TweetData {
    sender: 'carbontruth' | 'default';
    tweetData: TweetDataContent;
}

/**
 * API response interface
 */
export interface ApiResponse {
    message?: string;
    tweet?: TweetDataContent;
    id?: number;
    error?: string;
    valid_senders?: string[];
    [key: string]: any;
}

/**
 * Helper function to format dates to the required format
 * @param dateInput - Date string in various formats or Date object
 * @returns Formatted date string in YYYY-MM-DD format
 */
function formatDate(dateInput: string | Date): string {
    const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
        throw new Error(`Invalid date: ${dateInput}`);
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

/**
 * Helper function to format time to the required format
 * @param timeInput - Time string or Date object
 * @returns Formatted time string in HH:MM:SS format
 */
function formatTime(timeInput: string | Date): string {
    // If it's already in HH:MM:SS format, return it
    if (typeof timeInput === 'string' && /^\d{2}:\d{2}:\d{2}$/.test(timeInput)) {
        return timeInput;
    }

    const date = timeInput instanceof Date ? timeInput : new Date(timeInput);

    if (isNaN(date.getTime())) {
        throw new Error(`Invalid time: ${timeInput}`);
    }

    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return `${hours}:${minutes}:${seconds}`; // Always 24-hour format
}

/**
 * TweetDataSender class for sending tweet data to the Flask API
 */
export class TweetDataSender {
    private apiUrl: string;    /**
     * Create a new TweetDataSender
     * @param apiUrl - The URL of the API endpoint
     */
    constructor(apiUrl: string = 'http://127.0.0.1:8000/api/tweets/') {
        this.apiUrl = apiUrl;
    }/**
     * Send tweet data using an already constructed tweet object
     * @param tweetDataObject - Object containing sender and tweetData fields OR the new format with tweet_id, tweet_link, etc.
     * @returns Promise that resolves with the API response
     */
    async sendTweetObject(tweetDataObject: any): Promise<ApiResponse> {        try {
            let formattedTweetData: any;
            
            // Check if incoming data is in the new format (has tweet_id instead of tweetData)
            if (tweetDataObject.tweet_id && !tweetDataObject.tweetData) {
                // Already in the new format, just validate and use it
                if (!tweetDataObject.sender || !tweetDataObject.tweet_id || !tweetDataObject.content || !tweetDataObject.tweet_link) {
                    throw new Error('Invalid tweet data object structure. Must contain sender, tweet_id, content, and tweet_link fields.');
                }
                
                formattedTweetData = {
                    sender: tweetDataObject.sender,
                    tweet_id: tweetDataObject.tweet_id,
                    content: tweetDataObject.content,
                    tweet_link: tweetDataObject.tweet_link,
                    hashtags: tweetDataObject.hashtags || [],
                    image_urls: tweetDataObject.image_urls || []
                };
            } else {
                // Handle original format: convert { sender, tweetData: { tweetID, date, time, ... } } to new format
                if (!tweetDataObject.sender || !tweetDataObject.tweetData) {
                    throw new Error('Invalid tweet data object structure. Must contain sender and tweetData fields.');
                }
                
                // Convert old format to new format
                formattedTweetData = {
                    sender: tweetDataObject.sender,
                    tweet_id: tweetDataObject.tweetData.tweetID,
                    content: tweetDataObject.tweetData.content,
                    tweet_link: tweetDataObject.tweetData.tweetLnk,
                    hashtags: tweetDataObject.tweetData.hashtags || [],
                    image_urls: tweetDataObject.tweetData.imageUrl || []
                };
            }
              // Make the API call
            elizaLogger.log('Sending tweet object to:', this.apiUrl);
            elizaLogger.log('Request payload:', JSON.stringify(formattedTweetData, null, 2));
            
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formattedTweetData)
            });            elizaLogger.log('Response status:', response.status);
            elizaLogger.log('Response status text:', response.statusText);
            
            // Get the raw response text first
            const responseText = await response.text();
            elizaLogger.log('Raw response text:', responseText);
            
            // Try to parse as JSON
            let responseData: ApiResponse;
            try {
                responseData = JSON.parse(responseText);
                elizaLogger.log('Parsed response data:', responseData);
            } catch (parseError) {
                elizaLogger.error('Failed to parse response as JSON:', parseError);
                elizaLogger.error('Response was:', responseText.substring(0, 500));
                throw new Error(`API returned non-JSON response: ${responseText.substring(0, 200)}`);
            }
            
            if (!response.ok) {
                throw new Error(`API error: ${responseData.error || response.statusText}`);
            }
            
            return responseData;
        } catch (error) {
            console.error('Error sending tweet object:', error);
            throw error;
        }
    }

    /**
     * Get all tweets from a specific sender
     * @param sender - The sender identifier
     * @returns Promise that resolves with array of tweets
     */    async getTweets(sender: 'carbontruth' | 'default' = 'carbontruth'): Promise<TweetDataContent[]> {
        try {
            const response = await fetch(`${this.apiUrl}?sender=${sender}`);
            const data = await response.json();
            
            if (!response.ok) {
                const errorResponse = data as ApiResponse;
                throw new Error(`API error: ${errorResponse.error || response.statusText}`);
            }
            
            return data as TweetDataContent[];
        } catch (error) {
            console.error('Error getting tweets:', error);
            throw error;
        }
    }

    /**
     * Get a specific tweet by ID
     * @param tweetID - The tweet ID to retrieve
     * @param sender - The sender identifier
     * @returns Promise that resolves with the tweet data
     */    async getTweetById(tweetID: string, sender: 'carbontruth' | 'default' = 'carbontruth'): Promise<TweetDataContent> {
        try {
            const response = await fetch(`${this.apiUrl}${tweetID}/?sender=${sender}`);
            const data = await response.json();
            
            if (!response.ok) {
                const errorResponse = data as ApiResponse;
                throw new Error(`API error: ${errorResponse.error || response.statusText}`);
            }
            
            return data as TweetDataContent;
        } catch (error) {
            console.error('Error getting tweet by ID:', error);
            throw error;
        }
    }

    /**
     * Get list of valid senders
     * @returns Promise that resolves with the list of valid senders
     */    async getValidSenders(): Promise<string[]> {
        try {
            const response = await fetch(`${this.apiUrl.replace('/tweets/', '/senders/')}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }
            
            return data.valid_senders as string[];
        } catch (error) {
            console.error('Error getting valid senders:', error);
            throw error;
        }
    }
}