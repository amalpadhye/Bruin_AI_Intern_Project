# Next Steps - Action Checklist for Alex

## Immediate Actions (Do These First)

### 1. Set Up Environment ⚙️

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example if it exists, or create manually)
# You need these variables:
```

**Create `.env` file with:**
```env
# Cal AI (REQUIRED - get from https://docs.calai.app)
CAL_AI_API_KEY=your_actual_api_key_here
CAL_AI_BASE_URL=https://api.calai.app

# AWS (for S3 - you can use local testing first)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_RAW=forku-raw
S3_BUCKET_DERIVED=forku-derived
S3_BUCKET_MEDIA=forku-media

# Database (for later - can use local Postgres)
DATABASE_URL=postgresql://user:pass@localhost:5432/forku_db

# Redis (optional for now)
REDIS_URL=redis://localhost:6379/0

# API Secret (generate a random string)
API_SECRET_KEY=your-random-secret-here

# UCLA API (optional - if you get access)
UCLA_API_KEY=your_ucla_key_if_available
UCLA_API_BASE_URL=https://api.ucla.edu/sis
```

### 2. Test Cal AI Integration 🧪

**Get your Cal AI API key:**
1. Go to https://docs.calai.app/api-reference/introduction
2. Sign up/get API credentials
3. Add to `.env` file

**Test it:**
```bash
# Test with a food image
python test_cal_ai.py path/to/food_image.jpg
```

**What to check:**
- Does the API call work?
- What does the actual response structure look like?
- You may need to update `app/services/cal_ai_client.py` → `normalize_response()` method based on real API response

### 3. Test UCLA Scraper 🍽️

**Test the scraper:**
```bash
# Test scraping today's menu
python test_scraper.py

# Test specific date
python test_scraper.py 2025-04-15
```

**What to check:**
- Does web scraping fallback work?
- Are you getting menu data?
- If UCLA API access is approved, test that too

### 4. Run the API Locally 🚀

```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Test endpoints:
# - http://localhost:8000/docs (Swagger UI)
# - http://localhost:8000/health
# - POST http://localhost:8000/scan (upload image)
# - GET http://localhost:8000/menus?date=2025-04-15
```

## Priority Tasks (This Week)

### ✅ Cal AI Integration
- [ ] Get Cal AI API key
- [ ] Test `/scan-image` endpoint with real image
- [ ] Inspect actual API response structure
- [ ] Update `normalize_response()` if response format differs
- [ ] Test discrepancy calculation with real data

### ✅ UCLA Scraper
- [ ] Request UCLA API access (if not done): https://developer.api.ucla.edu/api/61
- [ ] Test web scraping fallback with current dates
- [ ] Verify scraper can fetch menu data
- [ ] If UCLA API approved, update `fetch_menu_via_api()` with real endpoint structure

### ✅ Basic Testing
- [ ] Test Cal AI with multiple food images
- [ ] Test scraper with different dates
- [ ] Verify S3 uploads work (if AWS configured)
- [ ] Test API endpoints via Swagger UI

## Medium Priority (Next Week)

### Database Setup
- [ ] Set up local Postgres (or use existing)
- [ ] Create SQLAlchemy models based on schema in project spec
- [ ] Set up Alembic for migrations
- [ ] Implement database insertion for normalized menu items

### Normalization Pipeline
- [ ] Test `MenuNormalizer` with scraped data
- [ ] Create database insertion logic
- [ ] Test full flow: scrape → normalize → insert to DB

## Lower Priority (Before Deployment)

### AWS Infrastructure
- [ ] Set up S3 buckets
- [ ] Configure IAM roles/permissions
- [ ] Set up ECR repository
- [ ] Create ECS task definition
- [ ] Configure EventBridge for daily scraping
- [ ] Set up ALB/API Gateway

### Testing & Quality
- [ ] Write unit tests
- [ ] Integration tests
- [ ] Error handling improvements
- [ ] Logging improvements

## Quick Reference Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Test Cal AI
python test_cal_ai.py image.jpg

# Test scraper
python test_scraper.py

# Run API
uvicorn app.main:app --reload

# Run scraper task manually
python -m app.tasks.scraper_task 2025-04-15
```

## Common Issues & Solutions

**"Module not found" errors:**
- Make sure you're in the project root directory
- Run `pip install -r requirements.txt`

**Cal AI 401 Unauthorized:**
- Check `.env` file has correct `CAL_AI_API_KEY`
- Verify API key is valid

**Scraper returns empty data:**
- Check date format (YYYY-MM-DD)
- Try different dates
- Check if UCLA website structure changed

**S3 errors:**
- Verify AWS credentials in `.env`
- Check bucket names exist
- Verify IAM permissions

## Questions to Answer

1. **Cal AI API**: What does the actual response look like? (Run test and inspect)
2. **UCLA API**: Do you have access? What's the endpoint structure?
3. **AWS**: Do you have AWS account set up? S3 buckets created?
4. **Database**: Local Postgres or cloud? Need help setting up?

## Need Help?

- Check `ALEX_TASKS.md` for detailed implementation guide
- Check `README.md` for project overview
- Review code comments in service files
- Test scripts will help you debug issues

