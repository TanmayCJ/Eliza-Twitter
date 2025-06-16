# Groq API Rate Limit Error Filtering

This document explains how the Groq API rate limit error filtering works in the ElizaBots CarbonRant application.

## Overview

The ElizaBots application uses Groq's API for language model capabilities. When the Groq API reaches its rate limits, it can generate numerous error messages that flood the logs, making it difficult to see other important messages.

Our custom logger filter:
- Detects Groq API rate limit errors
- Filters repetitive error messages
- Shows a user-friendly notification at most once per minute
- Keeps detailed error information in debug logs
- Tracks the number of filtered errors

## How It Works

1. **Detection**: The logger has an enhanced detection mechanism that identifies rate limit errors in various formats, including:
   - Status code 429 (Too Many Requests)
   - Error messages containing "rate limit" or "too many requests"
   - Provider-specific errors from Groq
   - Stack traces that suggest rate limiting

2. **Filtering Logic**:
   - When a rate limit error is detected, it doesn't get logged at the ERROR level
   - Instead, it's downgraded to the DEBUG level for detailed logs
   - A user-friendly warning is shown at most once per minute at the WARN level
   - The warning includes a count of how many errors were filtered in the interval

3. **User Experience**:
   - The console stays clean without repetitive error spam
   - Users remain informed about rate limiting
   - Detailed error information is still available for troubleshooting

## Configuration

The rate limit filtering behavior can be adjusted by modifying the following variables in `packages/core/src/logger.ts`:

```typescript
// How often (in milliseconds) to show rate limit warnings
const RATE_LIMIT_NOTIFICATION_INTERVAL_MS = 60000; // Default: once per minute
```

## Debugging

If you need to see the full details of filtered rate limit errors:

1. Set the log level to DEBUG or lower:
   ```
   DEFAULT_LOG_LEVEL=debug
   ```

2. Look for log entries with the message `[Groq Rate Limit Error Details]`

## Example Output

With rate limit filtering:

```
[2023-06-16 14:23:45] WARN: ⚠️ Groq API rate limit reached. Some requests may be delayed.
[2023-06-16 14:24:45] WARN: ⚠️ Groq API rate limit reached. Some requests may be delayed. 23 rate limit errors filtered in the last minute.
```

Without rate limit filtering (what users would see without this feature):

```
[2023-06-16 14:23:45] ERROR: Groq API rate limit exceeded. Try again later.
[2023-06-16 14:23:46] ERROR: Groq API rate limit exceeded. Try again later.
[2023-06-16 14:23:47] ERROR: Groq API rate limit exceeded. Try again later.
[2023-06-16 14:23:48] ERROR: Groq API rate limit exceeded. Try again later.
... (many more similar errors)
```
