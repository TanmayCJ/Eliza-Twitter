import {
  IAgentRuntime,
  Memory,
  ModelClass,
  elizaLogger,
  generateText,
  addHeader,
  Provider,
  ServiceType,
} from "@elizaos/core";
import dotenv from "dotenv";

// import { GoogleGenAI } from "@google/genai";

import { OpenAI } from "openai";
import { json } from "stream/consumers";

dotenv.config({ path: '../../../.env' });

interface NewsApiResponse {
  totalResults: number;
  articles: any[];
}

interface NewsUploadData {
  isNews: boolean;
  lastUpdatedNews: string;
}

interface ImageUploadData {
  isImg: boolean;
  imgIds: string[];
}

// Expected tweet response format:
// {
//   id: number;
//   content: string;
//   hashtags: string[];
//   bot: string;
//   category: string;
//   url: string;
//   when_to_post: string;
//   created_at: string;
//   is_posted: boolean;
//   posted_tweet_link: string | null;
// }

class NewsService {
  private readonly API_KEY_NEWS: string;
  private readonly API_KEY_GNEWS: string;
  private readonly API_KEY_TINYURL: string;
  private readonly API_KEY_GEMINI: string;
  private readonly API_KEY_OPENAI: string;
  private readonly BASE_URL_NEWS: string = "https://newsapi.org/v2/everything";
  private readonly BASE_URL_GNEWS: string = "https://gnews.io/api/v4/top-headlines";
  private readonly BASE_URL_GEMINI: string = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent";
  private readonly COUNTRIES: string[] = ["US", "CA"]; // us, ca, uk, au, de, fr, in, it, jp, mx, nl, no, ru, se, sg, za
  
  private params: Record<string, string | number | undefined>;

  constructor() {
    this.API_KEY_NEWS = process.env.NEWS_API_KEY as string;
    this.API_KEY_GNEWS = process.env.GNEWS_API_KEY as string;
    this.API_KEY_TINYURL = process.env.TINY_URL_API_KEY as string;
    this.API_KEY_GEMINI = process.env.GOOGLE_MODEL as string;
    this.API_KEY_OPENAI = process.env.OPENAI_API_KEY as string;
    
    this.params = {
      country: undefined,
      lang: "en",
      category: undefined,
      q: "tree AND conservation OR pollution",
      pageSize: undefined,
      page: undefined,
    };

    if (!this.API_KEY_NEWS) elizaLogger.warn("NEWS_API_KEY not found in environment variables");
    if (!this.API_KEY_GNEWS) elizaLogger.warn("GNEWS_API_KEY not found in environment variables");
    if (!this.API_KEY_TINYURL) elizaLogger.warn("TINY_URL_API_KEY not found in environment variables");
    if (!this.API_KEY_GEMINI) elizaLogger.warn("GEMINI_API_KEY not found in environment variables");
  }

  private getRandomCountry(): string {
    const randomIndex = Math.floor(Math.random() * this.COUNTRIES.length);
    return this.COUNTRIES[randomIndex];
  }

