import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { getActivitiesByUser } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: "User not found" }, { status: 401 });
    }

    // Get optional limit from query params
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');

    // Fetch activities for this user
    const activities = await getActivitiesByUser(user.id, limit);

    // Filter out internal operational events from user-facing feed
    const HIDE_TITLES = new Set([
      'Account funded successfully',
      'Account is now active and ready for trading',
      'Account approved and funding in progress',
      'Portfolio strategy saved'
    ]);

    const visibleActivities = (activities || []).filter((activity: any) => {
      if (activity?.meta?.internal === true) return false;
      if (activity?.title && HIDE_TITLES.has(activity.title)) return false;
      return true;
    });

    return NextResponse.json({
      success: true,
      activities: visibleActivities.map(activity => ({
        id: activity.id,
        type: activity.type,
        title: activity.title,
        body: activity.body,
        timestamp: activity.ts,
        // Ensure alpaca_account_id is always accessible from meta on the client
        meta: {
          ...(activity.meta || {}),
          alpaca_account_id: (activity as any).alpaca_account_id || activity?.meta?.alpaca_account_id
        }
      }))
    });

  } catch (error: any) {
    console.error('Failed to fetch activities:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to fetch activities' 
    }, { status: 500 });
  }
}