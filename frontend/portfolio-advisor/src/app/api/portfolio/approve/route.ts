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
import { logActivity, logOrderSubmission, updateUserOnboardingState } from "@/lib/supabase";

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

// Generate a unique test email for sandbox to avoid "email already exists" errors
function generateTestEmail(userId: string): string {
  // Create a hash of the user ID + current timestamp to ensure uniqueness
  const timestamp = Date.now();
  const hash = userId.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0);
  
  // Generate unique identifier
  const uniqueId = Math.abs(hash + timestamp).toString(36);
  
  // Return test email
  return `test+${uniqueId}@cedric-sandbox.com`;
}

// Note: We now store Alpaca account IDs in Supabase via activity logging
// No separate storage function needed as we log the account creation

// Get or create Alpaca account for user
async function ensureAlpacaAccount(
  userId: string, 
  email: string, 
  givenName: string, 
  familyName: string
): Promise<{ accountId: string; testEmail: string; initialStatus: string }> {
  // Check if user already has an Alpaca account (from your backend or local storage)
  // For MVP, we'll create a new account each time
  // In production, you'd check your database first
  
  try {
    // Create new paper account with generated test email to avoid conflicts
    const testEmail = generateTestEmail(userId);
    const account = await createPaperAccount({
      contact: {
        email_address: testEmail,
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

    console.log(`Account created: ${account.id}, status: ${account.status}`);
    
    return { 
      accountId: account.id, 
      testEmail,
      initialStatus: account.status 
    };
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
    const { accountId, testEmail, initialStatus } = await ensureAlpacaAccount(
      userId,
      userEmail,
      userFirstName,
      userLastName
    );

    // Log account creation activity - account is being prepared
    await logActivity(
      userId,
      'info',
      'Cedric is preparing your $10,000 simulated portfolio',
      `Your paper trading account is being set up. Account will be funded and trades executed once ready. Account ID: ${accountId}`,
      { 
        alpaca_account_id: accountId, 
        total_investment: totalInvestment,
        test_email: testEmail,
        user_email: userEmail,
        initial_status: initialStatus,
        target_weights: weights
      },
      accountId
    );

    // Store portfolio weights for later execution when account is ready
    await logActivity(
      userId,
      'info',
      'Portfolio strategy saved',
      'Your investment strategy has been saved and will be executed once your account is ready.',
      {
        weights: weights,
        total_investment: totalInvestment,
        pending_execution: true
      },
      accountId
    );

    // Update user onboarding state to portfolio_approved
    try {
      await updateUserOnboardingState(
        userId,
        'portfolio_approved',
        {
          portfolio_preferences: {
            weights: weights,
            total_investment: totalInvestment,
            approved_at: new Date().toISOString()
          }
        }
      );
      console.log(`Updated onboarding state to 'portfolio_approved' for user ${userId}`);
    } catch (error) {
      console.warn('Failed to update onboarding state:', error);
      // Don't fail the entire request if onboarding state update fails
    }

    // Return immediately - dashboard will handle the funding and execution process
    return NextResponse.json({
      success: true,
      accountId,
      initialStatus,
      message: "Account created successfully. Portfolio execution will begin once account is ready.",
      portfolio: {
        totalInvestment,
        weights
      }
    });
    
  } catch (error: any) {
    console.error('Portfolio approval error:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to execute portfolio' 
    }, { status: 500 });
  }
}