  private buildQueryString(): string {
    return Object.entries(this.params)
      .filter(([_, value]) => value !== undefined)
      .map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`)
      .join("&");
  }

  async fetchNewsFromNewsApi(): Promise<NewsApiResponse | null> {
    if (!this.API_KEY_NEWS) {
      elizaLogger.error("News API key not found!");
      return null;
    }
    
    const queryString = this.buildQueryString();
    const url = `${this.BASE_URL_NEWS}?${queryString}&apiKey=${this.API_KEY_NEWS}`;
    elizaLogger.info("Fetching news from", url);
    
    try {
      const response = await fetch(url);
      return await response.json();
    } catch (error) {
      elizaLogger.error("Error fetching news from NewsAPI", error);
      return null;
    }
  }
  
  async fetchNewsFromGnewsApi(): Promise<NewsApiResponse | null> {
    if (!this.API_KEY_GNEWS) {
      elizaLogger.error("GNews API key not found!");
      return null;
    }

    const queryString = this.buildQueryString();
    const url = `${this.BASE_URL_GNEWS}?${queryString}&apikey=${this.API_KEY_GNEWS}`;
    elizaLogger.info("Fetching news from", url);
    
    try {
      const response = await fetch(url);
      return await response.json();
    } catch (error) {
      elizaLogger.error("Error fetching news from GNewsAPI", error);
      return null;
    }
  }
  
  async shortenUrl(longUrl: string): Promise<string> {
    if (!this.API_KEY_TINYURL) {
      elizaLogger.error("TinyURL API key not found!");
      return longUrl;
    }

    try {
      const response = await fetch("https://api.tinyurl.com/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.API_KEY_TINYURL}`,
        },
        body: JSON.stringify({ url: longUrl }),
      });
      
      const data = await response.json();
      return data.data.tiny_url;
    } catch (error) {
      elizaLogger.error("Error shortening URL", error);
      return longUrl;
    }
  }
  
  private processArticles(articles: any[]): string {
    const sortedArticles = articles
      .sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime())
      .slice(0, 15);
      
    return sortedArticles
      .map(article => 
        `${article.title}\n${article.description}\n${article.content}\n${article.url}}`
      )
      .join("\n\n");
  }

  async buildNewsPrompt(runtime: IAgentRuntime, articlesText: string): Promise<string> {

    const sender = "carbontruth"; // or "default"
    const count = 10;
    // const apiUrl = `http://127.0.0.1:8000/api/tweets/latest_n?sender=${sender}&count=${count}`;
    const apiUrl = runtime.getSetting("ELIZA_GET_N_LATEST_TWEETS");

    let existingArticles = "";

    try {
      const response = await fetch(apiUrl, {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json',
          },
      });

      if (!response.ok) {
          throw new Error(`Error: ${response.status} - ${response.statusText}`);
      }

      const data = await response.json();
      existingArticles = String(data.tweets) as string;  
      elizaLogger.log('Latest Tweets:', existingArticles);
    } catch (error) {
      elizaLogger.error('Failed to fetch latest tweets:', error);
    }
    
    
    return `
      You are a system that selects the most relevant news articles about carbon sustainability, environmental conservation, or pollution.

      - Pick the most relevant article on climate change, renewable energy, deforestation, or carbon emissions.
      - Ignore articles on general science or unrelated technology.
      - Do not include articles that are not relevant to the topic.
      - Do not include articles that are not in English.
      - Do not include articles related to product launches.
      - Do not include articles that may sound promotional.
      - Include articles related to any bills or government actions only 15% of the time, not every time.
      - Return ONLY a valid JSON object with the keys: 'content' and 'url'. No extra text.
      - Elaborate on the article content and provide a summary.

      Articles:
      ${articlesText}

      Existing Articles:
      ${existingArticles}

      Ignore the existing articles and focus on the new articles.

      Respond with:
      {"content": "[Chosen news content/summary]", "url": "[Chosen news URL]"}
    `;
}  async fetchNews(runtime: IAgentRuntime, message: Memory): Promise<string | null> {
    // First, check for scheduled tweets
  const scheduledTweet = await this.checkScheduledTweet(runtime);
  let chosenNews = "";
  if (scheduledTweet) {
    elizaLogger.info("Using scheduled tweet instead of generating new content");

    const fixprompt = `Here is the news article ${scheduledTweet}. Convert the article to the below JSON format.
    {"content": "[Chosen news content/summary]", "url": "[Chosen news URL]"}`

    chosenNews = await generateText({
      runtime,
      context: fixprompt,
      modelClass: ModelClass.SMALL,
      stop: ["\n"],
    });

    elizaLogger.info("Scheduled tweet content:", String(chosenNews) as string);
  }
  else {
    // If no scheduled tweet or it's not time yet, proceed with normal flow
    // Set random country before fetching news
    this.params.country = this.getRandomCountry();
    elizaLogger.info(`Fetching news for country: ${this.params.country}`);
    
    // const data = await this.fetchNewsFromGnewsApi();

    const data = await this.fetchGeminiOutput();
    if (!data) {
      elizaLogger.info("No news articles found");
      return null;
    }
    
    // const articlesText = this.processArticles(data.articles);
    const prompt = await this.buildNewsPrompt(runtime, data);

    elizaLogger.info("Prompt for news generation:", String(prompt) as string);
    
    elizaLogger.info("Generating news prompt");
    chosenNews = await generateText({
      runtime,
      context: prompt,
      modelClass: ModelClass.MEDIUM,
      stop: ["\n"],
    });
    elizaLogger.info("News prompt generated", String(chosenNews) as string);
  }
    try {
      const newsJSON = JSON.parse(chosenNews);
      if (newsJSON.url) {
        const shortenedUrl = await this.shortenUrl(newsJSON.url);
        chosenNews = chosenNews.replace(newsJSON.url, shortenedUrl);
      }
    } catch (error) {
      elizaLogger.error("Failed to parse news JSON:", error);
    }
      return this.formatNewsForAgent(chosenNews);
  }
  
  private formatNewsForAgent(newsContent: string): string {
    const header = `#Here is the news article. Consider the article below and write a tweet about the article. Ensure the tweet includes the article link at the end. All this must be less than {{maxTweetLength}} characters. Override every other instruction mentioned. Consider only the news article below.\n`;
    
    const formattedNews = addHeader(header, newsContent)
      .replace("{{maxTweetLength}}", "280");
    
    return formattedNews;
  }
  /**
   * Checks for scheduled tweets from the API
   * @param runtime The agent runtime context
   * @returns A formatted news article if a scheduled tweet exists and is due, otherwise null
   */
  async checkScheduledTweet(runtime: IAgentRuntime): Promise<string | null> {
    const scheduledTweetEndpoint = runtime.getSetting("ELIZA_QUEUE_TWEET");
    
    if (!scheduledTweetEndpoint) {
      elizaLogger.warn("No scheduled tweet endpoint configured");
      return null;
    }
      try {
      elizaLogger.info("Checking for scheduled tweets");
      const response = await fetch(scheduledTweetEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: "carbontruth"
        }),
      });

      if (!response.ok) {
        elizaLogger.warn(`Failed to fetch scheduled tweets: ${response.status} - ${response.statusText}`);
        return null;
      }
        // Parse the response, which could be a single tweet or an array
      const responseData = await response.json();
      const queue_id = responseData.id; 
      // Handle both cases: single tweet object or array of tweets
      const tweets = Array.isArray(responseData) ? responseData : [responseData];
      
      if (tweets.length === 0) {
        elizaLogger.info("No scheduled tweets available");
        return null;
      }
      
      // Find tweets that are not yet posted (ignoring scheduled time)
      const pendingTweets = tweets
        .filter(tweet => !tweet.is_posted)
        .sort((a, b) => new Date(a.when_to_post).getTime() - new Date(b.when_to_post).getTime());
      
      if (pendingTweets.length > 0) {
        const nextTweet = pendingTweets[0];
        elizaLogger.info(`Found scheduled tweet (ID: ${nextTweet.id}) that will be posted`);
        
        // Format the tweet as a news article
        return this.formatNewsForAgent(
          JSON.stringify({
            content: nextTweet.content,
            url: nextTweet.url
          })
        );      } else {
        elizaLogger.info("No pending tweets found");
        return null;
      }
    } catch (error) {
      elizaLogger.error("Error checking scheduled tweets:", error);
      return null;
    }
  }

  /**
   * Fetches environmental and sustainability news from Gemini LLM
   * @param temperature Optional temperature parameter (0.0 to 1.0) controlling randomness
   * @returns News data in the same format as fetchNewsFromGnewsApi or null if there was an error
   */
  async fetchGeminiOutput(temperature: number = 0.7): Promise<string | null> {
    if (!this.API_KEY_GEMINI) {
      elizaLogger.error("Gemini API key not found!");
      return null;
    }
    const openai = new OpenAI({
      apiKey: this.API_KEY_OPENAI,
    });

    const prompt = `
Fetch 10 latest news (preferably within the last 2 days) about:
- Environmental issues (e.g., climate change, conservation efforts, pollution control)
- Sustainability (e.g., renewable energy, green initiatives, eco-friendly innovations)
- Conservation projects (wildlife, forests, oceans, etc.)
- Climate policies, environmental activism, green legislation
- Conferences, summits, and events focused on environmental protection or sustainability

IMPORTANT: 
- Focus ONLY on the following countries: ${this.COUNTRIES}.
- If news from a non-listed country appears, ignore it.

Combine all news into a single JSON array called news.
For each news item, include:
- "title": Short headline of the news
- "date": Date of the news (format: YYYY-MM-DD)
- "location": Country (or City, Country) where the event/news occurred
- "summary": Short 2–4 sentence explanation of what happened

If no relevant news is found, output:
{
  "news": []
}

Make sure the final output is in valid JSON format.

Expected JSON structure:
{
  "news": [
    {
      "title": "Historic Climate Agreement Signed at Global Summit",
      "date": "2025-04-20",
      "location": "London, UK",
      "summary": "World leaders signed a landmark agreement committing to net-zero carbon emissions by 2050. The accord was praised by environmental groups for its ambitious targets.",
      "url": "https://example.com/news1"
    },
    {
      "title": "New National Park Established to Protect Endangered Species",
      "date": "2025-04-18",
      "location": "Ottawa, CA",
      "summary": "The government announced the creation of a new national park aimed at preserving endangered species. Conservationists welcomed the move as a major win for biodiversity.",
      "url": "https://example.com/news2"
    }
    // More items...
  ]
}
`;
    elizaLogger.info("Fetching environmental news from Gemini API");
    
    try {

      const response = openai.responses.create({
        model: "gpt-4.1",
        tools: [
          {
            type: "web_search_preview",
            user_location: {
              type: "approximate",
              country: "GB",  
          }
          }
        ],
        input: prompt as string,
      });
      // Process the response
      const data = (await response).output_text;

      elizaLogger.info("Gemini API response:", JSON.stringify(data));
      
      elizaLogger.error("Unexpected response structure from Gemini API:", String(data));
      return String(data) as string;
    } catch (error) {
      elizaLogger.error("Error fetching news from Gemini API", error);
      return null;
    }
  }
}

