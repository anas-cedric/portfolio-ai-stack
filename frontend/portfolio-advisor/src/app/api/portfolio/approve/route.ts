import { NextRequest, NextResponse } from "next/server";
import { 
  createPaperAccount, 
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
  weights: Weight[];
  totalInvestment?: number; // Optional, defaults to 10000
  userId: string; // Pass from client
  userEmail: string;
  userFirstName?: string;
  userLastName?: string;
};

// Helper to batch arrays
function toBatches<T>(arr: T[], size: number): T[][] {
  const batches: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    batches.push(arr.slice(i, i + size));
  }
  return batches;
}

// Generate a unique, valid-format test SSN for sandbox based on user ID
function generateTestSSN(userId: string): string {
  // Use 900-999 range (often used for testing) + hash user ID to 6 digits
  const hash = userId.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a; // Convert to 32-bit integer
  }, 0);
  
  // Generate area number 900-999 from user hash
  const area = 900 + (Math.abs(hash) % 100); // 900-999
  
  // Ensure we get a positive 6-digit number for group+serial
  const sixDigits = Math.abs(hash % 1000000).toString().padStart(6, '0');
  
  // Ensure group is not 00
  const group = sixDigits.slice(0, 2) === '00' ? '01' : sixDigits.slice(0, 2);
  
  // Ensure serial is not 0000
  const serial = sixDigits.slice(2, 6) === '0000' ? '0001' : sixDigits.slice(2, 6);
  
  // Format as XXXGGSSSS (area + group + serial, no dashes for API)
  return `${area}${group}${serial}`;
}

// Note: We now store Alpaca account IDs in Supabase via activity logging
// No separate storage function needed as we log the account creation

// Get or create Alpaca account for user
async function ensureAlpacaAccount(
  userId: string, 
  email: string, 
  givenName: string, 
  familyName: string
): Promise<string> {
  // Check if user already has an Alpaca account (from your backend or local storage)
  // For MVP, we'll create a new account each time
  // In production, you'd check your database first
  
  try {
    // Create new paper account
    const account = await createPaperAccount({
      contact: {
        email_address: email,
        given_name: givenName,
        family_name: familyName,
        phone_number: "555-555-0100",
        street_address: ["123 Main Street"],
        city: "Los Angeles", 
        state: "CA",
        postal_code: "90210",
        country: "USA"
      },
      identity: {
        given_name: givenName,
        family_name: familyName,
        date_of_birth: "1990-01-01", // You should collect this properly
        tax_id: generateTestSSN(userId), // Generate unique test SSN based on user ID
        tax_id_type: "USA_SSN",
        country_of_citizenship: "USA",
        country_of_tax_residence: "USA",
        funding_source: ["employment_income"]
      },
      disclosures: {
        is_control_person: false,
        is_affiliated_exchange_or_finra: false,
        is_politically_exposed: false,
        immediate_family_exposed: false,
      },
      agreements: [
        {
          agreement: "customer_agreement",
          signed_at: new Date().toISOString(),
          ip_address: "127.0.0.1"
        },
        {
          agreement: "crypto_agreement", 
          signed_at: new Date().toISOString(),
          ip_address: "127.0.0.1"
        }
      ]
    });

    return account.id;
  } catch (error: any) {
    console.error('Failed to create Alpaca account - Full error:', {
      status: error?.response?.status,
      statusText: error?.response?.statusText,
      data: error?.response?.data,
      message: error?.message,
      url: error?.config?.url
    });
    
    // Return more specific error message
    const alpacaError = error?.response?.data?.message || error?.message || 'Unknown Alpaca error';
    throw new Error(`Alpaca account creation failed: ${alpacaError}`);
  }
}

