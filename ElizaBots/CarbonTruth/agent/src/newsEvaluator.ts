import { elizaLogger, Evaluator, IAgentRuntime, Memory } from "@elizaos/core";

const newsData = {
    isNews: true,
    lastUpdatedNews: new Date().toISOString() // Store time in ISO format
};

const hours = 1;
const minutes = 5; 

export const newsEvaluator: Evaluator = {
    name: "NEWS_EVALUATOR",
    similes: ["EXTRACT_NEWS_DATA"],
    
    validate: async (runtime, message) => {
        elizaLogger.info("News evaluator called");

        const agentKey = `${runtime.character.name}/newsUploadData`;
        let agentUploadData = await runtime.cacheManager.get<{ isNews: boolean, isImg: boolean, lastUpdatedNews: string }>(agentKey);

        if (agentUploadData === undefined) { 
            await runtime.cacheManager.set(agentKey, newsData);
        }
        else {
            const currentTime = new Date().toISOString();
            const lastUpdatedTime = new Date(agentUploadData.lastUpdatedNews).getTime();
            const timeDifference = new Date(currentTime).getTime() - lastUpdatedTime;
            const timeLimit = hours* (minutes * (60 * 1000)); // 24 hours in milliseconds

            if (timeDifference > timeLimit) {
                agentUploadData.isNews = true;
                agentUploadData.isImg = false;
                await runtime.cacheManager.set(agentKey, agentUploadData);
            }
        }
        
        return true;
    },
    
    handler: async (runtime, message) => {
        elizaLogger.log("News evaluator handler called");

        const newsKey = `${runtime.character.name}/newsCount`;
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
