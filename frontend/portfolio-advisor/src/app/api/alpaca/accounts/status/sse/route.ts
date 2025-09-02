import { NextRequest } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { getActivitiesByUser } from "@/lib/supabase";

// Node runtime (not Edge) to reuse existing Kinde session utilities.
// Streams Alpaca Account Status SSE and filters events by accountId before forwarding to the browser.

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { getUser } = getKindeServerSession();
    const user = await getUser();
    if (!user?.id) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });
    }

    const url = new URL(req.url);
    const accountId = url.searchParams.get("accountId");
    if (!accountId) {
      return new Response(JSON.stringify({ error: "Missing accountId" }), { status: 400 });
    }

    // Validate that the requested accountId belongs to the current user
    try {
      const activities = await getActivitiesByUser(user.id, 20);
      const ownsAccount = activities.some((a: any) =>
        a?.meta?.alpaca_account_id === accountId || (a as any)?.alpaca_account_id === accountId
      );
      if (!ownsAccount) {
        return new Response(JSON.stringify({ error: "Forbidden" }), { status: 403 });
      }
    } catch (e) {
      // If Supabase isn't configured, allow but warn.
      console.warn("SSE account validation skipped due to Supabase error:", e);
    }

    // Redirect to Railway backend SSE proxy to avoid Vercel 300s limit
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://portfolio-ai-stack-production.up.railway.app";
    const target = new URL("/alpaca/accounts/status/sse", apiUrl);
    target.searchParams.set("accountId", accountId);

    // Optional since* passthrough
    let since = url.searchParams.get("since");
    let since_id = url.searchParams.get("since_id");
    let since_ulid = url.searchParams.get("since_ulid");
    // Fallback to Last-Event-ID header if no explicit since provided
    const lastEventId = req.headers.get('last-event-id');
    if (!since && !since_id && !since_ulid && lastEventId) {
      since_id = lastEventId;
    }
    const sinceCount = [since, since_id, since_ulid].filter(Boolean).length;
    if (sinceCount > 1) {
      return new Response(JSON.stringify({ error: "Only one of since, since_id, since_ulid may be used" }), { status: 400 });
    }
    if (since) target.searchParams.set("since", since);
    if (since_id) target.searchParams.set("since_id", since_id);
    if (since_ulid) target.searchParams.set("since_ulid", since_ulid);

    console.log("[SSE] Redirecting to backend SSE", {
      userId: user.id,
      accountId,
      redirectUrl: target.toString(),
    });

    return new Response(null, {
      status: 307,
      headers: {
        Location: target.toString(),
        "Cache-Control": "no-cache, no-transform",
      },
    });
  } catch (error: any) {
    console.error("SSE proxy error:", error);
    return new Response(JSON.stringify({ error: error?.message || "Internal error" }), { status: 500 });
  }
}
