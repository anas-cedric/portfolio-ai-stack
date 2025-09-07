import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { 
  getAccount,
  createJournalUSD,
  placeOrder,
  generateClientOrderId,
  getLatestTrades,
  calculateNotionalAmount,
  getPositions,
  getOrders,
  type NotionalOrder
} from "@/lib/alpacaBroker";
import { logActivity, logOrderSubmission, getActivitiesByUser } from "@/lib/supabase";

type Weight = { 
  symbol: string; 
  weight: number; // 0-100 percentage
};

type RequestBody = {
  accountId: string;
  weights: Weight[];
  totalInvestment?: number;
};

// Helper to batch arrays
function toBatches<T>(arr: T[], size: number): T[][] {
  const batches: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    batches.push(arr.slice(i, i + size));
  }
  return batches;
}

// --- Utility helpers for execution flow ---
function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

function safeParseNumber(val?: string | number | null): number {
  if (val === undefined || val === null) return 0;
  const n = typeof val === 'number' ? val : Number(val);
  return Number.isFinite(n) ? n : 0;
}

async function waitForBuyingPower(
  accountId: string,
  minRequired: number,
  timeoutMs = 30000,
  pollIntervalMs = 1500
): Promise<{ buyingPower: number; cash: number; attempts: number; snapshots: Array<{ ts: string; status: string; buying_power?: string; cash?: string }> }> {
  const start = Date.now();
  let attempts = 0;
  const snapshots: Array<{ ts: string; status: string; buying_power?: string; cash?: string }> = [];
  while (Date.now() - start < timeoutMs) {
    attempts += 1;
    const acc = await getAccount(accountId);
    snapshots.push({ ts: new Date().toISOString(), status: acc.status, buying_power: acc.buying_power, cash: acc.cash });
    const bp = safeParseNumber(acc.buying_power);
    const cash = safeParseNumber(acc.cash);
    if (bp >= minRequired) {
      return { buyingPower: bp, cash, attempts, snapshots };
    }
    await sleep(pollIntervalMs);
  }
  // Return last known values if timeout
  const last = snapshots[snapshots.length - 1];
  return { buyingPower: last ? safeParseNumber(last.buying_power) : 0, cash: last ? safeParseNumber(last.cash) : 0, attempts, snapshots };
}

