import { NextRequest, NextResponse } from 'next/server';
import { getKindeServerSession } from '@kinde-oss/kinde-auth-nextjs/server';
import { getOrCreateUserOnboardingState, updateUserOnboardingState } from '@/lib/supabase';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: 'User not found' }, { status: 401 });
    }

    const body = await request.json().catch(() => ({}));
    const quiz_data = body?.quiz_data;
    const portfolio_preferences = body?.portfolio_preferences;

    // Ensure onboarding row exists
    await getOrCreateUserOnboardingState(user.id);

    // Update state to quiz_completed and optionally persist quiz data
    const onboarding = await updateUserOnboardingState(user.id, 'quiz_completed', {
      quiz_data,
      portfolio_preferences,
    });

    return NextResponse.json({ success: true, onboarding });
  } catch (error: any) {
    console.error('Failed to mark quiz as completed:', error);
    return NextResponse.json({ error: error?.message || 'Internal error' }, { status: 500 });
  }
}
