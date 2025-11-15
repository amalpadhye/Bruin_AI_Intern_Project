# Backend Integration Notes

This document tracks how the mobile app integrates with the existing backend and what's pending.

## ✅ Currently Working (Using Existing Backend)

### 1. Scan Endpoint
- **Backend**: `POST /scan` (app/api/scan.py)
- **Mobile**: `app/(tabs)/scan.tsx`
- **Implementation**: Matches `test_ui.html` - sends FormData with 'image' field
- **Status**: ✅ Fully working
- **Notes**: Backend handles S3 upload internally (scan.py line 44), returns scan results

### 2. Menu Endpoint
- **Backend**: `GET /menus` (app/api/menus.py)
- **Mobile**: `src/lib/api.ts` - `getMenus()`
- **Status**: ✅ Fully working
- **Notes**: Returns menu items from database, supports date/hall filtering

### 3. Presigned URLs
- **Backend**: `GET /uploads/presign` (app/api/uploads.py)
- **Mobile**: `src/lib/api.ts` - `getPresignedUrl()`
- **Status**: ✅ Fully working
- **Notes**: Used for post image uploads

## ❌ Pending Backend Implementation (Per STATUS.md)

### 1. Authentication (STATUS.md line 115-120)
- **Backend Status**: ❌ No Auth0 integration, no JWT validation, uses "temp_user"
- **Mobile Status**: ✅ Auth0 login implemented, ready for backend
- **What's Needed**:
  - Backend: Add Auth0 JWT validation middleware
  - Backend: Extract user_id from tokens (replace "temp_user" in scan.py line 42)
  - Backend: Add GET /me endpoint for user profile
  - Mobile: Already implemented, will work automatically when backend adds auth

### 2. User Profiles (STATUS.md line 122-128)
- **Backend Status**: ❌ No user profiles
- **Mobile Status**: ✅ Onboarding flow ready, profile store ready
- **What's Needed**:
  - Backend: Create users/profiles tables
  - Backend: Add GET /me endpoint
  - Backend: Add PUT /me endpoint
  - Mobile: Already implemented, will work when endpoints are added

### 3. Meal Logging (STATUS.md line 169-173)
- **Backend Status**: ❌ No meal logs, no endpoints
- **Mobile Status**: ✅ Meal log UI ready, offline cache ready
- **What's Needed**:
  - Backend: Create meal_logs table (per data model in requirements)
  - Backend: Add POST /me/meals endpoint
  - Backend: Add GET /me/meals endpoint
  - Mobile: Already implemented, cached meals will sync when endpoints added

### 4. Social Features (STATUS.md line 185-189)
- **Backend Status**: ❌ No posts/votes/comments
- **Mobile Status**: ✅ Feed UI ready, upvote functionality ready
- **What's Needed**:
  - Backend: Create posts/votes/comments tables (per data model)
  - Backend: Add POST /posts endpoint
  - Backend: Add GET /posts endpoint
  - Backend: Add POST /posts/:id/vote endpoint
  - Backend: Add POST /posts/:id/comments endpoint
  - Mobile: Already implemented, cached posts/votes will sync when endpoints added

### 5. Recommendations (STATUS.md line 191-193)
- **Backend Status**: ❌ No recommendations
- **Mobile Status**: ✅ Ready to consume
- **What's Needed**:
  - Backend: Implement recommendation logic (V0 rules-based)
  - Backend: Add GET /me/recommendations endpoint
  - Mobile: Already implemented, will work when endpoint is added

## Mobile App Architecture

The mobile app is designed to work with existing endpoints now and gracefully handle missing endpoints:

1. **Existing Endpoints**: Fully functional (scan, menus, presign)
2. **Pending Endpoints**: 
   - UI is ready
   - Offline cache stores data locally
   - Sync service will push cached data when endpoints are added
   - Error handling gracefully degrades when endpoints don't exist

## Testing Strategy

### Current State (Backend as-is)
- ✅ Test scan flow with existing POST /scan
- ✅ Test menu browsing with existing GET /menus
- ⚠️ Auth/login works but backend doesn't validate tokens yet
- ⚠️ Meal logging UI works but data is only cached locally
- ⚠️ Feed UI works but posts are only cached locally

### After Backend Updates
- ✅ All features will work automatically
- ✅ Cached data will sync to backend
- ✅ Real user tracking instead of "temp_user"

## Migration Path

When backend endpoints are added:

1. **No mobile changes needed** - all code is ready
2. **Cached data will sync** - offline cache will push to new endpoints
3. **Auth will work** - mobile already sends tokens, backend just needs to validate
4. **User tracking** - will automatically switch from "temp_user" to real user_id

