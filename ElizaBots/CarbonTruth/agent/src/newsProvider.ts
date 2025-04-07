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

class NewsService {
  private readonly API_KEY_NEWS: string;
  private readonly API_KEY_GNEWS: string;
  private readonly API_KEY_TINYURL: string;
  private readonly BASE_URL_NEWS: string = "https://newsapi.org/v2/everything";
  private readonly BASE_URL_GNEWS: string = "https://gnews.io/api/v4/top-headlines";
  private readonly COUNTRIES: string[] = ["us", "ca", "uk"]; // us, ca, uk, au, de, fr, in, it, jp, mx, nl, no, ru, se, sg, za
  
  private params: Record<string, string | number | undefined>;

  constructor() {
    this.API_KEY_NEWS = process.env.NEWS_API_KEY as string;
    this.API_KEY_GNEWS = process.env.GNEWS_API_KEY as string;
    this.API_KEY_TINYURL = process.env.TINY_URL_API_KEY as string;
    
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
  
  private buildNewsPrompt(articlesText: string): string {
    return `
      You are a system that selects the most relevant news about carbon sustainability, environmental conservation, or pollution.
      
      - Pick the most relevant article on climate change, renewable energy, deforestation, or carbon emissions.
      - Ignore articles on politics, general science, or unrelated tech.
      - Do not include any articles that are not relevant to the topic.
      - Do not include any articles that are not in English.
      - Do not include any articles related to product launches.
      - Do not include any articles that might sound promotional.
      - Return ONLY a valid JSON object with keys: 'content' and 'url'. No extra text.
      - Elaborate on the article content and provide a summary.
      
      Articles:
      ${articlesText}
      
      Respond with:
      {"content": "[Chosen news content/summary]", "url": "[Chosen news URL]"}
    `;
  }
  
  async fetchNews(runtime: IAgentRuntime, message: Memory): Promise<string | null> {
    // Set random country before fetching news
    this.params.country = this.getRandomCountry();
    elizaLogger.info(`Fetching news for country: ${this.params.country}`);
    
    const data = await this.fetchNewsFromGnewsApi();
    if (!data || data.totalResults === 0) {
      elizaLogger.info("No news articles found");
      return null;
    }
    
    const articlesText = this.processArticles(data.articles);
    const prompt = this.buildNewsPrompt(articlesText);
    
    elizaLogger.info("Generating news prompt");
    let chosenNews = await generateText({
      runtime,
      context: prompt,
      modelClass: ModelClass.SMALL,
      stop: ["\n"],
    });
    elizaLogger.info("News prompt generated");
    
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

    elizaLogger.info(`News upload data status: ${agentUploadData?.isNews}`);

    if (!agentUploadData?.isNews || !agentImageUploadData) {
      if (agentImageUploadData) {
        const imageData: ImageUploadData = {
          isImg: true,
          imgIds: agentImageUploadData.imgIds || []
        };
        await runtime.cacheManager.set(agentImageKey, imageData);
      }
      return null;
    }

    elizaLogger.info("Fetching news");
    const article = await newsService.fetchNews(runtime, message);
    
    if (article) {
      elizaLogger.info("News fetched successfully");
      
      const updatedData: NewsUploadData = {
        isNews: false,
        lastUpdatedNews: new Date().toISOString(),
      };
      
      await runtime.cacheManager.set(agentKey, updatedData);
      return article;
    }
    
    return null;
  },
};