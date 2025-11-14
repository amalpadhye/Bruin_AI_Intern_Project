# ForkU Backend

Backend API for ForkU - Food tracking and social app for UCLA students.

## Architecture

- **Framework**: FastAPI (Python 3.12)
- **Deployment**: AWS ECS Fargate
- **Database**: Aurora PostgreSQL Serverless v2
- **Storage**: Amazon S3
- **Cache**: Redis (ElastiCache)
- **Scheduling**: EventBridge → ECS tasks

## Features

### Cal AI Integration
- Food image analysis via Cal AI API
- Response normalization
- Discrepancy detection vs menu data
- Confidence threshold validation

### UCLA Menu Scraping
- API-first approach (UCLA official API)
- Web scraping fallback
- Daily automated scraping via EventBridge
- S3 storage for raw data
- Postgres normalization pipeline

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Required environment variables:**
   - `CAL_AI_API_KEY`: Cal AI API key
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
   - `S3_BUCKET_RAW`, `S3_BUCKET_DERIVED`, `S3_BUCKET_MEDIA`: S3 bucket names
   - `DATABASE_URL`: PostgreSQL connection string
   - `API_SECRET_KEY`: Secret for admin endpoints

4. **Run locally:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Run scraper task:**
   ```bash
   python -m app.tasks.scraper_task [YYYY-MM-DD]
   ```

## API Endpoints

### Scan
- `POST /scan` - Analyze food image with Cal AI

### Menus
- `GET /menus?date=YYYY-MM-DD&hall=name` - Get menu data
- `GET /menus/items/{item_id}` - Get menu item details

### Uploads
- `GET /uploads/presign?contentType=image/jpeg` - Get presigned S3 URL

### Admin
- `POST /tasks/scrape-ucla?date=YYYY-MM-DD` - Trigger menu scraping (requires X-Secret header)

## Deployment

### Docker Build
```bash
docker build -t forku-backend .
```

### ECS Fargate
- Build and push to ECR
- Create ECS task definition
- Set up EventBridge rule for daily scraping
- Configure ALB/API Gateway in front

## Cal AI Integration

The Cal AI client (`app/services/cal_ai_client.py`) handles:
- Image analysis via `/scan-image` endpoint
- Response normalization to standard format
- Discrepancy calculation vs menu data
- Confidence threshold validation

## UCLA Scraper

The scraper (`app/services/ucla_scraper.py`) supports:
1. **UCLA API** (if access granted): Official API endpoint
2. **Web scraping fallback**: Scrapes from dining.ucla.edu JSON endpoints

The scraper task (`app/tasks/scraper_task.py`) is designed to run as an ECS Fargate task triggered by EventBridge.

## Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── api/                 # API routes
│   ├── scan.py         # Food scanning endpoints
│   ├── menus.py        # Menu endpoints
│   ├── uploads.py      # Presigned URL generation
│   └── admin.py        # Admin tasks
├── services/           # Business logic
│   ├── cal_ai_client.py    # Cal AI integration
│   ├── ucla_scraper.py     # Menu scraping
│   └── s3_service.py        # S3 operations
└── tasks/              # Background tasks
    └── scraper_task.py     # ECS scraper task
```

## Notes

- Cal AI API structure may vary - adjust `normalize_response()` based on actual API response
- UCLA API access requires approval from MyUCLA IWE partners
- Web scraping fallback may break if UCLA website structure changes
- All S3 operations use presigned URLs for security

