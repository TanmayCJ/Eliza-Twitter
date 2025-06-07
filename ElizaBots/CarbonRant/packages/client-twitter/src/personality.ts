console.log("personality.ts module loaded");

/**
 * Twitter Personality Configuration
 * 
 * This file defines different personalities that can influence the tone and style
 * of generated tweets. Each personality has a percentage weight that determines
 * how likely the system will adopt that personality's characteristics when creating content.
 */

/**
 * Twitter personality configuration with percentage weights
 * The total percentage should add up to 100%
 */
export interface PersonalityConfig {
    name: string;
    percentage: number;
    description: string;
    
}

/**
 * List of personalities with their percentage weights
 */
export const personalities: PersonalityConfig[] = [
    {
        name: 'George Carlin',
        percentage: 50,
        description: 'Sharp, satirical commentary with bold truth-telling and cynical observations about society and politics'
    },
    {
        name: 'Al Gore',
        percentage: 20,
        description: 'Serious, fact-based climate advocate focusing on scientific data and urgent calls to action'
    },
    {
        name: 'Default',
        percentage: 30,
        description: 'Balanced tone with moderate positions on climate issues'
    }
];

/**
 * Gets a random personality based on the configured percentage weights
 * 
 * @returns A randomly selected personality based on percentage weights
 */
export function getRandomPersonality(): PersonalityConfig {
    const rand = Math.random() * 100;
    let cumulativePercentage = 0;
    
    for (const personality of personalities) {
        cumulativePercentage += personality.percentage;
        if (rand <= cumulativePercentage) {
            return personality;
        }
    }
    
    // Fallback to the first personality if something goes wrong with the calculation
    return personalities[0];
}

/**
 * Checks if the total percentage allocations add up to 100%
 * 
 * @returns Boolean indicating whether the percentages are valid
 */
export function validatePersonalityPercentages(): boolean {
    const total = personalities.reduce((sum, personality) => sum + personality.percentage, 0);
    return Math.abs(total - 100) < 0.001; // Allow for minor floating point errors
}