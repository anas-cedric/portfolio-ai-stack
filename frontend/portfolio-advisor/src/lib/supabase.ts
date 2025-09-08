import 'server-only';
import { createClient } from '@supabase/supabase-js';

// Supabase client configuration
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.warn('Supabase environment variables not set. Some features may not work.');
}

// Create Supabase client for server-side operations (only if env vars are available)
export const supabase = supabaseUrl && supabaseServiceKey 
  ? createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })
  : null;

// Database helper functions for Cedric features
export async function logActivity(
  kindeUserId: string, 
  type: 'info' | 'trade_executed' | 'proposal_created' | 'proposal_approved' | 'proposal_rejected' | 'warning',
  title: string,
  body?: string,
  meta?: any,
  alpacaAccountId?: string
) {
  if (!supabase) {
    console.warn('Supabase not configured, skipping activity log');
    return;
  }

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
  if (!supabase) {
    console.warn('Supabase not configured, skipping order submission log');
    return;
  }

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
  if (!supabase) {
    console.warn('Supabase not configured, returning empty activities');
    return [];
  }

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

  return data || [];
}

// --- User Onboarding State Management ---

export type OnboardingState = 'new' | 'quiz_completed' | 'portfolio_approved' | 'active';

export type UserOnboarding = {
  id: string;
  kinde_user_id: string;
  onboarding_state: OnboardingState;
  quiz_data?: any;
  portfolio_preferences?: any;
  risk_bucket?: string | null;
  risk_score?: number | null;
  created_at: string;
  updated_at: string;
};

export async function getUserOnboardingState(kindeUserId: string): Promise<UserOnboarding | null> {
  if (!supabase) {
    console.warn('Supabase not configured, returning default onboarding state');
    return {
      id: 'default',
      kinde_user_id: kindeUserId,
      onboarding_state: 'new',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }

  const { data, error } = await supabase
    .from('user_onboarding')
    .select('*')
    .eq('kinde_user_id', kindeUserId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') { // No rows returned
      return null;
    }
    console.error('Failed to get user onboarding state:', error);
    throw error;
  }

  return data;
}

/**
 * Save or update a user's risk profile into user_onboarding.
 * - Writes dedicated columns risk_bucket, risk_score (if present in schema)
 * - Mirrors into portfolio_preferences JSON for backward compatibility
 */
export async function saveRiskProfile(
  kindeUserId: string,
  riskBucket?: string | null,
  riskScore?: number | null
): Promise<UserOnboarding | void> {
  if (!supabase) {
    console.warn('Supabase not configured, skipping risk save');
    return;
  }

  // Ensure row exists
  const existing = await getUserOnboardingState(kindeUserId);
  if (!existing) {
    await createUserOnboardingState(kindeUserId, 'new');
  }

  const updateData: any = {
    updated_at: new Date().toISOString(),
  };
  if (typeof riskBucket === 'string' && riskBucket.trim()) {
    updateData.risk_bucket = riskBucket;
  }
  if (typeof riskScore === 'number' && Number.isFinite(riskScore)) {
    updateData.risk_score = riskScore;
  }

  // Merge portfolio_preferences JSON
  const mergedPrefs = {
    ...(existing?.portfolio_preferences || {}),
    ...(typeof riskBucket === 'string' ? { risk_bucket: riskBucket } : {}),
    ...(typeof riskScore === 'number' ? { risk_score: riskScore } : {}),
  };
  updateData.portfolio_preferences = mergedPrefs;

  const { data, error } = await supabase
    .from('user_onboarding')
    .update(updateData)
    .eq('kinde_user_id', kindeUserId)
    .select()
    .single();

  if (error) {
    console.error('Failed to save risk profile:', error);
    throw error;
  }

  return data;
}

export async function createUserOnboardingState(
  kindeUserId: string, 
  initialState: OnboardingState = 'new'
): Promise<UserOnboarding> {
  if (!supabase) {
    console.warn('Supabase not configured, returning mock onboarding state');
    return {
      id: 'mock',
      kinde_user_id: kindeUserId,
      onboarding_state: initialState,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }

  const { data, error } = await supabase
    .from('user_onboarding')
    .insert({
      kinde_user_id: kindeUserId,
      onboarding_state: initialState
    })
    .select()
    .single();

  if (error) {
    console.error('Failed to create user onboarding state:', error);
    throw error;
  }

  return data;
}

export async function updateUserOnboardingState(
  kindeUserId: string, 
  newState: OnboardingState, 
  additionalData?: {
    quiz_data?: any;
    portfolio_preferences?: any;
    risk_bucket?: string | null;
    risk_score?: number | null;
  }
): Promise<UserOnboarding> {
  if (!supabase) {
    console.warn('Supabase not configured, returning mock updated state');
    return {
      id: 'mock',
      kinde_user_id: kindeUserId,
      onboarding_state: newState,
      ...additionalData,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }

  const updateData: any = {
    onboarding_state: newState,
    updated_at: new Date().toISOString()
  };

  if (additionalData?.quiz_data) {
    updateData.quiz_data = additionalData.quiz_data;
  }
  if (additionalData?.portfolio_preferences) {
    updateData.portfolio_preferences = additionalData.portfolio_preferences;
  }
  if (typeof additionalData?.risk_bucket === 'string') {
    updateData.risk_bucket = additionalData.risk_bucket;
    // also mirror into JSON if present/mergeable
    updateData.portfolio_preferences = {
      ...(updateData.portfolio_preferences || {}),
      risk_bucket: additionalData.risk_bucket
    };
  }
  if (typeof additionalData?.risk_score === 'number') {
    updateData.risk_score = additionalData.risk_score;
    updateData.portfolio_preferences = {
      ...(updateData.portfolio_preferences || {}),
      risk_score: additionalData.risk_score
    };
  }

  const { data, error } = await supabase
    .from('user_onboarding')
    .update(updateData)
    .eq('kinde_user_id', kindeUserId)
    .select()
    .single();

  if (error) {
    console.error('Failed to update user onboarding state:', error);
    throw error;
  }

  return data;
}

export async function getOrCreateUserOnboardingState(kindeUserId: string): Promise<UserOnboarding> {
  let onboardingState = await getUserOnboardingState(kindeUserId);
  
  if (!onboardingState) {
    onboardingState = await createUserOnboardingState(kindeUserId);
  }

  return onboardingState;
}

export async function createCedricProposal(
  kindeUserId: string,
  alpacaAccountId: string,
  rationale: string,
  plan: any,
  expiresAt?: Date
) {
  if (!supabase) {
    console.warn('Supabase not configured, skipping proposal creation');
    return { id: 'mock-proposal', kinde_user_id: kindeUserId, alpaca_account_id: alpacaAccountId, rationale, plan, status: 'pending', created_at: new Date().toISOString() };
  }

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
  if (!supabase) {
    console.warn('Supabase not configured, returning empty proposals');
    return [];
  }

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

  return data || [];
}

export async function updateProposalStatus(
  proposalId: string,
  status: 'approved' | 'rejected' | 'expired'
) {
  if (!supabase) {
    console.warn('Supabase not configured, skipping proposal status update');
    return;
  }

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
  if (!supabase) {
    console.warn('Supabase not configured, skipping portfolio snapshot');
    return;
  }

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
  if (!supabase) {
    console.warn('Supabase not configured, skipping chat message');
    return;
  }

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