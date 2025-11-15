# ForkU Project Status

## Overview

ForkU is a food tracking and social app for UCLA students. This document describes the current state of the backend API, what's working, what's not, and what needs to be done.

## Architecture & Design Decisions

### Why These Choices?

- **FastAPI**: Modern async Python framework, fast, great docs, auto-generated API docs
- **ChatGPT Vision (not Cal AI)**: More flexible, better at multi-food detection, handles unmatched foods gracefully
- **PostgreSQL**: Relational data (menus, users, meals), ACID compliance, complex queries
- **S3**: Scalable image storage, presigned URLs for security, cost-effective
- **Alembic**: Database migrations, version control for schema changes
- **SQLAlchemy**: ORM for type-safe database operations

## ✅ What's Set Up & Working

### 1. Database Layer

- ✅ **PostgreSQL models** (`app/db/models.py`): `MenuItem` table with all nutrition fields
- ✅ **Database connection** (`app/db/database.py`): SQLAlchemy session management
- ✅ **CRUD operations** (`app/db/crud.py`): Query, create, update menu items
- ✅ **Alembic migrations**: Schema versioning ready (migration created)
- ✅ **Database populated**: 316+ menu items scraped and stored

### 2. Food Scanning System

- ✅ **ChatGPT Vision integration** (`app/services/chatgpt_service.py`):
  - Analyzes food images
  - Identifies multiple foods per image
  - Matches to menu items
  - Estimates serving sizes and calories
  - Provides detailed classification (description, visual features, ingredients)
  - Suggests food names/calories for unmatched items
- ✅ **Scan endpoint** (`app/api/scan.py`):
  - Uploads images to S3
  - Queries database for menu items
  - Filters by dining halls
  - Returns matched + unmatched foods with full details
  - Handles errors gracefully (timeouts, API errors)
- ✅ **S3 integration** (`app/services/s3_service.py`):
  - Uploads scan images
  - Stores raw menu data
  - Generates presigned URLs

### 3. Menu Scraping System

- ✅ **UCLA scraper** (`app/services/ucla_scraper.py`):
  - API-first approach (UCLA official API)
  - Web scraping fallback
  - Extracts menu items with nutrition data
- ✅ **Historical scraper** (`app/services/historical_scraper.py`):
  - Scrapes date ranges
  - Extracts unique items across dates
  - Aggregates dining halls and services
- ✅ **Bulk scraper endpoint** (`app/api/scraper_bulk.py`):
  - Scrapes last N days (up to 90)
  - Scrapes date ranges
  - Automatically stores in database
  - Filters by dining halls
- ✅ **Scraper script** (`scripts/scrape_and_store.py`):
  - Easy command-line interface
  - Automatically stores results

### 4. API Endpoints

- ✅ `POST /scan` - Food image analysis with menu matching
- ✅ `GET /menus` - Get menu data for date/hall
- ✅ `GET /menus/items/{item_id}` - Get menu item details
- ✅ `GET /uploads/presign` - Generate presigned S3 URLs
- ✅ `POST /scraper/scrape-recent` - Bulk scrape recent days
- ✅ `POST /scraper/bulk-scrape` - Scrape date range
- ✅ `POST /store/menu-items` - Manually store scraped items
- ✅ `POST /tasks/scrape-ucla` - Trigger single-day scrape
- ✅ `GET /health` - Health check

### 5. Testing UI

- ✅ **HTML/JavaScript UI** (`test_ui.html`):
  - Image upload
  - Dining hall filtering
  - Displays all foods (matched + unmatched)
  - Shows classification details
  - Shows calories comparison
  - Shows ChatGPT suggestions for unmatched foods

### 6. Configuration

- ✅ **Environment-based config** (`app/config.py`):
  - Pydantic settings validation
  - Supports .env file
  - Optional Cal AI (not currently used)
  - AWS region configuration

## ⚠️ What's Partially Working

### 1. Menu Item Nutrition Data

- ⚠️ **Issue**: Most menu items in database have `calories = None`
- ⚠️ **Why**: UCLA scraper doesn't always extract nutrition data
- ⚠️ **Impact**: System still works (uses ChatGPT estimates), but can't compare to menu calories
- ✅ **Workaround**: ChatGPT provides calorie estimates, system handles None gracefully

### 2. Timeout Handling

- ⚠️ **Issue**: Large images or slow OpenAI responses can timeout
- ✅ **Fixed**: Increased timeouts (60s for analysis, 45s for suggestions)
- ✅ **Fixed**: Better error messages for timeouts
- ⚠️ **Remaining**: May still timeout on very large images

## ❌ What Doesn't Work Yet

### 1. Authentication

