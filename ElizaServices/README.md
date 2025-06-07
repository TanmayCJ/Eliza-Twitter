# ElizaServices

**ElizaServices** is a Django-based REST API offering AI-powered text and image analysis tools. It includes capabilities like content popularity prediction, safety scoring, hashtag comparison, image captioning, personality and emotion detection, environmental news summarization, and smart tweet management.

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

### 🧠 3. Emotion & Personality Analysis
- Extracts top emotional sentiments using AWS Comprehend
- Matches emotions to predefined personality archetypes

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

### 🧠 Personality Analysis
| Endpoint                         | Method | Description                                  |
|----------------------------------|--------|----------------------------------------------|
| `/api/personality-analysis/`    | POST   | Analyze personality from a list of emotions   |

### 🌟 Emotion Detection
> Internally used in personality and news modules via AWS Comprehend

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
| `/api/queued-tweets/`                          | GET/POST | List or create queued tweets (filters optional)  |
| `/api/queued-tweets/<pk>/`                     | GET/PUT/DELETE | Get, update, or delete a specific queued tweet |

---

## ⚙️ Setup and Installation