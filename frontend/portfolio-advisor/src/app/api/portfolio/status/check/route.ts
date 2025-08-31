import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { getAccount } from "@/lib/alpacaBroker";
import { logActivity, getActivitiesByUser } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    // Get authenticated user
    const { getUser } = getKindeServerSession();
    const user = await getUser();
    
    if (!user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Get user's latest activities to find account ID
    const activities = await getActivitiesByUser(user.id, 10);
    
    // Find the most recent activity with an account ID
    const accountActivity = activities.find(activity => 
      activity.meta?.alpaca_account_id
    );
    
    if (!accountActivity?.meta?.alpaca_account_id) {
      return NextResponse.json({ 
        error: "No account found for user" 
      }, { status: 404 });
    }

    const accountId = accountActivity.meta.alpaca_account_id;
    const previousStatus = accountActivity.meta.account_status || 
                          accountActivity.meta.initial_status || 
                          'UNKNOWN';

    const checkTimestamp = new Date().toISOString();
    console.log(`[${checkTimestamp}] POLLING: Checking status for account ${accountId}, previous status: ${previousStatus}`);

    // Check current account status from Alpaca
    const account = await getAccount(accountId);
    const currentStatus = account.status;

    console.log(`[${checkTimestamp}] POLLING RESULT: Account ${accountId} status: ${previousStatus} → ${currentStatus}`);

    // If status changed, log new activity
    if (currentStatus !== previousStatus) {
      let title: string;
      let body: string;
      
      if (currentStatus === 'APPROVED') {
        title = 'Account approved and funding in progress';
        body = 'Your paper trading account has been approved. Funding is now in progress (typically takes 2-4 minutes).';
      } else if (currentStatus === 'ACTIVE') {
        title = 'Account is now active and ready for trading';
        body = 'Your account is fully funded and ready. Your portfolio will be executed automatically.';
      } else {
        title = `Account status updated to ${currentStatus}`;
        body = `Your account status has changed to ${currentStatus}.`;
      }

      await logActivity(
        user.id,
        'info',
        title,
        body,
        {
          alpaca_account_id: accountId,
          account_status: currentStatus,
          previous_status: previousStatus,
          status_updated: true,
          buying_power: account.buying_power,
          cash: account.cash,
          portfolio_value: account.portfolio_value
        },
        accountId
      );

      console.log(`[${checkTimestamp}] STATUS CHANGE: ${previousStatus} → ${currentStatus} logged to activities`);
    }

    return NextResponse.json({
      success: true,
      accountId,
      currentStatus,
      previousStatus,
      statusChanged: currentStatus !== previousStatus,
      accountDetails: {
        buying_power: account.buying_power,
        cash: account.cash,
        portfolio_value: account.portfolio_value,
        currency: account.currency
      }
    });

  } catch (error: any) {
    console.error('Account status check failed:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to check account status' 
    }, { status: 500 });
  }
}