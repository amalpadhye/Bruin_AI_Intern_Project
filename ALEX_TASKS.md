# Alex's Tasks - Implementation Guide

This document outlines the implementation for Cal AI integration and UCLA menu scraping.

## Cal AI Integration

### Overview
The Cal AI client (`app/services/cal_ai_client.py`) handles food image analysis.

### Key Components

1. **CalAIClient Class**
   - `scan_image()`: Calls Cal AI `/scan-image` endpoint
   - `normalize_response()`: Converts Cal AI response to standard format
   - `calculate_discrepancy()`: Compares Cal AI predictions vs menu data

2. **Configuration**
   - `CAL_AI_API_KEY`: Your Cal AI API key (Bearer token)
   - `CAL_AI_BASE_URL`: API base URL (default: https://api.calai.app)
   - Thresholds in `config.py`:
     - `calorie_discrepancy_threshold`: 0.15 (15% difference triggers warning)
     - `protein_discrepancy_threshold`: 0.20 (20% difference)
     - `confidence_threshold`: 0.7 (minimum confidence)

3. **API Endpoint**
   - `POST /scan`: Accepts image upload, calls Cal AI, returns normalized prediction

### Usage Example

```python
from app.services.cal_ai_client import CalAIClient

client = CalAIClient()

# Scan image
response = await client.scan_image(image_bytes=image_data)
normalized = client.normalize_response(response)

# Compare with menu data
menu_nutrition = {"calories": 300, "protein_g": 20}
discrepancy = client.calculate_discrepancy(normalized, menu_nutrition)
```

### Important Notes

- **API Response Structure**: The actual Cal AI API response format may differ from assumptions. You'll need to:
  1. Make a test API call to see the actual response structure
  2. Update `normalize_response()` method to match the real format
  3. Check Cal AI docs: https://docs.calai.app/api-reference/introduction

- **Authentication**: Uses Bearer token in Authorization header

## UCLA Menu Scraping

### Overview
The scraper (`app/services/ucla_scraper.py`) fetches UCLA dining menu data with API-first approach and web scraping fallback.

### Key Components

1. **UCLAScraper Class**
   - `fetch_menu_via_api()`: Uses UCLA official API (requires approval)
   - `fetch_menu_via_web_scraping()`: Fallback web scraping
   - `scrape_daily_menu()`: Main method (tries API, then web scraping)
   - `fetch_recipe_details()` / `fetch_ingredient_details()`: Get nutrition data

2. **Configuration**
   - `UCLA_API_KEY`: UCLA API key (if available)
   - `UCLA_API_BASE_URL`: https://api.ucla.edu/sis

3. **API Endpoints**
   - `GET /menus?date=YYYY-MM-DD&hall=name`: Get menu data
   - `GET /menus/items/{item_id}`: Get item details

### Scraping Pipeline

1. **Daily Scraping (EventBridge → ECS)**
   - EventBridge triggers ECS Fargate task daily
   - Task runs `app/tasks/scraper_task.py`
   - Scrapes menu data → uploads to S3 → triggers normalization

2. **Manual Trigger**
   - `POST /tasks/scrape-ucla?date=YYYY-MM-DD` (requires X-Secret header)

### Current Status

- **UCLA API**: Requires approval from MyUCLA IWE partners
  - Portal: https://developer.api.ucla.edu/api/61
  - Once approved, update `fetch_menu_via_api()` with actual endpoint structure

- **Web Scraping Fallback**: 
  - Tries old JSON endpoint: `dining.ucla.edu/wp-content/uploads/jamix/menus/{date}.json`
  - May need updates if UCLA changes website structure
  - HTML scraping placeholder exists but needs implementation

### Usage Example

```python
from app.services.ucla_scraper import UCLAScraper

scraper = UCLAScraper()

# Scrape today's menu
menu_data = await scraper.scrape_daily_menu()

# Scrape specific date
menu_data = await scraper.scrape_daily_menu("2025-04-15")
```

## S3 Storage

### Bucket Structure

- **Raw Data**: `s3://{bucket_raw}/raw/`
  - Menus: `raw/menus/YYYY-MM-DD/menu.json`
  - Scans: `raw/scans/{user_id}/{scan_id}.jpg`

- **Derived Data**: `s3://{bucket_derived}/derived/`
  - Cal AI results: `derived/cal_ai/{user_id}/{scan_id}.json`

- **Media**: `s3://{bucket_media}/media/`
  - Posts: `media/posts/{post_id}/{image}.jpg`

## Next Steps

1. **Cal AI Integration**
   - [ ] Get Cal AI API key and test `/scan-image` endpoint
   - [ ] Verify actual API response structure
   - [ ] Update `normalize_response()` if needed
   - [ ] Test discrepancy logic with real data

2. **UCLA Scraper**
   - [ ] Request UCLA API access (if not already done)
   - [ ] Test UCLA API endpoint structure once approved
   - [ ] Update `fetch_menu_via_api()` with real endpoint
   - [ ] Test web scraping fallback
   - [ ] Implement HTML scraping if JSON endpoint stops working

3. **Normalization Pipeline**
   - [ ] Create Postgres models (SQLAlchemy)
   - [ ] Implement database insertion for normalized menu items
   - [ ] Set up Alembic migrations
   - [ ] Create normalization ECS task or Lambda

4. **Testing**
   - [ ] Unit tests for Cal AI client
   - [ ] Unit tests for scraper
   - [ ] Integration tests for full pipeline
   - [ ] Test EventBridge → ECS task flow

5. **Deployment**
   - [ ] Set up ECR repository
   - [ ] Create ECS task definition
   - [ ] Configure EventBridge daily rule
   - [ ] Set up ALB/API Gateway
   - [ ] Configure secrets in AWS Secrets Manager

## Troubleshooting

### Cal AI Issues
- **401 Unauthorized**: Check API key in `.env`
- **Response format mismatch**: Update `normalize_response()` based on actual API response
- **Timeout errors**: Increase timeout in `httpx.AsyncClient`

### Scraper Issues
- **API 403**: UCLA API access not approved yet
- **JSON endpoint 404**: Website structure changed, need to update scraper
- **Empty results**: Check date format (YYYY-MM-DD) and dining hall names

### S3 Issues
- **Access denied**: Check AWS credentials and bucket permissions
- **Presigned URL fails**: Verify bucket name and key format

