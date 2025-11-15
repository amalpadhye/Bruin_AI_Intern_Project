# ForkU Backend

Backend API for ForkU - Food tracking and social app for UCLA students.

## Features

### Food Image Analysis
- **ChatGPT Vision integration**: Analyzes food images, identifies multiple foods
- **Menu matching**: Matches foods to UCLA dining hall menu items
- **Serving size estimation**: Estimates portion sizes in ounces and adjusts calories
- **Calorie comparison**: Compares ChatGPT estimates vs menu calories with warnings
- **Unmatched food handling**: Suggests food names and calories for items not on menu
- **Detailed classification**: Shows what ChatGPT sees (description, visual features, ingredients)

### UCLA Menu Scraping
- **Historical scraping**: Scrapes up to 90 days of menu data
- **Bulk operations**: Scrape date ranges or recent days
- **Database storage**: Automatically stores unique menu items with nutrition data
- **Dining hall filtering**: Filter by specific dining halls
- **API-first approach**: Uses UCLA official API when available
- **Web scraping fallback**: Falls back to web scraping if API unavailable

## Prerequisites

- **Python 3.12+** (tested with Python 3.13)
- **PostgreSQL** (local or remote)
- **AWS Account** (for S3 storage)
- **OpenAI API Key** (for ChatGPT Vision)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Bruin_AI_Intern_Project
```

### 2. Set Up Virtual Environment

```bash
# Run the setup script (creates venv and installs dependencies)
./setup_venv.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/forku_db

# AWS Configuration
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_RAW=your-raw-bucket-name
S3_BUCKET_DERIVED=your-derived-bucket-name
S3_BUCKET_MEDIA=your-media-bucket-name

# API Configuration
API_SECRET_KEY=your_secret_key_for_admin_endpoints

# Optional: UCLA API (if you have access)
UCLA_API_KEY=your_ucla_api_key
```

### 4. Set Up Database

```bash
# Create database (if using local PostgreSQL)
createdb forku_db

# Run database migrations
alembic upgrade head
```

### 5. Populate Menu Data

```bash
# Scrape last 90 days of menu data and store in database
python3 scripts/scrape_and_store.py 90
```

### 6. Start the API Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server
uvicorn app.main:app --reload

# Server will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 7. Test the Application

Open `test_ui.html` in your browser to test the food scanning functionality.

## Project Structure

```
Bruin_AI_Intern_Project/
├── alembic/              # Database migrations
│   ├── versions/         # Migration scripts
│   └── env.py           # Alembic environment
├── app/                  # Main application
│   ├── api/             # API endpoints
│   │   ├── scan.py      # Food scanning endpoints
│   │   ├── menus.py     # Menu endpoints
│   │   ├── uploads.py   # Presigned URL generation
│   │   ├── admin.py     # Admin tasks
│   │   └── scraper_bulk.py  # Bulk scraping endpoints
│   ├── db/              # Database layer
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── database.py  # Database connection
│   │   └── crud.py      # CRUD operations
│   ├── services/        # Business logic
│   │   ├── chatgpt_service.py  # ChatGPT Vision integration
│   │   ├── ucla_scraper.py     # Menu scraping
│   │   ├── historical_scraper.py  # Historical scraping
│   │   ├── s3_service.py       # S3 operations
│   │   └── cal_ai_client.py   # Cal AI (optional, unused)
│   ├── tasks/           # Background tasks
│   │   └── scraper_task.py    # ECS scraper task
│   ├── config.py        # Configuration management
│   └── main.py          # FastAPI application
├── scripts/             # Utility scripts
│   ├── scrape_and_store.py  # Scrape and store menu data
│   └── update_nutrition.py   # Update nutrition data for existing items
├── venv/                # Virtual environment (created by setup)
├── requirements.txt     # Python dependencies
├── setup_venv.sh        # Virtual environment setup script
├── alembic.ini         # Alembic configuration
├── test_ui.html        # Testing UI for food scanning
└── .env                # Environment variables (create this)
```

## API Endpoints

### Scan
- `POST /scan?dining_halls=name1,name2` - Analyze food image, match to menu items
  - Upload image file
  - Returns matched and unmatched foods with details

### Menus
- `GET /menus?date=YYYY-MM-DD&hall=name` - Get menu data for specific date/hall
- `GET /menus/items/{item_id}` - Get menu item details

### Scraper
- `POST /scraper/scrape-recent?days=N` - Scrape last N days (requires `X-Secret` header)
- `POST /scraper/bulk-scrape?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Scrape date range

### Uploads
- `GET /uploads/presign?contentType=image/jpeg` - Get presigned S3 URL for direct upload

### Admin
- `POST /tasks/scrape-ucla?date=YYYY-MM-DD` - Trigger single-day scrape (requires `X-Secret` header)

### Health
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API info

## Development

### Running Tests

```bash
# Test database connection
python3 test_db.py

# Test S3 connection
python3 test_s3.py

# Test scraper
python3 test_scraper.py
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Updating Menu Data

```bash
# Scrape and store recent days
python3 scripts/scrape_and_store.py 30

# Update nutrition data for existing items
python3 scripts/update_nutrition.py
```

## Dependencies

### Core
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and settings
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **psycopg** - PostgreSQL adapter (v3)

### AWS
- **boto3** - AWS SDK for Python

### HTTP & Scraping
- **httpx** - Async HTTP client
- **requests** - HTTP library
- **beautifulsoup4** - HTML parsing
- **lxml** - XML/HTML parser

### AI
- **openai** - OpenAI API client (ChatGPT Vision)

### Utilities
- **python-dotenv** - Environment variable management
- **python-multipart** - File upload support

## Architecture

- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (Aurora Serverless v2 planned for production)
- **Storage**: Amazon S3 (raw data, derived data, media)
- **AI**: OpenAI ChatGPT Vision API
- **Deployment**: Local development (ECS Fargate planned)

## Key Components

### ChatGPT Vision Service
- Analyzes food images using OpenAI's GPT-4 Vision
- Identifies multiple foods per image
- Matches to menu items with flexible matching
- Estimates serving sizes in ounces
- Provides suggestions for unmatched foods

### UCLA Scraper
- **API-first**: Uses UCLA official API when available
- **Web scraping fallback**: Scrapes from dining.ucla.edu if API unavailable
- **Historical scraping**: Can scrape date ranges
- **Database storage**: Automatically stores unique items with nutrition data

### Database
- **PostgreSQL**: Stores menu items with nutrition data
- **Alembic**: Database migrations for schema versioning
- **SQLAlchemy**: ORM for type-safe operations

## Documentation

- **[STATUS.md](STATUS.md)**: Detailed project status, what works, what doesn't, what needs to be done

## Troubleshooting

### Virtual Environment Issues

```bash
# If dependencies fail to install, try:
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
brew services list  # macOS
# or
sudo systemctl status postgresql  # Linux

# Test connection
python3 test_db.py
```

### S3 Connection Issues

```bash
# Verify AWS credentials
aws configure list

# Test S3 connection
python3 test_s3.py
```

## Notes

- **ChatGPT Vision** is the primary food analysis method (Cal AI integration exists but unused)
- **UCLA API** access requires approval from MyUCLA IWE partners
- **Web scraping fallback** may break if UCLA website structure changes
- **Nutrition data** extraction from menus is being improved
- All **S3 operations** use presigned URLs for security
- **CORS** currently allows all origins (change for production)

## License

See [LICENSE.md](LICENSE.md) for details.