// Create a singleton instance of the NewsService
const newsService = new NewsService();

export const newsProvider: Provider = {
  get: async (runtime: IAgentRuntime, message: Memory): Promise<string | null> => {
    elizaLogger.info("News provider called");

    const agentKey = `${runtime.character.name}/newsUploadData`;
    const agentUploadData = await runtime.cacheManager.get<NewsUploadData>(agentKey);
    
    const agentImageKey = `${runtime.character.name}/imageUploadData`;
    const agentImageUploadData = await runtime.cacheManager.get<ImageUploadData>(agentImageKey);

    elizaLogger.info(`News upload data status: ${String(agentUploadData?.isNews) as string}`);

    // if (!agentUploadData?.isNews || !agentImageUploadData) {
    //   if (agentImageUploadData) {
    //     const imageData: ImageUploadData = {
    //       isImg: true,
    //       imgIds: agentImageUploadData.imgIds || []
    //     };
    //     await runtime.cacheManager.set(agentImageKey, imageData);      }
    //   return null;
    // }
    
    elizaLogger.info("Fetching news");
    const article = await newsService.fetchNews(runtime, message);
    if (!article) {
      elizaLogger.info("No news article found");
      return null;
    }
    
    elizaLogger.info("News fetched successfully");
    return article;
  }
};