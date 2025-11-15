# Testing Guide

## What's Working Now (Can Test Immediately)

### 1. Scan Flow (✅ Fully Working)

**Prerequisites:**
- Backend API running (`uvicorn app.main:app --reload`)
- Backend has menu data (run `python3 scripts/scrape_and_store.py 90`)

**Steps:**
1. Start mobile app: `cd mobile && npm start`
2. Run on device/simulator: `npm run ios` or `npm run android`
3. Navigate to Scan tab
4. Take a photo or select from gallery
5. Should see scan results with matched/unmatched foods

**Expected Result:**
- Image uploads to backend
- Backend processes with ChatGPT
- Returns scan results matching `test_ui.html` behavior
- Shows matched foods with menu items
- Shows unmatched foods with ChatGPT suggestions

### 2. Menu Browsing (✅ Fully Working)

**Steps:**
1. Navigate to any screen that uses menu data
2. Menu data loads from existing `GET /menus` endpoint

**Expected Result:**
- Menu items load from database
- Can filter by date/hall (if implemented in UI)

## What's Partially Working (UI Ready, Backend Pending)

### 3. Auth0 Login (⚠️ Mobile Ready, Backend Pending)

**Current State:**
- Mobile: Auth0 login flow implemented
- Backend: Uses "temp_user" (STATUS.md line 119)

**Testing:**
1. Try to login - will attempt Auth0 flow
2. May fail if Auth0 not configured
3. Will work when backend adds Auth0 JWT validation

**Expected:**
- Login screen appears
- Auth0 flow attempts (may error if not configured)
- Falls back to temp user if backend doesn't validate tokens

### 4. Onboarding Flow (⚠️ UI Ready, Backend Pending)

**Current State:**
- Mobile: Complete 5-step onboarding form
- Backend: No profile endpoints yet (STATUS.md line 122-128)

**Testing:**
1. Complete onboarding form
2. Data saved locally
3. Will sync when backend adds `PUT /me` endpoint

**Expected:**
- Can fill out all 5 steps
- Data stored in profile store
- Shows completion message
- Navigates to home screen

### 5. Meal Log (⚠️ UI Ready, Backend Pending)

**Current State:**
- Mobile: Meal list UI ready, offline cache ready
- Backend: No meal endpoints (STATUS.md line 169-173)

**Testing:**
1. Scan a food (creates cached meal)
2. Navigate to Meals tab
3. Should see cached meals
4. Shows "Offline mode" banner

**Expected:**
- Meals from scans appear in list
- Shows "Offline mode" indicator
- Data cached in SQLite
- Will sync when backend adds `POST /me/meals`

### 6. Social Feed (⚠️ UI Ready, Backend Pending)

**Current State:**
- Mobile: Feed UI ready, upvote functionality ready
- Backend: No post endpoints (STATUS.md line 185-189)

**Testing:**
1. Navigate to Feed tab
2. See empty state (no posts yet)
3. Can sort by "new" or "top"
4. Upvote buttons present but won't work until backend adds endpoints

**Expected:**
- Feed screen loads
- Empty state shown
- UI ready for when backend adds `GET /posts`

## Setup Instructions

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure Environment

Create `mobile/.env`:
```env
EXPO_PUBLIC_AUTH0_DOMAIN=your-domain.auth0.com
EXPO_PUBLIC_AUTH0_CLIENT_ID=your-client-id
EXPO_PUBLIC_AUTH0_AUDIENCE=https://api.forku.app
```

**Note:** Auth0 config is optional for now since backend doesn't validate tokens yet.

### 3. Start Backend

```bash
# From project root
uvicorn app.main:app --reload
```

### 4. Start Mobile App

```bash
cd mobile
npm start
```

Then:
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan QR code for physical device

## Testing Checklist

### ✅ Can Test Now
- [ ] Scan food image (uses existing POST /scan)
- [ ] View scan results
- [ ] Navigate between tabs
- [ ] Onboarding flow UI
- [ ] Meal log UI (shows cached meals)
- [ ] Feed UI (empty state)

### ⚠️ Will Work When Backend Adds Endpoints
- [ ] Auth0 login (backend needs JWT validation)
- [ ] Profile saving (backend needs PUT /me)
- [ ] Meal syncing (backend needs POST /me/meals)
- [ ] Post creation (backend needs POST /posts)
- [ ] Upvoting (backend needs POST /posts/:id/vote)

## Common Issues

### 1. "Network Error" when scanning
- **Solution:** Make sure backend is running on `http://localhost:8000`
- **Check:** `curl http://localhost:8000/health`

### 2. "No menu items found"
- **Solution:** Run scraper: `python3 scripts/scrape_and_store.py 90`
- **Check:** Database has menu items

### 3. Auth0 login fails
- **Expected:** Backend doesn't validate tokens yet (STATUS.md line 115-120)
- **Workaround:** App will use temp user for now

### 4. Meals don't sync
- **Expected:** Backend doesn't have POST /me/meals yet (STATUS.md line 169-173)
- **Workaround:** Meals are cached locally, will sync when endpoint is added

### 5. Posts don't appear
- **Expected:** Backend doesn't have GET /posts yet (STATUS.md line 185-189)
- **Workaround:** Feed shows empty state, ready for when endpoint is added

## Next Steps for Full Testing

1. **Backend Team:** Add Auth0 JWT validation (STATUS.md line 162-167)
2. **Backend Team:** Add user/profile endpoints (STATUS.md line 169-173)
3. **Backend Team:** Add meal logging endpoints (STATUS.md line 169-173)
4. **Backend Team:** Add social endpoints (STATUS.md line 185-189)

Once backend endpoints are added, mobile app will automatically work with them - no mobile changes needed!

