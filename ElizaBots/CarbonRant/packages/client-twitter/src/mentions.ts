/**
 * Twitter mentions configuration
 * 
 * This file defines personalities that can be tagged in tweets and controls which ones
 * are actually enabled for tagging. It also provides utility functions for handling tags.
 */

/**
 * Complete list of climate-related personalities that could potentially be tagged
 */
export const climatePersonalities = [
    // Political figures
    { handle: 'ElonMusk', name: 'Elon Musk', category: 'tech' },
    { handle: 'realDonaldTrump', name: 'Donald Trump', category: 'political' },
    { handle: 'GretaThunberg', name: 'Greta Thunberg', category: 'activist' },
    { handle: 'AOC', name: 'Alexandria Ocasio-Cortez', category: 'political' },
    { handle: 'POTUS', name: 'Joe Biden', category: 'political' },
    { handle: 'JeffBezos', name: 'Jeff Bezos', category: 'tech' },
    { handle: 'BillGates', name: 'Bill Gates', category: 'tech' },
    { handle: 'KimKardashian', name: 'Kim Kardashian', category: 'celebrity' },
    
    // Corporate/Business
    { handle: 'BlackRock', name: 'BlackRock', category: 'corporate' },
    { handle: 'Shell', name: 'Shell', category: 'corporate' },
    { handle: 'exxonmobil', name: 'Exxon', category: 'corporate' },
    { handle: 'zuck', name: 'Mark Zuckerberg', category: 'tech' },
    
    // Economists, technologists, and thinkers
    { handle: 'yanisvaroufakis', name: 'Yanis Varoufakis', category: 'economist' },
    { handle: 'VitalikButerin', name: 'Vitalik Buterin', category: 'tech' },
    { handle: 'SBF_FTX', name: 'Sam Bankman-Fried', category: 'tech' },
    { handle: 'Larry_Fink', name: 'Larry Fink', category: 'corporate' },
    
    // More political figures
    { handle: 'GavinNewsom', name: 'Gavin Newsom', category: 'political' },
    { handle: 'algore', name: 'Al Gore', category: 'political' },
    { handle: 'Cobratate', name: 'Andrew Tate', category: 'controversial' },
    { handle: 'taylorswift13', name: 'Taylor Swift', category: 'celebrity' },
    { handle: 'KylieJenner', name: 'Kylie Jenner', category: 'celebrity' },
    
    // Activists and journalists
    { handle: 'Janefonda', name: 'Jane Fonda', category: 'activist' },
    { handle: 'NaomiAKlein', name: 'Naomi Klein', category: 'journalist' },
    { handle: 'ShellenbergerMD', name: 'Michael Shellenberger', category: 'controversial' },
    { handle: 'JohnKerry', name: 'John Kerry', category: 'political' },
    { handle: 'sacca', name: 'Chris Sacca', category: 'tech' },
    { handle: 'RobertKennedyJr', name: 'RFK Jr.', category: 'controversial' },
    { handle: 'GeorgeMonbiot', name: 'George Monbiot', category: 'journalist' },
    { handle: 'Sen_JoeManchin', name: 'Joe Manchin', category: 'political' },
    
    // Groups and collectives
    { handle: 'wef', name: 'World Economic Forum', category: 'organization' },
    { handle: 'CryptoTwitter', name: 'Crypto Bros', category: 'tech' },
    { handle: 'API', name: 'American Petroleum Institute', category: 'organization' },
    { handle: 'UNFCCC', name: 'UN Climate', category: 'organization' },
    { handle: 'RepMTG', name: 'Marjorie Taylor Greene', category: 'controversial' },
    
    // Climate-focused accounts and organizations
    { handle: 'CarbonTruths', name: 'Carbon Truths', category: 'climate' },
    { handle: 'ClimateReality', name: 'Climate Reality', category: 'organization' },
    { handle: 'GreenpeaceUSA', name: 'Greenpeace USA', category: 'organization' },
    { handle: 'ClimateDefense', name: 'Environmental Defense Fund', category: 'organization' }
];

/**
 * Subset of accounts that are actually enabled for tagging
 * Currently configured to only tag climate-positive accounts
 */
export const enabledForTagging = [
    'CarbonTruths',
    'ClimateReality',
    'GreenpeaceUSA',
    'ClimateDefense'
];

/**
 * Categories that should be tagged in a positive manner only
 */
export const positiveTaggingOnly = [
    'climate',
    'organization',
    'activist'
];

/**
 * Checks if a handle is enabled for tagging
 * 
 * @param handle The Twitter handle to check
 * @returns Boolean indicating whether the handle can be tagged
 */
export function isTaggingEnabled(handle: string): boolean {
    return enabledForTagging.includes(handle);
}

/**
 * Checks if a personality should only be tagged positively
 * 
 * @param handle The Twitter handle to check
 * @returns Boolean indicating whether the handle should only be tagged positively
 */
export function shouldTagPositivelyOnly(handle: string): boolean {
    const personality = climatePersonalities.find(p => p.handle === handle);
    if (!personality) return true; // Default to positive-only if personality not found
    return positiveTaggingOnly.includes(personality.category);
}

/**
 * Formats a handle for proper Twitter tagging
 * 
 * @param handle The Twitter handle to format
 * @returns The formatted handle with @ symbol
 */
export function formatHandle(handle: string): string {
    return `@${handle}`;
}

/**
 * Gets a list of recommended handles to tag based on tweet content 
 * 
 * @param content The tweet content to analyze
 * @param maxTags Maximum number of tags to return
 * @returns Array of handles that could be tagged
 */
export function getRecommendedTags(content: string, maxTags: number = 1): string[] {
    // Tagging is currently disabled - returning empty array
    // When re-enabling, this would normally involve some NLP to determine relevant personalities
    return [];
}