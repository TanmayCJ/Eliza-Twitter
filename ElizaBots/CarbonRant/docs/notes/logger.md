# Logger Features

## Overview

The ElizaBots CarbonRant application uses the Pino logger (`elizaLogger`) for all logging needs. The logger has been enhanced with several features to improve the developer and user experience.

## Features

### Custom Log Levels

Besides the standard log levels, our logger supports the following custom levels:

- `fatal`: 60 (highest severity)
- `error`: 50
- `warn`: 40
- `info`: 30
- `log`: 29
- `progress`: 28
- `success`: 27
- `debug`: 20
- `trace`: 10 (lowest severity)

### Colorized Output

By default, log output is colorized and formatted with human-readable timestamps. This can be disabled by setting `LOG_JSON_FORMAT=true` in your environment.

### Log Level Configuration

You can configure the default log level by setting the `DEFAULT_LOG_LEVEL` environment variable. If not specified, it defaults to "info".

```
DEFAULT_LOG_LEVEL=debug
```

### API Rate Limit Error Filtering

The logger includes a special filter for Groq API rate limit errors to reduce terminal noise:

- Detects rate limit errors from the Groq API
- Downsamples these errors to avoid flooding the logs
- Shows a user-friendly warning message at most once per minute
- Keeps detailed error information in debug logs
- Tracks the number of filtered errors

For more details, see the [Groq Rate Limit Error Filtering](./groq-rate-limit-filtering.md) documentation.

## Usage Examples

Basic usage:

```typescript
import { elizaLogger } from "@elizaos/core";

// Various log levels
elizaLogger.fatal("Critical error occurred, shutting down");
elizaLogger.error("Failed to connect to database", { retries: 3 });
elizaLogger.warn("API rate limit approaching", { usagePercent: 85 });
elizaLogger.info("User logged in", { userId: "user123" });
elizaLogger.log("Processing operation", { operation: "data-sync" });
elizaLogger.progress("Importing data: 50%");
elizaLogger.success("Operation completed successfully");
elizaLogger.debug("Detailed operation information", { details: { ... } });
elizaLogger.trace("Function call trace", { args: [...], stack: "..." });
```

## Extending the Logger

To add custom functionality to the logger, you can extend the Pino hooks in `src/logger.ts`. The existing rate limit filtering provides a good example of how to implement custom log processing.
