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
      // Hydrate from localStorage if present
      let saved: UserProfile | null = null;
      try {
        const raw = typeof window !== 'undefined' ? window.localStorage.getItem('cedric_user_profile') : null;
        if (raw) {
          saved = JSON.parse(raw);
        }
      } catch {}

      if (user) {
        // Initialize/merge profile with Kinde user data
        const initialProfile: UserProfile = {
          ...saved,
          firstName: user.given_name || saved?.firstName || undefined,
          lastName: user.family_name || saved?.lastName || undefined,
          // Age, birthday, riskProfile, etc. may be in saved
        };
        setProfile(initialProfile);
      } else if (saved) {
        setProfile(saved);
      }
      setIsLoading(false);
    }
  }, [user, isAuthLoading]);

  const updateProfile = (updates: Partial<UserProfile>) => {
    setProfile(prev => {
      const next = prev ? { ...prev, ...updates } : (updates as UserProfile);
      try {
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('cedric_user_profile', JSON.stringify(next));
        }
      } catch {}
      return next;
    });
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