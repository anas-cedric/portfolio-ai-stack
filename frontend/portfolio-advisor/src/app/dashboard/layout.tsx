import { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { getAuthUser } from '@/lib/auth';
import { getUserOnboardingState } from '@/lib/supabase';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const user = await getAuthUser();
  if (!user?.id) {
    redirect('/api/auth/login');
  }

  // Fetch onboarding record (read-only). If none, treat as 'new'.
  const onboarding = await getUserOnboardingState(user.id);
  const state = onboarding?.onboarding_state ?? 'new';

  // Enforce quiz completion before accessing dashboard
  const order = ['new', 'quiz_completed', 'portfolio_approved', 'active'] as const;
  const idx = order.indexOf(state as any);
  const minIdx = order.indexOf('quiz_completed');
  if (idx === -1 || idx < minIdx) {
    redirect('/portfolio-quiz');
  }

  return <>{children}</>;
}
