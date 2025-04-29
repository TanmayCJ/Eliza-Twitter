# ElizaServices

ElizaServices is a Django-based REST API service that provides various AI-powered text and image analysis capabilities, including popularity prediction, safety checking, and image captioning.

## Features

### 1. Popularity Prediction
- Predicts the potential popularity of text content using advanced ML models
- Provides popularity scores on a scale of 0-100
- Supports hashtag comparison to find the most effective tags

### 2. Safety Analysis
- Analyzes text content for appropriateness
- Uses the Toxic-BERT model for content moderation
- Provides detailed toxicity scores across multiple categories

### 3. Image Processing
- Generates captions for images
- Integrates image analysis with text analysis for comprehensive content evaluation

### 4. Tweet Management
- Supports multiple tweet types:
  - CarbonTruth Tweets
  - CarbonRant Tweets
  - Default Tweets
  - CarbonSustainAI Tweets
- CRUD operations for tweet management
- Latest tweet retrieval functionality

## API Endpoints

### Popularity Endpoints
- `POST /api/popularity/`: Get popularity score for text/image content
- `POST /api/compare_hashtags/`: Compare effectiveness of different hashtags

### Safety Endpoints
- `POST /api/safety/`: Get safety analysis for text/image content

### Tweet Endpoints
- `GET/POST /api/tweets/`: List all tweets or create new tweet
- `GET /api/tweets/latest/`: Get the most recent tweet
- `GET /api/tweets/<tweet_id>/`: Get specific tweet details
- `GET /api/tweets/senders/`: List all valid tweet sender types

## Setup and Installation

1. Create a virtual environment:
```bash
python -m venv elizaservicevenv
```

2. Activate the virtual environment:
```bash
# On Windows
elizaservicevenv\Scripts\activate
# On macOS/Linux
source elizaservicevenv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in a `.env` file:
```env
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Dependencies

- Django >= 4.0
- Django REST Framework >= 3.13
- Python-decouple
- Detoxify
- Boto3
- Pillow
- PyTorch >= 1.10.0
- Sentence-transformers
- Transformers
- Huggingface-hub == 0.10.1
- psycopg2-binary >= 2.9.9

## Project Structure
elizaservices/
├── elizaservices/ # Main Django project settings
├── elizaservicesapi/ # Main API application
│ ├── utils/
│ │ ├── caption_service/ # Image captioning functionality
│ │ ├── popularity_service/ # Popularity prediction
│ │ └── safety_service/ # Content safety analysis
│ ├── views.py # API endpoints
│ ├── urls.py # URL routing
│ ├── models.py # Data models
│ └── serializers.py # Data serializers
└── manage.py # Django management script


## API Usage Examples

### Predict Content Popularity
```bash
curl -X POST http://localhost:8000/api/popularity/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Your content here"}'
```

### Check Content Safety
```bash
curl -X POST http://localhost:8000/api/safety/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Content to check"}'
```

### Compare Hashtags
```bash
curl -X POST http://localhost:8000/api/compare_hashtags/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Base content",
    "hashtags": ["#tag1", "#tag2"],
    "top_n": 1
  }'
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

[Add your license information here]