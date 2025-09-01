'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import { Loader2 } from 'lucide-react';

type OnboardingState = 'new' | 'quiz_completed' | 'portfolio_approved' | 'active';

type OnboardingData = {
  state: OnboardingState;
  quiz_data?: any;
  portfolio_preferences?: any;
  created_at: string;
  updated_at: string;
};

interface OnboardingRouterProps {
  children: React.ReactNode;
  expectedState?: OnboardingState;
  fallbackRoute?: string;
}

export default function OnboardingRouter({ 
  children, 
  expectedState, 
  fallbackRoute = '/portfolio-quiz' 
}: OnboardingRouterProps) {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useKindeBrowserClient();
  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Allow certain states to pass when a later state is acceptable
  const isStateAllowed = (current: OnboardingState, expected?: OnboardingState) => {
    if (!expected) return true;
    // If expecting 'portfolio_approved', also allow 'active' (post-approval)
    if (expected === 'portfolio_approved') {
      return current === 'portfolio_approved' || current === 'active';
    }
    return current === expected;
  };

  useEffect(() => {
    if (!isAuthLoading && user?.id) {
      fetchOnboardingState();
    } else if (!isAuthLoading && !user) {
      // Not authenticated, redirect to login
      router.push('/api/auth/login');
    }
  }, [user, isAuthLoading, router]);

  const fetchOnboardingState = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/onboarding');
      
      if (!response.ok) {
        throw new Error('Failed to fetch onboarding state');
      }

      const data = await response.json();
      setOnboardingData(data.onboarding);

      // Route based on current state vs expected state
      if (expectedState && !isStateAllowed(data.onboarding.state, expectedState)) {
        routeToCorrectPage(data.onboarding.state);
      }

    } catch (error: any) {
      console.error('Failed to fetch onboarding state:', error);
      setError(error.message);
      // On error, default to fallback route
      router.push(fallbackRoute);
    } finally {
      setIsLoading(false);
    }
  };

  const routeToCorrectPage = (currentState: OnboardingState) => {
    console.log(`Routing user with state '${currentState}'`);
    
    switch (currentState) {
      case 'new':
        router.push('/portfolio-quiz');
        break;
      case 'quiz_completed':
        // User completed quiz but hasn't approved portfolio yet
        // Stay on current page if it's the quiz, otherwise go to quiz
        if (!window.location.pathname.includes('/portfolio-quiz')) {
          router.push('/portfolio-quiz');
        }
        break;
      case 'portfolio_approved':
        // Don't auto-redirect for portfolio_approved - let parent component handle it
        // This prevents race conditions with approval flow navigation
        break;
      case 'active':
        router.push('/dashboard');
        break;
      default:
        router.push(fallbackRoute);
    }
  };

  // Show loading while checking auth or onboarding state
  if (isAuthLoading || isLoading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-[#E6EFF3]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-[#E6EFF3]">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated
  if (!user) {
    return null;
  }

  // If we have expected state and it matches, or no expected state, render children
  if (!expectedState || (onboardingData?.state && isStateAllowed(onboardingData.state, expectedState))) {
    return <>{children}</>;
  }

  // Otherwise, show loading while redirecting
  return (
    <div className="w-full h-screen flex items-center justify-center bg-[#E6EFF3]">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-gray-700">Redirecting...</p>
      </div>
    </div>
  );
}