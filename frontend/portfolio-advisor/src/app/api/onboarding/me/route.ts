import { NextRequest, NextResponse } from 'next/server';
import { getKindeServerSession } from '@kinde-oss/kinde-auth-nextjs/server';
import { getUserOnboardingState } from '@/lib/supabase';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(_request: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: 'User not found' }, { status: 401 });
    }

    const onboarding = await getUserOnboardingState(user.id);

    // Prefer dedicated columns if available; fall back to JSON
    const prefs = (onboarding as any)?.portfolio_preferences || {};
    const risk_bucket = (onboarding as any)?.risk_bucket
      ?? (typeof prefs?.risk_bucket === 'string' ? prefs.risk_bucket : null);
    const risk_score = (onboarding as any)?.risk_score
      ?? (typeof prefs?.risk_score === 'number' ? prefs.risk_score : null);

    return NextResponse.json({
      onboarding_state: onboarding?.onboarding_state ?? 'new',
      risk_bucket,
      risk_score,
      portfolio_preferences: prefs ?? null,
      updated_at: onboarding?.updated_at ?? null,
    });
  } catch (error: any) {
    console.error('Failed to fetch onboarding info:', error);
    return NextResponse.json({ error: error?.message || 'Internal error' }, { status: 500 });
  }
}
