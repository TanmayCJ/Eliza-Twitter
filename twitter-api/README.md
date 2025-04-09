# Twitter Analysis REST API

A Django REST API that fetches and analyzes Twitter data, including user information and tweets.

## Features

- Fetch and store Twitter user information
- Retrieve user tweets with metrics (public and non-public if authenticated)
- Incremental tweet updates using `since_id`
- Tweet analysis and storage
- RESTful API endpoints for data retrieval

## Prerequisites

- Python 3.8+
- Django 5.1+
- Twitter API credentials (v2)
- PostgreSQL (recommended) or SQLite

## Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd twitter-analysis
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root:
```env
DEBUG=True
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_KEY_SECRET=your_api_key_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Start the development server**
```bash
python manage.py runserver
```

## API Endpoints

### 1. Analyze Twitter User
- **Endpoint**: `POST /api/analyze/`
- **Purpose**: Fetch and analyze tweets for a given Twitter handle
- **Parameters**:
  ```json
  {
    "twitter_handle": "username",
    "tweet_count": 100  // optional
  }
  ```

### 2. Display Twitter Data
- **Endpoint**: `POST /api/display/`
- **Purpose**: Retrieve stored tweets and analysis
- **Parameters**:
  ```json
  {
    "twitter_handle": "username",
    "tweet_count": 100  // optional
  }
  ```
## Error Handling

The API returns appropriate HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (Twitter API authentication issues)
- 404: Not Found
- 429: Too Many Requests (Twitter API rate limit)
- 500: Internal

🛠️ TODO: Tweets/Users Feature Improvements

- [ ] **Integrate `since_id`** for incremental tweet/user fetching.

- [ ] **Improve pagination handling**, especially with:
  - `since_id`
  - Tracking the **last tweet ID** to ensure continuity.

- [ ] **Handle tweet metric updates** in the database:
  - Re-fetch tweets periodically to update changing metrics (likes, retweets, replies, etc.).
  - Compare and update only if values have changed to reduce DB writes.

- [ ] **Implement Django REST Framework serializers**:
  - Replace manual data transformation with DRF serializers for cleaner, more maintainable code.

- [ ] **Clean up and organize code** for better readability and maintainability.