import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { createJournal, type JournalRequest } from "@/lib/alpacaBroker";
import { logActivity } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  let userId: string | null = null;
  try {
    // Auth
    const { getUser } = getKindeServerSession();
    const user = await getUser();
    userId = user?.id ?? null;

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse and validate
    const body = await req.json();
    const entry_type = body.entry_type as JournalRequest["entry_type"]; // "JNLC" | "JNLS"
    const from_account: string | undefined = body.from_account || process.env.ALPACA_FIRM_ACCOUNT_ID;
    const to_account: string | undefined = body.to_account;
    const amount: string | undefined = body.amount;
    const symbol: string | undefined = body.symbol;
    const qty: string | undefined = body.qty;

    if (!entry_type || !from_account || !to_account) {
      return NextResponse.json(
        { error: "from_account, to_account, and entry_type are required" },
        { status: 400 }
      );
    }

    if (entry_type === "JNLC" && !amount) {
      return NextResponse.json(
        { error: "amount is required for JNLC (cash) journals" },
        { status: 400 }
      );
    }

    if (entry_type === "JNLS" && (!symbol || !qty)) {
      return NextResponse.json(
        { error: "symbol and qty are required for JNLS (securities) journals" },
        { status: 400 }
      );
    }

    const journal: JournalRequest = {
      entry_type,
      from_account,
      to_account,
      amount,
      symbol,
      qty,
    };

    const result = await createJournal(journal);

    await logActivity(
      userId,
      "info",
      entry_type === "JNLC" ? "Cash journal posted" : "Securities journal posted",
      entry_type === "JNLC"
        ? `Transferred $${amount} from ${from_account} to ${to_account}.`
        : `Transferred ${qty} ${symbol} from ${from_account} to ${to_account}.`,
      {
        journal_entry_type: entry_type,
        from_account,
        to_account,
        amount,
        symbol,
        qty,
        journal_id: result?.id,
      },
      to_account
    );

    return NextResponse.json({ success: true, journal: result });
  } catch (error: any) {
    console.error("Journal creation failed:", error);
    if (userId) {
      try {
        await logActivity(
          userId,
          "warning",
          "Journal creation failed",
          error.message || "Failed to create journal",
          { error_message: error.message }
        );
      } catch {}
    }
    return NextResponse.json(
      { error: error.message || "Failed to create journal" },
      { status: 500 }
    );
  }
}