export async function POST(req: NextRequest) {
  try {
    // Get authenticated user
    const { getUser } = getKindeServerSession();
    const user = await getUser();
    
    if (!user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse request body
    const body: RequestBody = await req.json();
    const { accountId, weights, totalInvestment = 10000 } = body;
    
    // Basic validation
    if (!accountId || !weights || weights.length === 0) {
      return NextResponse.json({ 
        error: "Missing required parameters" 
      }, { status: 400 });
    }

    // Normalize weights if provided as 0-1 fractions (convert to 0-100 percentages)
    const weightSum = weights.reduce((acc, w) => acc + (Number.isFinite(w.weight) ? w.weight : 0), 0);
    let weightsNormalized = false;
    if (weightSum > 0 && weightSum <= 1.01) {
      for (const w of weights) {
        w.weight = Math.round(w.weight * 10000) / 100; // keep two decimals after converting to %
      }
      weightsNormalized = true;
      console.log('Normalized fractional weights to percentages. New weights:', weights);
    }

    console.log('Executing portfolio trades for account:', accountId);

    // 1. Check account status
    const account = await getAccount(accountId);
    console.log(`Account ${accountId} status: ${account.status}`);

    if (account.status !== 'ACTIVE') {
      return NextResponse.json({
        error: `Account not ready for trading. Status: ${account.status}`,
        accountStatus: account.status
      }, { status: 400 });
    }

    // ---------------- Idempotency & duplicate-execution guards ----------------
    // 0) If positions already exist, assume portfolio already executed — skip funding and orders
    try {
      const existingPositions = await getPositions(accountId);
      if (Array.isArray(existingPositions) && existingPositions.length > 0) {
        await logActivity(
          user.id,
          'info',
          'Portfolio already executed',
          'Detected existing positions; skipping duplicate funding and orders.',
          {
            alpaca_account_id: accountId,
            positions_detected: existingPositions.length,
            internal: true
          },
          accountId
        );
        return NextResponse.json({
          success: true,
          accountId,
          skipped: true,
          reason: 'positions_exist',
          positions: existingPositions.length,
          message: 'Portfolio already executed. Skipping.',
        });
      }
    } catch {}

    // 1) If there are open orders, treat as in-progress and avoid duplicates
    try {
      const openOrders = await getOrders(accountId, 'open');
      if (Array.isArray(openOrders) && openOrders.length > 0) {
        await logActivity(
          user.id,
          'info',
          'Portfolio execution in progress',
          'Open orders detected; skipping duplicate order placement.',
          {
            alpaca_account_id: accountId,
            open_orders: openOrders.length,
            internal: true
          },
          accountId
        );
        return NextResponse.json({
          success: true,
          accountId,
          skipped: true,
          reason: 'orders_in_progress',
          openOrders: openOrders.length,
          message: 'Open orders in progress. Skipping duplicate execution.',
        });
      }
    } catch {}

    // 2) If Supabase shows a prior trade_executed activity, skip
    try {
      const acts = await getActivitiesByUser(user.id, 10);
      if (Array.isArray(acts) && acts.some((a: any) => a?.type === 'trade_executed' || a?.meta?.trades_executed === true)) {
        await logActivity(
          user.id,
          'info',
          'Portfolio already executed (activity)',
          'Found prior execution activity; skipping duplicate execution.',
          {
            alpaca_account_id: accountId,
            internal: true
          },
          accountId
        );
        return NextResponse.json({
          success: true,
          accountId,
          skipped: true,
          reason: 'prior_activity_detected',
          message: 'Prior execution activity found. Skipping.',
        });
      }
    } catch {}

    // Capture pre-funding snapshots
    const preBuyingPower = safeParseNumber(account.buying_power);
    const preCash = safeParseNumber(account.cash);
    let postBuyingPower = preBuyingPower;
    let postCash = preCash;
    let bpPollAttempts = 0;
    let bpSnapshots: Array<{ ts: string; status: string; buying_power?: string; cash?: string }> = [];
    let fundingAttempted = false;
    let fundingSucceeded = false;

    // 2. Fund the account (journal from firm account to user account) if needed
    const firmAccountId = process.env.ALPACA_FIRM_ACCOUNT_ID;
    console.log(`Funding plan: $${totalInvestment} from firm account ${firmAccountId ?? '(not configured)'}`);
    
    const needsFunding = !Number.isFinite(preBuyingPower) || preBuyingPower < totalInvestment * 0.9;
    if (firmAccountId && needsFunding) {
      fundingAttempted = true;
      try {
        await createJournalUSD(firmAccountId, accountId, totalInvestment);
        console.log(`Account ${accountId} funded successfully`);

        // Wait for buying power to reflect funding (tolerate 10% slack)
        const waitRes = await waitForBuyingPower(accountId, preBuyingPower + totalInvestment * 0.9);
        postBuyingPower = waitRes.buyingPower;
        postCash = waitRes.cash;
        bpPollAttempts = waitRes.attempts;
        bpSnapshots = waitRes.snapshots;
        fundingSucceeded = true;
        
        await logActivity(
          user.id,
          'info',
          'Account funded successfully',
          `Your paper trading account has been funded with $${totalInvestment.toLocaleString()} and is ready for trading.`,
          { 
            alpaca_account_id: accountId,
            funding_amount: totalInvestment,
            account_status: account.status,
            pre_buying_power: preBuyingPower,
            post_buying_power: postBuyingPower,
            pre_cash: preCash,
            post_cash: postCash,
            bp_poll_attempts: bpPollAttempts,
            internal: true
          },
          accountId
        );
      } catch (error: any) {
        console.error('Funding failed or delayed:', error);
        await logActivity(
          user.id,
          'warning',
          'Account funding delayed',
          'There was an issue funding your account. This is normal in sandbox mode. Orders will still be placed.',
          { 
            alpaca_account_id: accountId,
            funding_error: error.message
          },
          accountId
        );
        // Continue with orders even if funding fails (sandbox mode)
      }
    } else {
      console.warn('ALPACA_FIRM_ACCOUNT_ID not configured. Skipping funding journal.');
      await logActivity(
        user.id,
        'warning',
        needsFunding ? 'Funding skipped' : 'Funding not required',
        needsFunding
          ? 'Firm account ID not configured on server. Attempting to place orders with existing buying power.'
          : 'Detected sufficient buying power/cash; funding not required.',
        { alpaca_account_id: accountId, pre_buying_power: preBuyingPower, pre_cash: preCash },
        accountId
      );
    }

    // 3. Get current prices for all symbols
    const symbols = weights.map(w => w.symbol).filter(s => s !== 'CASH');
    const prices = await getLatestTrades(symbols);
    console.log('Current prices:', prices);

    // 4. Calculate order amounts and prepare orders
    let orders: NotionalOrder[] = [];
    let cashAllocation = 0;

    for (const weight of weights) {
      if (weight.symbol === 'CASH') {
        cashAllocation += weight.weight;
        continue;
      }

      const notionalAmount = calculateNotionalAmount(totalInvestment, weight.weight);
      console.log(`${weight.symbol}: ${weight.weight}% = $${notionalAmount}`);

      if (notionalAmount >= 1) { // Minimum $1 order
        orders.push({
          symbol: weight.symbol,
          side: 'buy',
          notional: notionalAmount,
          time_in_force: 'day',
          client_order_id: generateClientOrderId(user.id, weight.symbol),
          type: 'market',
          extended_hours: false
        });
      }
    }

    console.log(`Prepared ${orders.length} orders, ${cashAllocation}% cash allocation`);

    // Scale down to available buying power if necessary
    const originalTotalNotional = orders.reduce((sum, o) => sum + (o.notional || 0), 0);
    const availableBuyingPower = postBuyingPower || safeParseNumber(account.buying_power);
    if (originalTotalNotional > 0 && availableBuyingPower > 0 && originalTotalNotional > availableBuyingPower) {
      const scale = availableBuyingPower / originalTotalNotional;
      orders = orders.map(o => ({ ...o, notional: Math.max(1, Number((o.notional * scale).toFixed(2))) }));
      console.log(`Scaled orders by factor ${scale.toFixed(4)} to fit buying power $${availableBuyingPower.toFixed(2)} (from $${originalTotalNotional.toFixed(2)})`);
    }

    // 5. Execute orders in batches
    const orderBatches = toBatches(orders, 5); // Process 5 orders at a time
    const executedOrders: any[] = [];
    const failedOrders: any[] = [];

    for (let batchIndex = 0; batchIndex < orderBatches.length; batchIndex++) {
      const batch = orderBatches[batchIndex];
      console.log(`Executing batch ${batchIndex + 1}/${orderBatches.length} with ${batch.length} orders`);

      const batchPromises = batch.map(async (order) => {
        try {
          const result = await placeOrder(accountId, order);
          console.log(`Order placed: ${order.symbol} - ${result.id}`);

          // Log successful order
          await logOrderSubmission(
            user.id,
            accountId,
            result.client_order_id || order.client_order_id || '',
            {
              order_id: result.id,
              symbol: order.symbol,
              side: 'buy',
              notional: order.notional,
              type: 'market',
              status: 'submitted'
            }
          );

          return { success: true, order: result };
        } catch (error: any) {
          console.error(`Failed to place order for ${order.symbol}:`, error);
          
          // Log failed order
          await logOrderSubmission(
            user.id,
            accountId,
            order.client_order_id || '',
            {
              symbol: order.symbol,
              side: 'buy',
              notional: order.notional,
              type: 'market',
              status: 'failed',
              error_message: error.message
            }
          );

          return { success: false, symbol: order.symbol, error: error.message };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      
      batchResults.forEach(result => {
        if (result.success) {
          executedOrders.push(result.order);
        } else {
          failedOrders.push(result);
        }
      });

      // Small delay between batches to avoid rate limits
      if (batchIndex < orderBatches.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    // 6. Log final results
    const successRate = (executedOrders.length / orders.length) * 100;
    
    await logActivity(
      user.id,
      executedOrders.length > 0 ? 'trade_executed' : 'warning',
      `Portfolio execution ${executedOrders.length > 0 ? 'completed' : 'failed'}`,
      `${executedOrders.length} of ${orders.length} orders executed successfully (${successRate.toFixed(1)}% success rate). ${cashAllocation > 0 ? `${cashAllocation}% allocated to cash.` : ''}`,
      {
        total_orders: orders.length,
        successful_orders: executedOrders.length,
        failed_orders: failedOrders.length,
        success_rate: successRate,
        cash_allocation: cashAllocation,
        executed_order_ids: executedOrders.map(o => o.id),
        trades_executed: true,
        account_status: 'ACTIVE',
        pre_buying_power: preBuyingPower,
        post_buying_power: postBuyingPower,
        pre_cash: preCash,
        post_cash: postCash,
        bp_poll_attempts: bpPollAttempts,
        funding_attempted: fundingAttempted,
        funding_succeeded: fundingSucceeded,
        weights_normalized: weightsNormalized
      },
      accountId
    );

    return NextResponse.json({
      success: true,
      accountId,
      totalOrders: orders.length,
      executedOrders: executedOrders.length,
      failedOrders: failedOrders.length,
      successRate,
      cashAllocation,
      preBuyingPower,
      postBuyingPower,
      preCash,
      postCash,
      bpPollAttempts,
      fundingAttempted,
      fundingSucceeded,
      message: `Portfolio execution completed. ${executedOrders.length} orders placed successfully.`
    });
    
  } catch (error: any) {
    console.error('Portfolio execution error:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to execute portfolio' 
    }, { status: 500 });
  }
}