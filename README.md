# ForkU Backend

Backend API for ForkU - Food tracking and social app for UCLA students.

## Architecture

- **Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL (Aurora Serverless v2 planned)
- **Storage**: Amazon S3
- **AI**: OpenAI ChatGPT Vision API
- **Deployment**: Local development (ECS Fargate planned)

## Current Features

### Food Image Analysis
- **ChatGPT Vision integration**: Analyzes food images, identifies multiple foods
- **Menu matching**: Matches foods to UCLA dining hall menu items
- **Serving size estimation**: Estimates portion sizes and adjusts calories
- **Calorie comparison**: Compares ChatGPT estimates vs menu calories
- **Unmatched food handling**: Suggests food names and calories for items not on menu
- **Detailed classification**: Shows what ChatGPT sees (description, visual features, ingredients)

### UCLA Menu Scraping
- **Historical scraping**: Scrapes up to 90 days of menu data
- **Bulk operations**: Scrape date ranges or recent days
- **Database storage**: Automatically stores unique menu items
- **Dining hall filtering**: Filter by specific dining halls
- **API-first approach**: Uses UCLA official API when available
- **Web scraping fallback**: Falls back to web scraping if API unavailable

## Quick Start

See [STATUS.md](STATUS.md) for detailed setup instructions and current state.

**Quick setup:**
```bash
# Install dependencies
pip install -r requirements.txt

# Create database
createdb forku_db

# Run migrations
alembic upgrade head

# Scrape menu data
python3 scripts/scrape_and_store.py 90

# Start API
uvicorn app.main:app --reload

# Open test UI
open test_ui.html
```

## Required Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for ChatGPT Vision
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://localhost:5432/forku_db`)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AWS_REGION`: AWS region (e.g., `us-east-2`)
- `S3_BUCKET_RAW`, `S3_BUCKET_DERIVED`, `S3_BUCKET_MEDIA`: S3 bucket names
- `API_SECRET_KEY`: Secret for admin endpoints

## API Endpoints

### Scan
- `POST /scan?dining_halls=name1,name2` - Analyze food image, match to menu items

### Menus
- `GET /menus?date=YYYY-MM-DD&hall=name` - Get menu data
- `GET /menus/items/{item_id}` - Get menu item details

### Scraper
- `POST /scraper/scrape-recent?days=N` - Scrape last N days (requires X-Secret header)
- `POST /scraper/bulk-scrape?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Scrape date range

### Uploads
- `GET /uploads/presign?contentType=image/jpeg` - Get presigned S3 URL

### Admin
- `POST /tasks/scrape-ucla?date=YYYY-MM-DD` - Trigger single-day scrape (requires X-Secret header)

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

## Key Components

### ChatGPT Vision Service
- Analyzes food images using OpenAI's GPT-4 Vision
- Identifies multiple foods per image
- Matches to menu items
- Estimates serving sizes and calories
- Provides suggestions for unmatched foods

### UCLA Scraper
- **API-first**: Uses UCLA official API when available
- **Web scraping fallback**: Scrapes from dining.ucla.edu if API unavailable
- **Historical scraping**: Can scrape date ranges
- **Database storage**: Automatically stores unique items

### Database
- **PostgreSQL**: Stores menu items with nutrition data
- **Alembic**: Database migrations
- **SQLAlchemy**: ORM for type-safe operations

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

## Documentation

- **[STATUS.md](STATUS.md)**: Current project status, what works, what doesn't, what needs to be done

## Notes

- **ChatGPT Vision** is the primary food analysis method (Cal AI integration exists but unused)
- **UCLA API** access requires approval from MyUCLA IWE partners
- **Web scraping fallback** may break if UCLA website structure changes
- **Nutrition data** extraction from menus is incomplete (most items have `calories = None`)
- All **S3 operations** use presigned URLs for security
- **CORS** currently allows all origins (change for production)

