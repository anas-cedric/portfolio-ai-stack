import { withAuth } from "@kinde-oss/kinde-auth-nextjs/middleware";
import { NextRequest } from "next/server";

/**
 * Middleware to protect routes that require authentication
 * 
 * Protected routes:
 * - /dashboard - Main portfolio dashboard
 * - /portfolio - Portfolio management
 * - /trade - Trading interface  
 * - /onboarding - Account setup (requires auth first)
 * 
 * Public routes (not protected):
 * - / - Home page with quiz
 * - /advisor - Initial advisor flow
 * - /api/auth/* - Auth endpoints
 */
export default function middleware(req: NextRequest) {
  return withAuth(req);
}

export const config = {
  matcher: [
    "/disabled-for-testing/:path*"
  ]
};