- ❌ No Auth0 integration
- ❌ No JWT token validation
- ❌ User ID is hardcoded as "temp_user"
- **Impact**: Can't track which user uploaded what

### 2. User & Social Features

- ❌ No user profiles
- ❌ No meal logs
- ❌ No posts/votes/comments
- ❌ No recommendations
- **Impact**: Core social features missing

### 3. Menu Item Nutrition Extraction

- ❌ Nutrition data not reliably extracted from UCLA menus
- ❌ No fallback to fetch nutrition from external APIs
- **Impact**: Can't compare ChatGPT estimates to menu calories

### 4. Production Deployment

- ❌ No ECS Fargate deployment
- ❌ No EventBridge scheduling
- ❌ No ALB/API Gateway
- ❌ No secrets management (AWS Secrets Manager)
- ❌ No monitoring/alerting
- **Impact**: Can't run in production

### 5. Error Recovery

- ❌ No retry logic for failed API calls
- ❌ No queue system for failed scrapes
- ❌ No dead letter queue
- **Impact**: Manual intervention needed for failures

## 📋 What Needs to Be Done

### High Priority

1. **Extract Nutrition Data from Menus**

   - Improve UCLA scraper to extract nutrition from menu pages
   - Or integrate with nutrition API (e.g., USDA FoodData Central)
   - Store nutrition data in database

2. **Authentication**

   - Integrate Auth0
   - Add JWT validation middleware
   - Extract user_id from tokens
   - Protect admin endpoints

3. **User & Meal Logging**
   - Create user/profile models
   - Create meal_logs table
   - Add endpoints: `POST /me/meals`, `GET /me/meals`
   - Store scan results as meal logs

### Medium Priority

4. **Production Deployment**

   - Set up ECS Fargate task definitions
   - Configure EventBridge for daily scraping
   - Set up ALB/API Gateway
   - Configure AWS Secrets Manager
   - Add CloudWatch logging/metrics

5. **Social Features**

   - Create posts/votes/comments models
   - Add endpoints for social features
   - Implement ranking algorithm

6. **Recommendations**
   - Implement V0 rules-based recommendations
   - Add recommendation endpoint

### Low Priority

7. **Error Handling**

   - Add retry logic with exponential backoff
   - Set up SQS for failed jobs
   - Add dead letter queue

8. **Performance**

   - Add Redis caching for menu queries
   - Optimize database queries
   - Add pagination

9. **Testing**
   - Unit tests for services
   - Integration tests for endpoints
   - E2E tests for full flow

## 🚀 Quick Start (Current State)

### Prerequisites

- Python 3.8+
- PostgreSQL running
- AWS credentials configured
- OpenAI API key

### Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**

   ```bash
   # Create .env file with:
   DATABASE_URL=postgresql://localhost:5432/forku_db
   OPENAI_API_KEY=your-key-here
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   AWS_REGION=us-east-2
   S3_BUCKET_RAW=forku-raw-alexmarkova
   S3_BUCKET_DERIVED=forku-derived-alexmarkova
   S3_BUCKET_MEDIA=forku-media-alexmarkova
   API_SECRET_KEY=your-secret-key
   ```

3. **Create database:**

   ```bash
   createdb forku_db
   ```

4. **Run migrations:**

   ```bash
   alembic upgrade head
   ```

5. **Scrape menu data:**

   ```bash
   python3 scripts/scrape_and_store.py 90
   ```

6. **Start API:**

   ```bash
   uvicorn app.main:app --reload
   ```

7. **Test UI:**
   - Open `test_ui.html` in browser
   - Upload food image
   - See results!

## 🧪 How to Run and Test

### Running the API

1. **Start the API server:**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

2. **Check API is running:**

   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

3. **View API documentation:**
   - Open `http://localhost:8000/docs` in browser
   - Interactive Swagger UI for testing endpoints

### Testing the Scan Endpoint

#### Option 1: Using the Test UI (Easiest)

1. **Open the test UI:**

   ```bash
   open test_ui.html
   # Or manually open test_ui.html in your browser
   ```

2. **Configure:**

   - API Base URL: `http://localhost:8000` (should be default)
   - Dining Halls (optional): `Bruin Plate, Epicuria`

3. **Upload an image:**

   - Click the upload area or drag & drop a food image
   - Click "Scan Food Image"
   - Wait for results (may take 10-30 seconds)

4. **Check results:**
   - Should show all foods identified
   - Matched foods show menu item details
   - Unmatched foods show ChatGPT suggestions
   - Serving sizes should be in ounces (oz)

#### Option 2: Using curl

```bash
# Test scan endpoint
curl -X POST "http://localhost:8000/scan?dining_halls=Bruin%20Plate" \
  -F "image=@/path/to/your/food/image.jpg"

# Response will be JSON with food analysis
```

