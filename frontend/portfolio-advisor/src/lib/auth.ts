import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { redirect } from "next/navigation";

/**
 * Auth utility functions for server components
 */

export async function requireAuth() {
  const { isAuthenticated } = getKindeServerSession();
  
  if (!(await isAuthenticated())) {
    redirect("/api/auth/login");
  }
}

export async function getAuthUser() {
  const { getUser, isAuthenticated } = getKindeServerSession();
  
  if (!(await isAuthenticated())) {
    return null;
  }
  
  return await getUser();
}

export async function getAuthSession() {
  const { 
    getUser, 
    isAuthenticated, 
    getPermissions, 
    getOrganization,
    getAccessToken 
  } = getKindeServerSession();
  
  const isAuth = await isAuthenticated();
  
  if (!isAuth) {
    return null;
  }
  
  const [user, permissions, organization, accessToken] = await Promise.all([
    getUser(),
    getPermissions(),
    getOrganization(),
    getAccessToken()
  ]);
  
  return {
    user,
    permissions,
    organization,
    accessToken
  };
}

/**
 * Check if user has a specific permission
 */
export async function hasPermission(permission: string): Promise<boolean> {
  const { getPermissions, isAuthenticated } = getKindeServerSession();
  
  if (!(await isAuthenticated())) {
    return false;
  }
  
  const permissions = await getPermissions();
  return permissions?.permissions?.includes(permission) ?? false;
}

/**
 * Get user's custom properties (risk profile, etc)
 * Note: Custom properties need to be retrieved via Kinde Management API
 */
export async function getUserProperties() {
  const { getUser, isAuthenticated } = getKindeServerSession();
  
  if (!(await isAuthenticated())) {
    return null;
  }
  
  const user = await getUser();
  // For now, return empty object. Custom properties would require Management API call
  return {};
}