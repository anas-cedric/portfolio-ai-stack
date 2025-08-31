import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { updateProposalStatus, logActivity } from "@/lib/supabase";
import { supabase } from "@/lib/supabase";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: "User not found" }, { status: 401 });
    }

    const proposalId = params.id;

    // First, fetch the proposal to verify ownership and get details
    const { data: proposal, error: fetchError } = await supabase
      .from('cedric_proposal')
      .select('*')
      .eq('id', proposalId)
      .eq('kinde_user_id', user.id)
      .eq('status', 'pending')
      .single();

    if (fetchError || !proposal) {
      return NextResponse.json({ 
        error: "Proposal not found or not pending" 
      }, { status: 404 });
    }

    // Update proposal status to rejected
    await updateProposalStatus(proposalId, 'rejected');

    // Log the rejection activity
    await logActivity(
      user.id,
      'proposal_rejected',
      'You rejected Cedric\'s proposal',
      'No changes were made to your portfolio.',
      { 
        proposal_id: proposalId, 
        plan: proposal.plan,
        rationale: proposal.rationale
      },
      proposal.alpaca_account_id
    );

    return NextResponse.json({
      success: true,
      message: "Proposal rejected successfully"
    });

  } catch (error: any) {
    console.error('Failed to reject proposal:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to reject proposal' 
    }, { status: 500 });
  }
}