import { createClient } from '@supabase/supabase-js';

// Supabase client configuration
const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!; // Use service key for server-side operations

// Create Supabase client for server-side operations
export const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// Database helper functions for Cedric features
export async function logActivity(
  kindeUserId: string, 
  type: 'info' | 'trade_executed' | 'proposal_created' | 'proposal_approved' | 'proposal_rejected' | 'warning',
  title: string,
  body?: string,
  meta?: any,
  alpacaAccountId?: string
) {
  const { error } = await supabase
    .from('activity_log')
    .insert([{
      kinde_user_id: kindeUserId,
      alpaca_account_id: alpacaAccountId,
      type,
      title,
      body,
      meta
    }]);

  if (error) {
    console.error('Failed to log activity:', error);
    throw error;
  }
}

export async function logOrderSubmission(
  kindeUserId: string,
  alpacaAccountId: string,
  clientOrderId: string,
  payload: any
) {
  const { error } = await supabase
    .from('order_submission_log')
    .insert([{
      kinde_user_id: kindeUserId,
      alpaca_account_id: alpacaAccountId,
      client_order_id: clientOrderId,
      payload
    }]);

  if (error) {
    console.error('Failed to log order submission:', error);
    // Don't throw - order logging is non-critical
  }
}

export async function getActivitiesByUser(kindeUserId: string, limit = 50) {
  const { data, error } = await supabase
    .from('activity_log')
    .select('*')
    .eq('kinde_user_id', kindeUserId)
    .order('ts', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('Failed to fetch activities:', error);
    throw error;
  }

  return data;
}

export async function createCedricProposal(
  kindeUserId: string,
  alpacaAccountId: string,
  rationale: string,
  plan: any,
  expiresAt?: Date
) {
  const { data, error } = await supabase
    .from('cedric_proposal')
    .insert([{
      kinde_user_id: kindeUserId,
      alpaca_account_id: alpacaAccountId,
      rationale,
      plan,
      expires_at: expiresAt?.toISOString()
    }])
    .select()
    .single();

  if (error) {
    console.error('Failed to create proposal:', error);
    throw error;
  }

  return data;
}

export async function getCedricProposalsByUser(kindeUserId: string) {
  const { data, error } = await supabase
    .from('cedric_proposal')
    .select('*')
    .eq('kinde_user_id', kindeUserId)
    .eq('status', 'pending')
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Failed to fetch proposals:', error);
    throw error;
  }

  return data;
}

export async function updateProposalStatus(
  proposalId: string,
  status: 'approved' | 'rejected' | 'expired'
) {
  const updateData: any = { status };
  
  if (status === 'approved') {
    updateData.approved_at = new Date().toISOString();
  } else if (status === 'rejected') {
    updateData.rejected_at = new Date().toISOString();
  }

  const { error } = await supabase
    .from('cedric_proposal')
    .update(updateData)
    .eq('id', proposalId);

  if (error) {
    console.error('Failed to update proposal status:', error);
    throw error;
  }
}

export async function savePortfolioSnapshot(
  kindeUserId: string,
  alpacaAccountId: string,
  totalValueCents: number,
  positions: any[],
  performanceData?: any
) {
  const { error } = await supabase
    .from('portfolio_snapshot')
    .insert([{
      kinde_user_id: kindeUserId,
      alpaca_account_id: alpacaAccountId,
      total_value_cents: totalValueCents,
      positions,
      performance_data: performanceData,
      as_of: new Date().toISOString()
    }]);

  if (error) {
    console.error('Failed to save portfolio snapshot:', error);
    throw error;
  }
}

export async function saveCedricChatMessage(
  kindeUserId: string,
  sessionId: string,
  role: 'user' | 'assistant',
  content: string,
  context?: any
) {
  const { error } = await supabase
    .from('cedric_chat')
    .insert([{
      kinde_user_id: kindeUserId,
      session_id: sessionId,
      role,
      content,
      context
    }]);

  if (error) {
    console.error('Failed to save chat message:', error);
    throw error;
  }
}