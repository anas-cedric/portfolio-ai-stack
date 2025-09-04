import { NextRequest, NextResponse } from "next/server";
import { getKindeServerSession } from "@kinde-oss/kinde-auth-nextjs/server";
import { createCedricProposal, getCedricProposalsByUser, logActivity } from "@/lib/supabase";

// GET - Fetch user's pending proposals
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

    const proposals = await getCedricProposalsByUser(user.id);

    return NextResponse.json({
      success: true,
      proposals: proposals.map(proposal => ({
        id: proposal.id,
        alpacaAccountId: proposal.alpaca_account_id,
        rationale: proposal.rationale,
        plan: proposal.plan,
        status: proposal.status,
        createdAt: proposal.created_at,
        expiresAt: proposal.expires_at
      }))
    });

  } catch (error: any) {
    console.error('Failed to fetch proposals:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to fetch proposals' 
    }, { status: 500 });
  }
}

// POST - Create a new Cedric proposal (for testing/demo purposes)
export async function POST(request: NextRequest) {
  try {
    const { getUser, isAuthenticated } = getKindeServerSession();
    
    if (!(await isAuthenticated())) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await getUser();
    if (!user?.id) {
      return NextResponse.json({ error: "User not found" }, { status: 401 });
    }

    const { rationale, plan, alpacaAccountId, expiresAt } = await request.json();

    if (!rationale || !plan || !alpacaAccountId) {
      return NextResponse.json({ 
        error: "Missing required fields: rationale, plan, alpacaAccountId" 
      }, { status: 400 });
    }

    // Create the proposal
    const proposal = await createCedricProposal(
      user.id,
      alpacaAccountId,
      rationale,
      plan,
      expiresAt ? new Date(expiresAt) : undefined
    );

    // Log the proposal creation activity
    await logActivity(
      user.id,
      'proposal_created',
      'Cedric has a new proposal for your portfolio',
      rationale,
      { proposal_id: proposal.id, plan },
      alpacaAccountId
    );

    return NextResponse.json({
      success: true,
      proposal: {
        id: proposal.id,
        rationale: proposal.rationale,
        plan: proposal.plan,
        status: proposal.status,
        createdAt: proposal.created_at
      }
    });

  } catch (error: any) {
    console.error('Failed to create proposal:', error);
    return NextResponse.json({ 
      error: error.message || 'Failed to create proposal' 
    }, { status: 500 });
  }
}