export async function POST(req: NextRequest) {
  try {
    // Parse request body (user info passed from authenticated client)
    const body: RequestBody = await req.json();
    const { 
      weights, 
      totalInvestment = 10000,
      userId,
      userEmail,
      userFirstName = "User",
      userLastName = "Account"
    } = body;
    
    // Basic validation
    if (!userId || !userEmail) {
      return NextResponse.json({ 
        error: "Missing user information" 
      }, { status: 400 });
    }
    
    console.log('Processing portfolio for user:', { userId, userEmail });
    
    if (!weights || weights.length === 0) {
      return NextResponse.json({ error: "No portfolio weights provided" }, { status: 400 });
    }

    // Validate weights sum to ~100% (allow 2% tolerance for floating point precision)
    const totalWeight = weights.reduce((sum, w) => sum + w.weight, 0);
    if (Math.abs(totalWeight - 100) > 2) {
      return NextResponse.json({ 
        error: `Weights must sum to approximately 100%, got ${totalWeight}%` 
      }, { status: 400 });
    }

    // Check Alpaca configuration
    if (!process.env.ALPACA_API_KEY_ID || !process.env.ALPACA_API_SECRET || !process.env.ALPACA_FIRM_ACCOUNT_ID) {
      console.error('Missing Alpaca configuration:', {
        hasKey: !!process.env.ALPACA_API_KEY_ID,
        hasSecret: !!process.env.ALPACA_API_SECRET,
        hasFirmAccount: !!process.env.ALPACA_FIRM_ACCOUNT_ID
      });
      return NextResponse.json({ 
        error: "Alpaca not configured properly. Please check environment variables." 
      }, { status: 500 });
    }

    // 3. Ensure user has an Alpaca account
    const accountId = await ensureAlpacaAccount(
      userId,
      userEmail,
      userFirstName,
      userLastName
    );

    // Log account creation activity
    await logActivity(
      userId,
      'info',
      'Cedric created your $10,000 simulated portfolio',
      `Your paper trading account has been funded and is ready for trading. Account ID: ${accountId}`,
      { alpaca_account_id: accountId, total_investment: totalInvestment },
      accountId
    );

    // 4. Fund the account (journal from firm account)
    const firmAccountId = process.env.ALPACA_FIRM_ACCOUNT_ID!;
    
    try {
      await createJournalUSD(firmAccountId, accountId, totalInvestment);
      console.log(`Funded account ${accountId} with $${totalInvestment}`);
    } catch (error: any) {
      // Journaling might fail if already funded or insufficient firm balance
      console.warn('Journal failed (may already be funded):', error?.response?.data || error.message);
    }

    // 5. Get current prices for the symbols
    const symbols = weights.map(w => w.symbol);
    const prices = await getLatestTrades(symbols);

    // 6. Build notional orders
    const MIN_NOTIONAL = 1.00; // Alpaca minimum for fractional shares
    const orders: NotionalOrder[] = [];
    
    for (const weight of weights) {
      const targetAmount = calculateNotionalAmount(totalInvestment, weight.weight);
      
      if (targetAmount < MIN_NOTIONAL) {
        console.log(`Skipping ${weight.symbol}: $${targetAmount} below minimum`);
        continue;
      }
      
      orders.push({
        symbol: weight.symbol,
        side: "buy",
        notional: targetAmount,
        time_in_force: "day",
        client_order_id: generateClientOrderId(userId, weight.symbol),
        type: "market"
      });
    }

    // 7. Submit orders in batches
    const batches = toBatches(orders, 10); // Submit 10 at a time
    const submittedOrders: any[] = [];
    const failedOrders: any[] = [];
    
    for (const batch of batches) {
      await Promise.all(
        batch.map(async (order) => {
          try {
            const result = await placeOrder(accountId, order);
            
            // Log successful order
            await logOrderSubmission(userId, accountId, order.client_order_id || `order-${Date.now()}-${order.symbol}`, {
              order: order,
              result: result,
              status: 'submitted'
            });
            
            submittedOrders.push({
              symbol: order.symbol,
              notional: order.notional,
              orderId: result.id,
              status: result.status
            });
            console.log(`Order placed: ${order.symbol} for $${order.notional}`);
          } catch (error: any) {
            console.error(`Order failed for ${order.symbol}:`, error?.response?.data || error.message);
            
            // Log failed order
            await logOrderSubmission(userId, accountId, order.client_order_id || `order-${Date.now()}-${order.symbol}`, {
              order: order,
              error: error?.response?.data || error.message,
              status: 'failed'
            });
            
            failedOrders.push({
              symbol: order.symbol,
              notional: order.notional,
              error: error?.response?.data?.message || error.message
            });
          }
        })
      );
      
      // Small delay between batches to respect rate limits
      if (batches.length > 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    // 8. Log order execution summary
    await logActivity(
      userId,
      'trade_executed',
      `Portfolio execution completed`,
      `Successfully submitted ${submittedOrders.length} orders, ${failedOrders.length} failed. Total investment: $${totalInvestment}`,
      {
        orders_submitted: submittedOrders.length,
        orders_failed: failedOrders.length,
        submitted_orders: submittedOrders,
        failed_orders: failedOrders
      },
      accountId
    );

    // 9. Return summary
    return NextResponse.json({
      success: true,
      accountId,
      summary: {
        totalInvestment,
        ordersSubmitted: submittedOrders.length,
        ordersFailed: failedOrders.length,
        submittedOrders,
        failedOrders
      }
    });
    
  } catch (error: any) {
    console.error('Portfolio approval error:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to execute portfolio' 
    }, { status: 500 });
  }
}