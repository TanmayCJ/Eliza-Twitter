import pino, { type LogFn } from "pino";
import pretty from "pino-pretty";

import { parseBooleanFromText } from "./parsing.ts";


const customLevels: Record<string, number> = {
    fatal: 60,
    error: 50,
    warn: 40,
    info: 30,
    log: 29,
    progress: 28,
    success: 27,
    debug: 20,
    trace: 10,
};

const raw = parseBooleanFromText(process?.env?.LOG_JSON_FORMAT) || false;

const createStream = () => {
    if (raw) {
        return undefined;
    }
    return pretty({
        colorize: true,
        translateTime: "yyyy-mm-dd HH:MM:ss",
        ignore: "pid,hostname",
    });
};

const defaultLevel = process?.env?.DEFAULT_LOG_LEVEL || "info";

// Function to filter out Groq API rate limit errors or reduce their verbosity
// Keeps track of the last time a rate limit error was logged
let lastGroqRateLimitErrorTime = 0;
let rateLimitErrorCount = 0; // Count of filtered errors since last notification
const RATE_LIMIT_NOTIFICATION_INTERVAL_MS = 60000; // Show rate limit message once per minute

const isGroqRateLimitError = (obj: Record<string, any> | string): boolean => {
    if (typeof obj === 'string') {
        return (
            (obj.toLowerCase().includes('groq') && obj.toLowerCase().includes('rate limit')) ||
            (obj.includes('429') && obj.includes('Too Many Requests'))
        );
    }
    
    // Check error message in different formats
    const errorMsg = (obj.error?.message || obj.message || '').toLowerCase();
    const stack = String(obj.stack || '').toLowerCase();
    const name = String(obj.name || '').toLowerCase();
    const provider = String(obj.provider || '').toLowerCase();
    const statusCode = obj.status || obj.statusCode || obj.error?.status || obj.error?.statusCode;
    
    return (
        // Check for common rate limit phrases
        (errorMsg.includes('rate limit') || errorMsg.includes('too many requests') || errorMsg.includes('ratelimit')) ||
        // Check for HTTP 429 status code
        (statusCode === 429) ||
        // Check for Groq provider specifically
        (provider === 'groq' && (
            errorMsg.includes('limit') || 
            errorMsg.includes('429') || 
            errorMsg.includes('too many')
        )) ||
        // Check if error stack trace mentions groq and rate limiting
        (stack.includes('groq') && (
            stack.includes('rate') || 
            stack.includes('limit') || 
            stack.includes('429')
        )) ||
        // Check error name for rate limit indicators
        (name.includes('rate') && name.includes('limit'))
    );
};

const options = {
    level: defaultLevel,
    customLevels,    hooks: {
        logMethod(
            inputArgs: [string | Record<string, unknown>, ...unknown[]],
            method: LogFn
        ): void {
            const [arg1, ...rest] = inputArgs;
              // Check if this is a Groq rate limit error that we want to filter
            if (method.name === 'error' || method.name === 'ERROR') {
                let isRateLimitError = false;
                let errorObj: Record<string, any> | null = null;
                
                // Check if first argument is the rate limit error
                if (typeof arg1 === 'object' && isGroqRateLimitError(arg1 as Record<string, any>)) {
                    isRateLimitError = true;
                    errorObj = arg1 as Record<string, any>;
                }
                
                // Check if second argument is the rate limit error
                else if (typeof arg1 === 'string' && 
                    rest.length > 0 && 
                    typeof rest[0] === 'object' && 
                    isGroqRateLimitError(rest[0] as Record<string, any>)) {
                    isRateLimitError = true;
                    errorObj = rest[0] as Record<string, any>;
                }
                  if (isRateLimitError) {
                    const now = Date.now();
                    rateLimitErrorCount++; // Increment the counter
                    
                    // If we should show a notification (first time or after interval)
                    if (now - lastGroqRateLimitErrorTime > RATE_LIMIT_NOTIFICATION_INTERVAL_MS) {
                        // Show user-friendly message at warn level with count if applicable
                        const warnMethod = this.warn || this.WARN;
                        let message = '⚠️ Groq API rate limit reached. Some requests may be delayed.';
                        
                        // Add count info if this isn't the first error
                        if (rateLimitErrorCount > 1) {
                            message += ` ${rateLimitErrorCount} rate limit errors filtered in the last minute.`;
                        }
                        
                        warnMethod.apply(this, [
                            { 
                                source: 'groq',
                                type: 'rate_limit',
                                count: rateLimitErrorCount
                            }, 
                            message
                        ]);
                        
                        lastGroqRateLimitErrorTime = now;
                        rateLimitErrorCount = 0; // Reset counter after notification
                    }
                    
                    // Always log full details to debug
                    const debugMethod = this.debug || this.DEBUG;
                    debugMethod.apply(this, [
                        errorObj || { context: arg1 }, 
                        '[Groq Rate Limit Error Details]'
                    ]);
                    
                    return; // Skip regular error logging
                }
            }

            // Normal logging logic for non-filtered messages

            if (typeof arg1 === "object") {
                const messageParts = rest.map((arg) =>
                    typeof arg === "string" ? arg : JSON.stringify(arg)
                );
                const message = messageParts.join(" ");
                method.apply(this, [arg1, message]);
            } else {
                const context = {};
                const messageParts = [arg1, ...rest].map((arg) =>
                    typeof arg === "string" ? arg : arg
                );
                const message = messageParts
                    .filter((part) => typeof part === "string")
                    .join(" ");
                const jsonParts = messageParts.filter(
                    (part) => typeof part === "object"
                );

                Object.assign(context, ...jsonParts);

                method.apply(this, [context, message]);
            }
        },
    },
};

export const elizaLogger = pino(options, createStream());

export default elizaLogger;
