import { elizaLogger, Evaluator, IAgentRuntime, Memory } from "@elizaos/core";

const newsData = {
    isNews: true,
    lastUpdatedNews: new Date().toISOString() // Store time in ISO format
};

const imageData = {
    isImg: false,
    imgIds: [] // Initialize with an empty array
};

const hours = 0;
const minutes = 20; 

export const newsEvaluator: Evaluator = {
    name: "NEWS_EVALUATOR",
    similes: ["EXTRACT_NEWS_DATA"],
    
    validate: async (runtime, message) => {
        elizaLogger.info("News evaluator called");

        const agentKey = `${runtime.character.name}/newsUploadData`;
        const agentUploadData = await runtime.cacheManager.get<{ isNews: boolean, lastUpdatedNews: string }>(agentKey);

        const agentImageKey = `${runtime.character.name}/imageUploadData`;
        const agentImageUploadData = await runtime.cacheManager.get<{ isImg: boolean, imgIds: string[] }>(agentImageKey);

        

        if (agentUploadData === undefined) { 
            await runtime.cacheManager.set(agentKey, newsData);
        }
        if (agentImageUploadData === undefined) {
            await runtime.cacheManager.set(agentImageKey, imageData);
        }
        else {
            const currentTime = new Date().toISOString();
            const lastUpdatedTime = new Date(agentUploadData.lastUpdatedNews).getTime();
            const timeDifference = new Date(currentTime).getTime() - lastUpdatedTime;
           
            const timeLimit = (hours * 60 * 60 * 1000) + (minutes * 60 * 1000);

            if (timeDifference > timeLimit) {
                const agentData = {
                    isNews: true,
                    lastUpdatedNews: agentUploadData.lastUpdatedNews,
                }
                const imageData = {
                    isImg: false,
                    imgIds: agentImageUploadData.imgIds // Initialize with an empty array
                };
                await runtime.cacheManager.set(agentImageKey, imageData);
                await runtime.cacheManager.set(agentKey, agentData);
                elizaLogger.info("Updating news data:");
            }
            else {
                const imageData2 = {
                    isImg: true,
                    imgIds: agentImageUploadData.imgIds // Initialize with an empty array
                };
                await runtime.cacheManager.set(agentImageKey, imageData2);
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
