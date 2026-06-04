import { elizaLogger } from "@elizaos/core";

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
    sender: 'carbontruth' | 'default' | 'carbonrant';
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
    private apiUrl: string;

    /**
     * Create a new TweetDataSender
     * @param apiUrl - The URL of the API endpoint
     */
    constructor(apiUrl: string = 'http://127.0.0.1:8000/api/tweets/') {
        this.apiUrl = apiUrl;
    }
    /**
     * Send tweet data using an already constructed tweet object
     * @param tweetDataObject - Object containing sender and tweetData fields
     * @returns Promise that resolves with the API response
     */
    async sendTweetObject(tweetDataObject: TweetData): Promise<ApiResponse> {
        try {
            // Validate the structure of the tweet object
            if (!tweetDataObject.sender || !tweetDataObject.tweetData) {
                throw new Error('Invalid tweet data object structure. Must contain sender and tweetData fields.');
            }
            
            // Create a copy of the tweet data to format dates correctly
            const formattedTweetData: TweetData = {
                sender: tweetDataObject.sender,
                tweetData: {
                    ...tweetDataObject.tweetData,
                    // Format date and time to the expected format
                    date: formatDate(tweetDataObject.tweetData.date),
                    time: formatTime(tweetDataObject.tweetData.time)
                }
            };
            
            // Make the API call
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formattedTweetData)
            });

            // Parse the response
            const responseData: ApiResponse = await response.json();
            
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
     */
    async getTweets(sender: 'carbontruth' | 'default' = 'carbontruth'): Promise<TweetDataContent[]> {
        try {
            const response = await fetch(`${this.apiUrl}?sender=${sender}`);
            const data = await response.json();
            
            if (!response.ok) {
                const errorResponse = data as ApiResponse;
                throw new Error(`API error: ${errorResponse.error || response.statusText}`);
            }
            elizaLogger.log('Fetched tweets:', JSON.stringify(data));
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
     */
    async getLatestTweet(sender: 'carbontruth' | 'default' = 'carbontruth'): Promise<TweetDataContent> {
        try {
            const response = await fetch(`${this.apiUrl}/latest?sender=${sender}`);
            const data = await response.json();
            
            if (!response.ok) {
                const errorResponse = data as ApiResponse;
                throw new Error(`API error: ${errorResponse.error || response.statusText}`);
            }
            elizaLogger.log('Fetched tweets:', JSON.stringify(data));
            return data as TweetDataContent;
        } catch (error) {
            console.error('Error getting tweet by ID:', error);
            throw error;
        }
    }

    /**
     * Get list of valid senders
     * @returns Promise that resolves with the list of valid senders
     */
    async getValidSenders(): Promise<string[]> {
        try {
            const response = await fetch(`${this.apiUrl.replace('/tweets', '/senders')}`);
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