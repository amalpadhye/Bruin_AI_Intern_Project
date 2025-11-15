# What Still Needs to Be Done

## ✅ Mobile App - COMPLETE

All of Annika's mobile to-dos are implemented:
- ✅ RN app scaffold
- ✅ Auth0 login (mobile-side)
- ✅ Onboarding flow
- ✅ Camera → scan flow (uses existing POST /scan)
- ✅ Meal log UI
- ✅ Feed + upvotes
- ✅ Push notifications
- ✅ Offline cache + sync

## ❌ Backend - Still Needs Implementation

Per STATUS.md, the following backend work is needed:

### High Priority (STATUS.md line 152-173)

#### 1. Authentication (STATUS.md line 162-167)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Integrate Auth0 in backend
- [ ] Add JWT validation middleware
- [ ] Extract user_id from tokens (replace "temp_user" in scan.py line 42)
- [ ] Protect admin endpoints
- [ ] Add GET /me endpoint for user profile

**Impact:** Mobile auth is ready, just needs backend validation

#### 2. User & Meal Logging (STATUS.md line 169-173)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Create user/profile database models
- [ ] Create meal_logs table (per data model requirements)
- [ ] Add POST /me/meals endpoint
- [ ] Add GET /me/meals endpoint
- [ ] Store scan results as meal logs

**Impact:** Mobile meal log UI is ready, just needs backend endpoints

### Medium Priority (STATUS.md line 175-193)

#### 3. Social Features (STATUS.md line 185-189)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Create posts/votes/comments database models (per data model requirements)
- [ ] Add POST /posts endpoint
- [ ] Add GET /posts endpoint (with sort=top/new)
- [ ] Add POST /posts/:id/vote endpoint
- [ ] Add POST /posts/:id/comments endpoint
- [ ] Implement ranking algorithm

**Impact:** Mobile feed UI is ready, just needs backend endpoints

#### 4. Recommendations (STATUS.md line 191-193)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Implement V0 rules-based recommendations
- [ ] Add GET /me/recommendations endpoint

**Impact:** Mobile is ready to consume, just needs endpoint

### Low Priority (STATUS.md line 195-212)

#### 5. Error Recovery (STATUS.md line 197-201)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Add retry logic with exponential backoff
- [ ] Set up SQS for failed jobs
- [ ] Add dead letter queue

#### 6. Performance (STATUS.md line 203-207)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Add Redis caching for menu queries
- [ ] Optimize database queries
- [ ] Add pagination

#### 7. Testing (STATUS.md line 209-212)
**Status:** ❌ Not implemented
**What's Needed:**
- [ ] Unit tests for services
- [ ] Integration tests for endpoints
- [ ] E2E tests for full flow

## Systematic Implementation Plan

### Phase 1: Authentication & User Profiles (Week 1)
1. Add Auth0 JWT validation middleware
2. Create users/profiles tables
3. Add GET /me endpoint
4. Add PUT /me endpoint
5. Update scan endpoint to use real user_id

**Result:** Mobile auth and onboarding will work fully

### Phase 2: Meal Logging (Week 1-2)
1. Create meal_logs table
2. Add POST /me/meals endpoint
3. Add GET /me/meals endpoint
4. Update scan endpoint to create meal logs

**Result:** Mobile meal log will sync and display properly

### Phase 3: Social Features (Week 2-3)
1. Create posts/votes/comments tables
2. Add POST /posts endpoint
3. Add GET /posts endpoint
4. Add POST /posts/:id/vote endpoint
5. Add POST /posts/:id/comments endpoint

**Result:** Mobile feed will work fully

### Phase 4: Recommendations (Week 3)
1. Implement recommendation logic
2. Add GET /me/recommendations endpoint

**Result:** Mobile can show recommendations

## Testing Strategy

### Current State
- ✅ Test scan flow (works with existing POST /scan)
- ✅ Test menu browsing (works with existing GET /menus)
- ⚠️ Test auth (mobile ready, backend pending)
- ⚠️ Test meal logging (mobile ready, backend pending)
- ⚠️ Test feed (mobile ready, backend pending)

### After Each Phase
- Test that mobile app automatically works with new endpoints
- Verify cached data syncs properly
- Check offline functionality still works

## Notes

- **No mobile changes needed** - all code is ready
- **Backend can implement incrementally** - mobile will work as endpoints are added
- **Cached data will sync automatically** - offline cache will push when endpoints are available
- **Migration path is clear** - see STATUS.md for detailed requirements

