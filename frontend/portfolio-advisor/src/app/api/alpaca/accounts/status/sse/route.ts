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

    // Build upstream Alpaca SSE URL (ensure we don't drop the '/v1' path)
    // If ALPACA_BASE_URL is provided, it may be either with or without trailing '/v1' and/or '/'
    // Normalize to avoid URL resolution removing path segments.
    const rawBase = process.env.ALPACA_BASE_URL || "https://broker-api.sandbox.alpaca.markets";
    const baseNoSlash = rawBase.replace(/\/$/, '');
    const baseWithV1 = /\/v1$/.test(baseNoSlash) ? baseNoSlash : `${baseNoSlash}/v1`;
    const upstreamUrl = new URL(`${baseWithV1}/events/accounts/status`);
    

    const since = url.searchParams.get("since");
    const since_id = url.searchParams.get("since_id");
    const since_ulid = url.searchParams.get("since_ulid");
    const sinceCount = [since, since_id, since_ulid].filter(Boolean).length;
    if (sinceCount > 1) {
      return new Response(JSON.stringify({ error: "Only one of since, since_id, since_ulid may be used" }), { status: 400 });
    }
    if (since) upstreamUrl.searchParams.set("since", since);
    if (since_id) upstreamUrl.searchParams.set("since_id", since_id);
    if (since_ulid) upstreamUrl.searchParams.set("since_ulid", since_ulid);

    const key = process.env.ALPACA_API_KEY_ID;
    const secret = process.env.ALPACA_API_SECRET;
    if (!key || !secret) {
      return new Response(JSON.stringify({ error: "Missing Alpaca credentials" }), { status: 500 });
    }
    const authHeader = "Basic " + Buffer.from(`${key}:${secret}`).toString("base64");

    const upstream = await fetch(upstreamUrl.toString(), {
      method: "GET",
      headers: {
        "Accept": "text/event-stream",
        "Authorization": authHeader,
      },
      // If the client disconnects, propagate abort to upstream
      signal: req.signal,
    });

    if (!upstream.ok || !upstream.body) {
      const text = await upstream.text().catch(() => "");
      return new Response(
        JSON.stringify({ error: "Upstream SSE connection failed", status: upstream.status, body: text }),
        { status: 502 }
      );
    }

    const encoder = new TextEncoder();
    const decoder = new TextDecoder();
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();

    // Heartbeat to keep the connection alive
    const heartbeat = setInterval(() => {
      writer.write(encoder.encode(`: ping\n\n`)).catch(() => {/* ignore */});
    }, 25000);

    const close = async () => {
      clearInterval(heartbeat);
      try { await writer.close(); } catch {}
    };

    req.signal.addEventListener("abort", () => {
      close();
    });

    // Write initial comment so clients know we're connected
    await writer.write(encoder.encode(`: connected\n\n`));

    // Read and filter upstream SSE by accountId
    const reader = upstream.body.getReader();
    let buffer = "";

    (async () => {
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let idx: number;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const rawEvent = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);

            // Extract data lines
            const dataLines = rawEvent
              .split("\n")
              .filter((l) => l.startsWith("data:"))
              .map((l) => l.slice(5).trimStart());

            if (dataLines.length === 0) continue;
            const dataStr = dataLines.join("\n");

            let payload: any;
            try {
              payload = JSON.parse(dataStr);
            } catch {
              continue; // ignore non-JSON
            }

            // Try common locations for account id in payload
            const evAccountId = payload?.account_id || payload?.id || payload?.account?.id || payload?.accountId;
            if (evAccountId !== accountId) {
              continue; // do not leak other accounts
            }

            // Forward filtered event to client
            await writer.write(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
          }
        }
      } catch (err) {
        // On error, end stream gracefully
      } finally {
        await close();
      }
    })();

    return new Response(readable, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (error: any) {
    console.error("SSE proxy error:", error);
    return new Response(JSON.stringify({ error: error?.message || "Internal error" }), { status: 500 });
  }
}
