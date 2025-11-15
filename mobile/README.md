# ForkU Mobile App

React Native mobile app for ForkU - Food tracking and social app for UCLA students.

## Integration with Existing Backend

This mobile app integrates with the existing FastAPI backend. See `STATUS.md` for backend status.

### ✅ Existing Backend Endpoints (Working Now)

- **POST /scan** - Food image analysis (FormData with 'image' field)
  - Matches `app/api/scan.py` implementation
  - Backend handles S3 upload internally
  - Returns scan results with matched/unmatched foods
  - See `test_ui.html` for reference implementation

- **GET /menus** - Get menu data for date/hall
  - Matches `app/api/menus.py` implementation
  - Returns menu items from database

- **GET /uploads/presign** - Generate presigned S3 URLs
  - Matches `app/api/uploads.py` implementation
  - Used for post image uploads

### ❌ Pending Backend Endpoints (Per STATUS.md)

The following features are implemented in the mobile app but require backend endpoints:

- **User Profiles** (STATUS.md line 122-128)
  - Mobile: Auth0 login ready
  - Backend: Needs Auth0 integration, JWT validation, GET/PUT /me endpoints

- **Meal Logging** (STATUS.md line 169-173)
  - Mobile: Meal log UI ready, offline cache ready
  - Backend: Needs POST /me/meals, GET /me/meals endpoints

- **Social Features** (STATUS.md line 185-189)
  - Mobile: Feed UI, upvote functionality ready
  - Backend: Needs POST /posts, GET /posts, POST /posts/:id/vote endpoints

- **Recommendations** (STATUS.md line 191-193)
  - Mobile: Ready to consume
  - Backend: Needs GET /me/recommendations endpoint

## Features

✅ **Auth0 Login** - Mobile-side implementation (backend auth pending)  
✅ **Onboarding Flow** - Collect user profile (height/weight/goals/restrictions/dorm/plan)  
✅ **Camera → Scan Flow** - Uses existing POST /scan endpoint  
✅ **Meal Log UI** - Structure ready (backend endpoints pending)  
✅ **Social Feed** - Structure ready (backend endpoints pending)  
✅ **Push Notifications** - Meal reminders and social updates  
✅ **Offline Cache** - SQLite-based offline storage (will sync when backend endpoints added)  

## Tech Stack

- **Framework**: React Native with Expo (~51.0.0)
- **Navigation**: Expo Router (file-based routing)
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **Forms**: React Hook Form + Zod validation
- **Offline Storage**: SQLite (react-native-sqlite-storage)
- **Camera**: Expo Camera
- **Notifications**: Expo Notifications
- **Auth**: Auth0 via expo-auth-session

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Expo CLI (`npm install -g expo-cli`)
- Backend API running (see main README.md)
- iOS Simulator (for iOS) or Android Emulator (for Android)

### Installation

```bash
cd mobile
npm install
```

### Environment Variables

Create a `.env` file in the `mobile` directory:

```env
EXPO_PUBLIC_AUTH0_DOMAIN=your-domain.auth0.com
EXPO_PUBLIC_AUTH0_CLIENT_ID=your-client-id
EXPO_PUBLIC_AUTH0_AUDIENCE=https://api.forku.app
```

### Running the App

```bash
# Start Expo dev server
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## Project Structure

```
mobile/
├── app/                    # Expo Router pages
│   ├── (auth)/            # Auth screens
│   ├── (tabs)/            # Main app tabs
│   │   ├── scan.tsx       # Camera/scan (uses POST /scan)
│   │   ├── meals.tsx      # Meal log (pending backend)
│   │   └── feed.tsx       # Social feed (pending backend)
│   ├── onboarding/        # Onboarding flow
│   └── _layout.tsx        # Root layout
├── src/
│   ├── lib/
│   │   ├── api.ts         # API client (notes existing vs pending endpoints)
│   │   ├── auth0.ts       # Auth0 integration
│   │   ├── offlineCache.ts # SQLite cache
│   │   ├── sync.ts        # Offline sync service
│   │   └── notifications.ts # Push notifications
│   └── store/
│       ├── authStore.ts   # Auth state
│       └── profileStore.ts # Profile state
├── app.config.ts          # App configuration
└── package.json
```

## Key Implementation Details

### Scan Flow (Working Now)

The scan screen uses the existing `POST /scan` endpoint:

```typescript
// Matches test_ui.html implementation
const formData = new FormData();
formData.append('image', { uri: imageUri, type: 'image/jpeg', name: 'image.jpg' });
const result = await apiClient.scanImage(imageUri);
```

The backend (`app/api/scan.py`) handles:
- S3 upload internally (line 44)
- ChatGPT analysis
- Menu matching
- Returns scan results

### Offline Cache (Ready for Backend)

The offline cache system is fully implemented and will automatically sync when backend endpoints are added:

- Meals cached locally
- Posts cached locally
- Votes cached locally
- Automatic sync when online
- Graceful degradation when offline

### Auth Flow (Mobile Ready, Backend Pending)

- Mobile: Auth0 login fully implemented
- Backend: Currently uses "temp_user" (STATUS.md line 119)
- When backend adds auth, mobile will automatically use it

## Testing with Existing Backend

1. **Start backend** (from project root):
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Start mobile app**:
   ```bash
   cd mobile
   npm start
   ```

3. **Test scan flow**:
   - Open scan tab
   - Take/select photo
   - Should see scan results (matches test_ui.html behavior)

4. **Test menu browsing**:
   - Menu data loads from existing GET /menus endpoint

## Notes

- **Backend Auth**: Currently backend uses "temp_user" for all scans. Mobile auth is ready for when backend adds Auth0 integration.
- **Meal Logging**: UI is ready, but POST /me/meals endpoint doesn't exist yet. Meals are cached offline and will sync when endpoint is added.
- **Social Feed**: UI is ready, but POST /posts endpoint doesn't exist yet. Posts are cached offline.
- **Image URLs**: Post images use presigned URLs from existing GET /uploads/presign endpoint.

## Roadblocks / Next Steps

1. **Backend Auth Integration** (STATUS.md line 162-167)
   - Add Auth0 JWT validation middleware
   - Extract user_id from tokens
   - Update scan endpoint to use real user_id

2. **Meal Logging Endpoints** (STATUS.md line 169-173)
   - Create meal_logs table
   - Add POST /me/meals endpoint
   - Add GET /me/meals endpoint

3. **Social Features** (STATUS.md line 185-189)
   - Create posts/votes/comments models
   - Add endpoints for social features

4. **Recommendations** (STATUS.md line 191-193)
   - Implement recommendation logic
   - Add GET /me/recommendations endpoint

