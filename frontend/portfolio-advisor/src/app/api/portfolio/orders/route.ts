import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { getOrders } from "@/lib/alpacaBroker";
import { getActivitiesByUser } from "@/lib/supabase";

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

    if (!accountId) {
      const acts = await getActivitiesByUser(user.id, 20);
      const actWithAcct = acts.find((a: any) => a?.meta?.alpaca_account_id);
      accountId = actWithAcct?.meta?.alpaca_account_id;
    }

    if (!accountId) {
      return NextResponse.json({ error: "No account found for user" }, { status: 404 });
    }

    const openOrders = await getOrders(accountId, 'open');

    return NextResponse.json({
      success: true,
      accountId,
      open_count: Array.isArray(openOrders) ? openOrders.length : 0,
      open_orders: openOrders || [],
      as_of: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Failed to fetch orders:', error);
    return NextResponse.json({ error: error.message || 'Failed to fetch orders' }, { status: 500 });
  }
}
