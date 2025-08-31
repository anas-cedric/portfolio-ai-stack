import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { getOrCreateUserOnboardingState, updateUserOnboardingState, type OnboardingState } from "@/lib/supabase";

// GET /api/onboarding - Get user's current onboarding state
export async function GET(request: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: "User not found" }, { status: 401 });
    }

    // Get or create onboarding state
    const onboardingState = await getOrCreateUserOnboardingState(user.id);

    return NextResponse.json({
      success: true,
      onboarding: {
        state: onboardingState.onboarding_state,
        quiz_data: onboardingState.quiz_data,
        portfolio_preferences: onboardingState.portfolio_preferences,
        created_at: onboardingState.created_at,
        updated_at: onboardingState.updated_at
      }
    });

  } catch (error: any) {
    console.error('Failed to get onboarding state:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to get onboarding state' 
    }, { status: 500 });
  }
}

// PUT /api/onboarding - Update user's onboarding state
export async function PUT(request: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: "User not found" }, { status: 401 });
    }

    const body = await request.json();
    const { state, quiz_data, portfolio_preferences } = body;

    // Validate state
    const validStates: OnboardingState[] = ['new', 'quiz_completed', 'portfolio_approved', 'active'];
    if (!validStates.includes(state)) {
      return NextResponse.json({ 
        error: `Invalid state. Must be one of: ${validStates.join(', ')}` 
      }, { status: 400 });
    }

    // Update onboarding state
    const updatedState = await updateUserOnboardingState(
      user.id, 
      state as OnboardingState,
      {
        quiz_data,
        portfolio_preferences
      }
    );

    return NextResponse.json({
      success: true,
      onboarding: {
        state: updatedState.onboarding_state,
        quiz_data: updatedState.quiz_data,
        portfolio_preferences: updatedState.portfolio_preferences,
        updated_at: updatedState.updated_at
      }
    });

  } catch (error: any) {
    console.error('Failed to update onboarding state:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to update onboarding state' 
    }, { status: 500 });
  }
}