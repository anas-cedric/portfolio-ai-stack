import { handleAuth } from "@kinde-oss/kinde-auth-nextjs/server";

export const GET = handleAuth();

/**
 * Kinde Auth Route Handler
 * 
 * This creates all the necessary auth endpoints:
 * - /api/auth/login - Redirects to Kinde login
 * - /api/auth/register - Redirects to Kinde registration  
 * - /api/auth/logout - Logs out the user
 * - /api/auth/callback - Handles the OAuth callback from Kinde
 * - /api/auth/kinde_callback - Alternative callback endpoint
 * 
 * These routes are automatically handled by Kinde's handleAuth() function
 */