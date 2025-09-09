import { NextRequest, NextResponse } from 'next/server';
import { getKindeServerSession } from '@kinde-oss/kinde-auth-nextjs/server';
import { emitEvent } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  try {
    const BACKEND_URL = process.env.NODE_ENV === 'development'
      ? 'http://localhost:8000'
      : process.env.BACKEND_URL || '';

    const body = await request.json();

    const resp = await fetch(`${BACKEND_URL}/api/rebalance/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': request.headers.get('x-api-key') || '',
      },
      body: JSON.stringify(body),
    });

    const data = await resp.json();

    // Fire-and-forget event emission
    try {
      const { getUser } = getKindeServerSession();
      const user = await getUser();
      const kindeUserId = user?.id || '';
      if (kindeUserId && resp.ok && data?.decision) {
        const type = data.decision === 'rebalance' ? 'DRIFT_REBALANCE' : 'DRIFT_CHECK_NO_ACTION';
        const summary = data.summary || `Decision: ${data.decision}`;
        const description = data.decision === 'rebalance'
          ? `Proposed ${Array.isArray(data.trades) ? data.trades.length : 0} trades; max drift ${data.max_drift_pct}%`
          : `Max drift ${data.max_drift_pct}% within threshold ${data.drift_threshold_pct}%`;
        await emitEvent({
          kindeUserId,
          accountId: undefined,
          type,
          summary,
          description,
          meta: {
            decision: data.decision,
            decision_hash: data.decision_hash,
            max_drift_pct: data.max_drift_pct,
            drift_threshold_pct: data.drift_threshold_pct,
            turnover: data.turnover,
            trades: data.trades,
          }
        });
      }
    } catch (e) {
      console.warn('Failed to emit rebalance event:', e);
    }

    return NextResponse.json(data, { status: resp.status });
  } catch (error: any) {
    console.error('Rebalance Run API Error:', error);
    return NextResponse.json(
      { error: error?.message || 'Failed to run rebalance' },
      { status: 500 }
    );
  }
}
