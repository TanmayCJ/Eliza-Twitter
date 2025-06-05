import { elizaLogger, Evaluator, IAgentRuntime, Memory } from "@elizaos/core";

const newsData = {
    isNews: true,
    lastUpdatedNews: new Date().toISOString() // Store time in ISO format
};

const hours = 1;
const minutes = 4; // 4 minutes

export const newsEvaluator: Evaluator = {
    name: "NEWS_EVALUATOR",
    similes: ["EXTRACT_NEWS_DATA"],
    
    validate: async (runtime, message) => {
        elizaLogger.info("News evaluator called");

        const newsKey = `${runtime.character.name}/${message.userId}/newsUploadData`;
        let newsUploadData = await runtime.cacheManager.get<{ isNews: boolean, lastUpdatedNews: string }>(newsKey);

        if (newsUploadData === undefined) { 
            await runtime.cacheManager.set(newsKey, newsData);
        }
        else {
            const currentTime = new Date().toISOString();
            const lastUpdatedTime = new Date(newsUploadData.lastUpdatedNews).getTime();
            const timeDifference = new Date(currentTime).getTime() - lastUpdatedTime;
            const timeLimit = hours* (minutes * (60 * 1000)); // 24 hours in milliseconds

            if (timeDifference > timeLimit) {
                newsUploadData.isNews = true; // Reset isNews after 24 hours
                await runtime.cacheManager.set(newsKey, newsUploadData);
            }
        }
        
        return true;
    },
    
    handler: async (runtime, message) => {
        elizaLogger.log("News evaluator handler called");

        const newsKey = `${runtime.character.name}/${message.userId}/newsCount`;
        let newsCount = await runtime.cacheManager.get<number>(newsKey);

        if (newsCount === undefined) {
            newsCount = 3; // Initialize news count
        } else {
            newsCount = Math.max(0, newsCount - 1); // Prevent negative values
        }

        runtime.cacheManager.set(newsKey, newsCount);
        elizaLogger.info(`Updated News Count: ${newsCount}`);

        return true;
    },
    
    description: "This evaluator is used to extract news count.",
    alwaysRun: true,
    examples: []
};
