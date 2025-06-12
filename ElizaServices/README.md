# ElizaServices

**ElizaServices** is a Django-based REST API offering AI-powered text and image analysis tools. It includes capabilities like content popularity prediction, safety scoring, hashtag comparison, image captioning, environmental news summarization, and smart tweet management.

---

## 🚀 Features

### 🔥 1. Popularity Prediction
- Predicts content popularity scores (0-100)
- Accepts both text and image input
- Supports hashtag comparison for engagement optimization

### 🛡️ 2. Safety Analysis
- Detects toxic or inappropriate language
- Analyzes both raw text and image-derived captions
- Provides category-wise toxicity scores

### 🖼️ 4. Image Processing
- Generates captions from uploaded images using AWS Rekognition
- Fetches image URLs using keyword search via Pexels

### 🌍 5. Environmental News Summarizer
- Uses LLMs to summarize climate-related news
- Analyzes tone and personality traits of each article

### 🐦 6. Tweet Management
- Supports different tweet types (e.g., CarbonTruth, CarbonRant)
- Allows CRUD operations on tweets
- Retrieves latest tweet per sender
- Manages tweet queues with scheduling and filters

---

## 🔗 API Endpoints

### 📊 Popularity Endpoints
| Endpoint                         | Method | Description                                  |
|----------------------------------|--------|----------------------------------------------|
| `/api/popularity/`              | POST   | Get popularity score for content (text/image) |
| `/api/compare_hashtags/`        | POST   | Compare hashtags based on predicted score     |

### 🛡️ Safety Endpoints
| Endpoint                         | Method | Description                                  |
|----------------------------------|--------|----------------------------------------------|
| `/api/safety/`                  | POST   | Get safety score for content (text/image)     |

### 🌟 Emotion Detection And Personality Detection
> Internally used in Environmental News

### 🖼️ Image Utilities
| Endpoint                         | Method | Description                                  |
|----------------------------------|--------|----------------------------------------------|
| `/api/imagegen/`                | POST   | Get a relevant image URL from Pexels         |

### 📰 Environmental News
| Endpoint                         | Method | Description                                  |
|----------------------------------|--------|----------------------------------------------|
| `/api/news/`                    | GET    | Get recent environmental news by country     |

### 🐦 Tweet Management
| Endpoint                               | Method | Description                                      |
|----------------------------------------|--------|--------------------------------------------------|
| `/api/tweets/`                         | GET/POST | List or create tweet by sender type              |
| `/api/tweets/latest/?sender=<type>`    | GET    | Get most recent tweet for a sender               |
| `/api/tweets/<tweet_id>/?sender=<type>` | GET    | Get a specific tweet by ID                       |
| `/api/tweets/senders/`                 | GET    | Get list of valid tweet sender types             |

### ⏳ Queued Tweet Management
| Endpoint                                        | Method | Description                                      |
|-------------------------------------------------|--------|--------------------------------------------------|
| `/api/queuedtweets/`                          | POST | List pending tweets |


---

## ⚙️ Setup and Installation
```bash
Python version: 3.10.13
Pip version: 23.0.1
```
1. Create a virtual environment:Add commentMore actions
```bash
python -m venv elizaservicevenv
# OR
python3 -m venv elizaservicevenv
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
# OR
python3 manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
# OR
python3 manage.py runserver
```

## Dependencies

- django>=4.0
- djangorestframework>=3.13
- python-decouple
- boto3
- pillow
- torch>=1.10.0
- sentence-transformers
- psycopg2-binary>=2.9.9
- beautifulsoup4>=4.9.3
- requests>=2.25.1


## 🗂️ Project Structure
```text
elizaservices/
├── elizaservices/             # Django project settings
├── elizaservicesapi/          # Main API app
│   ├── utils/                 # Modular AI services
│   │   ├── caption_service/        # Image captioning functionality (Used Internally with other services)
│   │   ├── imagegen_service/       # Image generation logic
│   │   ├── news_service/           # Environmental news summarization
│   │   ├── personality_service/    # Provides best personality for each news article (Used Internally with news services)
│   │   ├── popularity_service/     # Popularity prediction
│   │   ├── safety_service/         # Content safety analysis
│   │   ├── text_emotion_service/   # Sentiment of each news article (Used Internally with news services)
│   ├── models.py              # Data models
│   ├── views.py               # API endpoints
│   ├── urls.py                # URL routing
│   └── serializers.py         # Data serializers
└── manage.py                  # Django management script
