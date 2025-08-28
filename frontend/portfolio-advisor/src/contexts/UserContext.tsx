'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";

interface UserProfile {
  age?: number;
  firstName?: string;
  lastName?: string;
  birthday?: string;
  riskProfile?: string;
  portfolioGenerated?: boolean;
  onboardingCompleted?: boolean;
}

interface UserContextType {
  profile: UserProfile | null;
  isLoading: boolean;
  updateProfile: (updates: Partial<UserProfile>) => void;
  hasCompletedOnboarding: boolean;
  hasGeneratedPortfolio: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const { user, isLoading: isAuthLoading } = useKindeBrowserClient();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthLoading) {
      if (user) {
        // Initialize profile from Kinde user data
        const initialProfile: UserProfile = {
          firstName: user.given_name || undefined,
          lastName: user.family_name || undefined,
          // Age, birthday, etc. will be set during onboarding flow
        };
        setProfile(initialProfile);
      }
      setIsLoading(false);
    }
  }, [user, isAuthLoading]);

  const updateProfile = (updates: Partial<UserProfile>) => {
    setProfile(prev => prev ? { ...prev, ...updates } : updates);
  };

  const hasCompletedOnboarding = Boolean(profile?.onboardingCompleted);
  const hasGeneratedPortfolio = Boolean(profile?.portfolioGenerated);

  return (
    <UserContext.Provider value={{
      profile,
      isLoading,
      updateProfile,
      hasCompletedOnboarding,
      hasGeneratedPortfolio
    }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUserProfile() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUserProfile must be used within a UserProvider');
  }
  return context;
}