#### Option 3: Using Python

```python
import requests

# Test scan endpoint
with open('food_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/scan',
        params={'dining_halls': 'Bruin Plate'},
        files={'image': f}
    )
    print(response.json())
```

### Testing the Menu Endpoint

```bash
# Get menu for today
curl "http://localhost:8000/menus"

# Get menu for specific date
curl "http://localhost:8000/menus?date=2025-01-15"

# Get menu for specific dining hall
curl "http://localhost:8000/menus?hall=Bruin%20Plate"

# Get menu for date and hall
curl "http://localhost:8000/menus?date=2025-01-15&hall=Bruin%20Plate"
```

### Testing the Scraper

```bash
# Scrape last 5 days (for testing)
python3 scripts/scrape_and_store.py 5

# Scrape with dining hall filter
python3 scripts/scrape_and_store.py 5 "Bruin Plate"

# Or use the API endpoint (requires API_SECRET_KEY)
curl -X POST "http://localhost:8000/scraper/scrape-recent?days=5&store_in_db=true" \
  -H "X-Secret: your-api-secret-key"
```

### Testing Database

```bash
# Connect to database
psql forku_db

# Check menu items
SELECT COUNT(*) FROM menu_items;

# See sample items
SELECT name, calories, dining_hall, service
FROM menu_items
WHERE calories IS NOT NULL
LIMIT 10;

# Check items with nutrition
SELECT name, calories, protein_g, fat_g, carbs_g
FROM menu_items
WHERE calories IS NOT NULL
LIMIT 10;

# Exit
\q
```

### Expected Test Results

#### Successful Scan:

- ✅ Returns JSON with `foods` array
- ✅ Each food has `matched: true/false`
- ✅ Matched foods have `matched_item` with menu details
- ✅ Unmatched foods have `suggestion` with ChatGPT recommendations
- ✅ Serving sizes are in ounces (e.g., "4 oz", "6 oz")
- ✅ Calories are estimated for each food
- ✅ Total calories calculated

#### Successful Menu Query:

- ✅ Returns JSON with `dining_halls` object
- ✅ Each dining hall has menu items
- ✅ Items have name, calories, serving_size, ingredients
- ✅ Filtered by date/hall if specified

#### Common Issues:

1. **"No menu items found"**

   - Solution: Run scraper first: `python3 scripts/scrape_and_store.py 90`

2. **"OpenAI API key not configured"**

   - Solution: Add `OPENAI_API_KEY=your-key` to `.env` file

3. **"Request timed out"**

   - Solution: Try smaller image or wait and retry

4. **"Error fetching menu"**
   - Solution: Check database has items, or scraper is working

### Performance Testing

```bash
# Test scan endpoint performance
time curl -X POST "http://localhost:8000/scan" \
  -F "image=@test_image.jpg"

# Should complete in 10-30 seconds typically
```

### Integration Testing

1. **Full flow test:**
   - Scrape menus → Store in DB → Query menu endpoint → Scan food image → Match to menu
2. **Test with multiple foods:**

   - Upload image with multiple foods on one plate
   - Should identify all foods separately

3. **Test unmatched foods:**
   - Upload image of food not on menu
   - Should show ChatGPT suggestion with calories

## 📊 Current Database State

- **Menu items**: 316+ items stored
- **Nutrition data**: Most items missing calories (None) - **FIXED**: Scraper now fetches nutrition from detail pages
- **Dining halls**: Multiple halls scraped (Bruin Plate, etc.)
- **Dates**: Last 90 days scraped

### Getting Nutrition Data

The scraper has been updated to fetch nutrition data from recipe detail pages. To populate nutrition data:

1. **Re-scrape menus** (this will fetch nutrition for each item):

   ```bash
   python3 scripts/scrape_and_store.py 90
   ```

2. **The scraper will now:**

   - Fetch recipe/ingredient details for each menu item
   - Extract calories, protein, fat, carbs, fiber, serving size
   - Extract ingredients list
   - Store everything in the database

3. **After re-scraping**, menu items will have:
   - ✅ Calories
   - ✅ Serving size (in ounces when available)
   - ✅ Protein, fat, carbs, fiber
   - ✅ Ingredients list

## 🔧 Known Issues

1. **Timeout errors**: Large images may timeout (60s limit)
2. **Missing nutrition**: Most menu items don't have calories
3. **No user tracking**: All scans attributed to "temp_user"
4. **No error recovery**: Failed scrapes need manual retry

## 📝 Notes

- Cal AI integration exists but is not used (ChatGPT Vision is primary)
- Web scraping fallback may break if UCLA website changes
- S3 buckets are in `us-east-2` region
- API uses CORS (currently allows all origins - change for production)
