import { NextRequest, NextResponse } from 'next/server';
import { getKindeServerSession } from '@kinde-oss/kinde-auth-nextjs/server';
import { saveRiskProfile, getOrCreateUserOnboardingState } from '@/lib/supabase';

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
    const risk_bucket: string | null = typeof body?.risk_bucket === 'string' ? body.risk_bucket : null;
    const risk_score: number | null = typeof body?.risk_score === 'number' ? body.risk_score : null;

    // Ensure onboarding row exists and then upsert risk
    await getOrCreateUserOnboardingState(user.id);
    const onboarding = await saveRiskProfile(user.id, risk_bucket ?? undefined, risk_score ?? undefined);

    return NextResponse.json({ success: true, onboarding });
  } catch (error: any) {
    console.error('Failed to save risk profile:', error);
    return NextResponse.json({ error: error?.message || 'Internal error' }, { status: 500 });
  }
}
