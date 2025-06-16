# Tweet Popularity Check Configuration

This document describes the configuration options for the tweet popularity checking feature, which helps ensure that tweets meet quality standards before being posted.

## Environment Variables

The following environment variables control the tweet popularity check feature:

### `TWITTER_POPULARITY_CHECK_ENABLED`
- Type: Boolean (`true` or `false`)
- Default: `false`
- Description: Enables or disables the tweet popularity check feature. When enabled, tweets will be evaluated for popularity before posting.

### `TWITTER_POPULARITY_MIN_SCORE`
- Type: Number (0-100)
- Default: `30`
- Description: Sets the minimum popularity score threshold that tweets must meet to be posted. Tweets with scores below this threshold will be rejected.

### `TWITTER_POPULARITY_API_URL`
- Type: String (URL)
- Default: `http://127.0.0.1:8000/api/popularity/`
- Description: URL for the ElizaServices API endpoint that provides tweet popularity scoring. Can be configured to use local or remote instances of the ElizaServices API.

### `TWITTER_POPULARITY_VERBOSE_OUTPUT`
- Type: Boolean (`true` or `false`)
- Default: `false`
- Description: Controls the verbosity of terminal output from popularity checks. When enabled, shows detailed formatted output with colors. When disabled, shows only essential information.

## Example Configuration

```env
# Enable tweet popularity checking
TWITTER_POPULARITY_CHECK_ENABLED=true

# Set minimum popularity score to 40
TWITTER_POPULARITY_MIN_SCORE=40

# Use a remote ElizaServices API instance
TWITTER_POPULARITY_API_URL=https://elizaservices.example.com/api/popularity/

# Disable verbose output for cleaner logs
TWITTER_POPULARITY_VERBOSE_OUTPUT=false
```

## Testing the Configuration

You can test the popularity check feature using the provided test script:

```powershell
# Run with default configuration
./scripts/test-tweet-popularity.ps1

# Run with custom configuration
./scripts/test-tweet-popularity-env.ps1
```

## Troubleshooting

- If popularity checks fail, ensure the ElizaServices API is running and accessible at the configured URL.
- Check network connectivity if using a remote API instance.
- The API should return a JSON response with a `predicted_score` field (0-100) and an `explanation` field.
