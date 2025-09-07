import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { getAccount, getPositions } from "@/lib/alpacaBroker";
import { getActivitiesByUser } from "@/lib/supabase";

function safeParseNumber(val?: string | number | null): number {
  if (val === undefined || val === null) return 0;
  const n = typeof val === 'number' ? val : Number(val);
  return Number.isFinite(n) ? n : 0;
}

export async function POST(req: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await req.json().catch(() => ({}));
    let accountId: string | undefined = body?.accountId;

    // Derive accountId from activities if not provided
    if (!accountId) {
      const acts = await getActivitiesByUser(user.id, 20);
      const actWithAcct = acts.find((a: any) => a?.meta?.alpaca_account_id);
      accountId = actWithAcct?.meta?.alpaca_account_id;
    }

    if (!accountId) {
      return NextResponse.json({ error: "No account found for user" }, { status: 404 });
    }

    const [account, positions] = await Promise.all([
      getAccount(accountId),
      getPositions(accountId)
    ]);

    const cash = safeParseNumber(account.cash);
    const portfolioValue = safeParseNumber(account.portfolio_value);

    // Build normalized holdings
    const normPositions = (positions || []).map((p: any) => {
      const mv = safeParseNumber(p.market_value);
      const qty = safeParseNumber(p.qty);
      return {
        symbol: p.symbol,
        qty,
        market_value: mv,
      };
    }).sort((a: any, b: any) => b.market_value - a.market_value);

    const positionsTotal = normPositions.reduce((sum: number, p: any) => sum + p.market_value, 0);
    const total = positionsTotal + cash || portfolioValue || positionsTotal; // fallback to portfolio_value

    const withPercent = normPositions.map((p: any) => ({
      ...p,
      percent: total > 0 ? (p.market_value / total) * 100 : 0,
    }));

    const cashPercent = total > 0 ? (cash / total) * 100 : 0;

    return NextResponse.json({
      success: true,
      accountId,
      cash,
      portfolio_value: portfolioValue || total,
      positions: withPercent,
      cash_percent: cashPercent,
      as_of: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Failed to fetch holdings:', error);
    return NextResponse.json({ error: error.message || 'Failed to fetch holdings' }, { status: 500 });
  }
}
