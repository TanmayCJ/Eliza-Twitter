import { TwitterClientInterface } from "./client";
import { TwitterPrePostHookHandler, type TweetInfo } from "./hooks";

const twitterPlugin = {
    name: "twitter",
    description: "Twitter client",
    clients: [TwitterClientInterface],
};

// Export the plugin as default export
export default twitterPlugin;


