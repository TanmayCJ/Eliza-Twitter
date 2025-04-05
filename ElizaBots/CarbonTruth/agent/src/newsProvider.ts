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
  
  const params: Record<string, string | number | undefined> = {
    country: undefined,
    lang: "en",
    category: undefined,
    q: "tree AND conservation OR pollution",
    pageSize: undefined,
    page: undefined,
};
  
  
  interface NewsApiResponse {
    totalResults: number;
    articles: any[];
  }
  
  async function fetchNewsFromNewsApi(): Promise<NewsApiResponse | null> {
    const API_KEY =
      (process.env.NEWS_API_KEY as string);
    const BASE_URL = "https://newsapi.org/v2/everything";
  
    if (!API_KEY) {
      elizaLogger.error("News API key not found!");
      return null;
    }
  
    const queryString = Object.entries(params)
      .filter(([_, value]) => value !== undefined)
      .map(
        ([key, value]) => `${key}=${encodeURIComponent(String(value))}`
      )
      .join("&");
  
    const url = `${BASE_URL}?${queryString}&apiKey=${API_KEY}`;
    elizaLogger.info("Fetching news from", url);
  
    try {
      const response = await fetch(url);
      const data = await response.json();
      return data;
    } catch (error) {
      elizaLogger.error("Error fetching news from API", error);
      return null;
    }
}
  
  async function fetchNewsFromGnewsApi(): Promise<NewsApiResponse | null> {
    const API_KEY =
      (process.env.GNEWS_API_KEY as string);
    const BASE_URL = "https://gnews.io/api/v4/top-headlines";
  
    if (!API_KEY) {
      elizaLogger.error("News API key not found!");
      return null;
    }
  
    const queryString = Object.entries(params)
      .filter(([_, value]) => value !== undefined)
      .map(
        ([key, value]) => `${key}=${encodeURIComponent(String(value))}`
      )
      .join("&");
  
    const url = `${BASE_URL}?${queryString}&apikey=${API_KEY}`;
    elizaLogger.info("Fetching news from", url);
  
    try {
      const response = await fetch(url);
      const data = await response.json();
      return data;
    } catch (error) {
      elizaLogger.error("Error fetching news from API", error);
      return null;
    }
  }
  
  async function shortenUrl(longUrl: string): Promise<string> {
    const apiUrl = "https://api.tinyurl.com/create";
    const apiKey = (process.env.TINY_URL_API_KEY as string);; // Replace with your actual API key
  
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ url: longUrl }),
    });
  
    const data = await response.json();
    return data.data.tiny_url; // Returns the shortened URL
  }
  
  export async function fetchNews(
    runtime: IAgentRuntime,
    message: Memory
  ): Promise<string | null> {
    const data = await fetchNewsFromGnewsApi();
    if (!data || data.totalResults === 0) {
      return null;
    }
  
    // Process news articles
    const sortedArticles = data.articles.sort(
      (a: any, b: any) =>
        new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
    );
  
    const articles = sortedArticles
      .slice(0, 15)
      .map(
        (article: any) =>
          `${article.title}\n${article.description}\n${article.content}\n${
            article.url}}`
      )
      .join("\n\n");
  
      const prompt = `
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
      ${articles}
      
      Respond with:
      {"content": "[Chosen news content/summary]", "url": "[Chosen news URL]"}
      `;
  
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
      if (!newsJSON.url) {
        throw new Error("URL is missing in response");
      }
      const shortenedUrl = await shortenUrl(newsJSON.url);
      chosenNews = chosenNews.replace(newsJSON.url, shortenedUrl);
    } catch (error) {
      elizaLogger.error("Failed to parse news JSON:", error);
    }
  
    chosenNews = addHeader(
      `#Here is the news article. Consider the article below and write a tweet about the article. Ensure the tweet includes the article link at the end. All this must be less than {{maxTweetLength}} characters. Override every other instruction mentioned. Consider only the news article below.\n`,
      chosenNews
    );
    chosenNews = chosenNews.replace(
      "{{maxTweetLength}}",
      "280"
    );
    return chosenNews;
  }
  
  export const newsProvider: Provider = {
    get: async (runtime: IAgentRuntime, message: Memory): Promise<string | null> => {
      elizaLogger.info("News provider called");
  
      const agentKey = `${runtime.character.name}/newsUploadData`;
      const agentUploadData = await runtime.cacheManager.get<{ isNews: boolean, ifImg: boolean, lastUpdatedNews: string }>(agentKey);

      elizaLogger.info(`News uData: ${agentUploadData}`);
  
      if (agentUploadData.isNews && agentUploadData) {
        elizaLogger.info("Fetching news");
          const article = await fetchNews(runtime, message);   
        if (article) {
            elizaLogger.info("News fetched:", article);
            const agentData = {
              isNews: false,
              ifImg: true,
              lastUpdatedNews: new Date().toISOString(),
          }
            await runtime.cacheManager.set(agentKey, agentData);
          return article;
        } else {
          return null;
        }
      } else {
        return null;
      }
    },
  };