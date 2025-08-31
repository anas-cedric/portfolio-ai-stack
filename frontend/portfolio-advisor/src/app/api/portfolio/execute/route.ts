import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { 
  getAccount,
  createJournalUSD,
  placeOrder,
  generateClientOrderId,
  getLatestTrades,
  calculateNotionalAmount,
  type NotionalOrder
} from "@/lib/alpacaBroker";
import { logActivity, logOrderSubmission } from "@/lib/supabase";

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

    // 2. Fund the account (journal from firm account to user account)
    const firmAccountId = process.env.ALPACA_FIRM_ACCOUNT_ID!;
    console.log(`Funding account ${accountId} with $${totalInvestment} from firm account ${firmAccountId}`);
    
    try {
      await createJournalUSD(firmAccountId, accountId, totalInvestment);
      console.log(`Account ${accountId} funded successfully`);
      
      await logActivity(
        user.id,
        'info',
        'Account funded successfully',
        `Your paper trading account has been funded with $${totalInvestment.toLocaleString()} and is ready for trading.`,
        { 
          alpaca_account_id: accountId,
          funding_amount: totalInvestment,
          account_status: account.status
        },
        accountId
      );
    } catch (error: any) {
      console.error('Funding failed:', error);
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

    // 3. Get current prices for all symbols
    const symbols = weights.map(w => w.symbol).filter(s => s !== 'CASH');
    const prices = await getLatestTrades(symbols);
    console.log('Current prices:', prices);

    // 4. Calculate order amounts and prepare orders
    const orders: NotionalOrder[] = [];
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
        account_status: 'ACTIVE'
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
      message: `Portfolio execution completed. ${executedOrders.length} orders placed successfully.`
    });
    
  } catch (error: any) {
    console.error('Portfolio execution error:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to execute portfolio' 
    }, { status: 500 });
  }
}