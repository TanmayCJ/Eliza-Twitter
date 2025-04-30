# TwitterModerator API Documentation

## Base URL
`/api/`

## Endpoints

### 1. Calculate Popularity Score
**Endpoint**: `POST /api/popularity/`  
**Description**: Predicts tweet popularity and suggests hashtags  
**Parameters**:
- `text` (string, optional): Tweet content
- `image` (file, optional): Image attachment

**Example Request**:
```bash
curl -X POST -F "text=New product launch!" -F "image=@demo.jpg" http://localhost:8000/api/popularity/
```

**Success Response**:
```json
{
  "popularity_score": 0.82,
  "hashtag_suggestions": ["#innovation", "#tech", "#newproduct"]
}
```

### 2. Safety Evaluation
**Endpoint**: `POST /api/safety/`  
**Description**: Assesses content safety for text and images  
**Parameters**:
- `text` (string, optional): Text content
- `image` (file, optional): Image to analyze

**Example Response**:
```json
{
  "text_safety": {
    "score": 0.94,
    "flags": ["violence: 0.02", "hate_speech: 0.01"]
  },
  "image_safety": {
    "score": 0.88,
    "flags": ["explicit: 0.12"]
  }
}
```

### 3. Hashtag Comparison
**Endpoint**: `POST /api/compare_hashtags/`  
**Description**: Ranks hashtag effectiveness  
**Parameters**:
- `hashtags` (array): List of hashtags to compare
- `text` (string, optional): Context text
- `top_n` (number): Number of top hashtags to return
- `image` (file, optional): Related image

**Example Request**:
```json
{
  "hashtags": ["#sustainability", "#eco", "#green"],
  "top_n": 2
}
```

**Response**:
```json
{
  "top_hashtags": [
    {"hashtag": "#sustainability", "score": 0.91},
    {"hashtag": "#eco", "score": 0.85}
  ]
}
```

### 4. Tweet Management
**Endpoint**: `GET /api/tweets/`  
**Description**: Retrieve filtered tweets  
**Query Params**:
- `sender` (string): Filter by author
- `limit` (number): Max results

**Example Response**:
```json
{
  "tweets": [
    {
      "id": "twt_123",
      "content": "Climate action now!",
      "author": "eco_warrior",
      "engagement": 142
    }
  ]
}
```

**Endpoint**: `POST /api/tweets/`  
**Description**: Create new tweet  
**Request Body**:
```json
{
  "text": "Renewable energy breakthroughs!",
  "sender": "green_tech",
  "media": {"type": "video", "url": "https://example.com/demo.mp4"}
}
```

### 5. Latest Tweet
**Endpoint**: `GET /api/tweets/latest/`  
**Description**: Get most recent tweet  
**Query Param**:
- `sender` (string): Filter by author

**Response**:
```json
{
  "id": "twt_456",
  "text": "Just planted 1000 trees!",
  "timestamp": "2023-07-25T09:30:00Z"
}
```

### 6. Valid Senders
**Endpoint**: `GET /api/tweets/senders/`  
**Description**: List authorized accounts  
**Response**:
```json
{
  "valid_senders": ["eco_news", "climate_facts", "green_tech"]
}
```

### 7. Tweet Details
**Endpoint**: `GET /api/tweets/{tweet_id}/`  
**Description**: Get specific tweet metadata  
**Parameters**:
- `tweet_id` (path): Unique tweet identifier
- `sender` (query): Verify ownership

**Example Response**:
```json
{
  "id": "twt_789",
  "content": "Carbon footprint reduction tips",
  "metrics": {
    "impressions": 1500,
    "engagements": 234,
    "shares": 45
  },
  "safety_rating": "A"
}
```

## Error Responses
All endpoints return standardized errors:
```json
{
  "error": {
    "code": 404,
    "message": "Tweet not found",
    "details": "No tweet exists with ID twt_999"
  }
}
```

## Testing Recommendations
1. Use Postman for endpoint testing
2. For image uploads:
```bash
curl -F "image=@/path/to/image.jpg" http://localhost:8000/api/safety/
```
3. Include headers:
```http
Content-Type: multipart/form-data
Accept: application/json
```

```
