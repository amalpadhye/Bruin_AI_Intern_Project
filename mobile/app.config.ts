// App configuration - matches backend API structure
// See STATUS.md for existing endpoints and what's pending

export const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000' // Local development - matches backend default
  : 'https://api.forku.app'; // Production (update when deployed)

// Auth0 configuration - backend auth pending per STATUS.md line 115-120
export const AUTH0_DOMAIN = process.env.EXPO_PUBLIC_AUTH0_DOMAIN || 'your-domain.auth0.com';
export const AUTH0_CLIENT_ID = process.env.EXPO_PUBLIC_AUTH0_CLIENT_ID || 'your-client-id';
export const AUTH0_AUDIENCE = process.env.EXPO_PUBLIC_AUTH0_AUDIENCE || 'https://api.forku.app';

