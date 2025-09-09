-- Cedric AI Features Schema Addition
-- Kinde-First Approach - No local user table needed
-- Run in Supabase SQL Editor
-- Safe to run once (idempotent guards included)

-- 1) Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2) Cedric proposal status enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cedric_proposal_status') THEN
    CREATE TYPE cedric_proposal_status AS ENUM ('pending','approved','rejected','expired');
  END IF;
END$$;

-- 3) Activity type enum for feed
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'activity_type') THEN
    CREATE TYPE activity_type AS ENUM ('info','trade_executed','proposal_created','proposal_approved','proposal_rejected','warning');
  END IF;
END$$;

-- 3.5) User onboarding state enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboarding_state') THEN
    CREATE TYPE onboarding_state AS ENUM ('new','quiz_completed','portfolio_approved','active');
  END IF;
END$$;

-- 4) Cedric proposals table (AI-generated portfolio adjustments)
CREATE TABLE IF NOT EXISTS cedric_proposal (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL,            -- Kinde user ID directly
  alpaca_account_id text,                  -- Associated Alpaca account
  created_at timestamptz DEFAULT now(),
  status cedric_proposal_status NOT NULL DEFAULT 'pending',
  rationale text NOT NULL,                 -- Human explanation from Cedric
  plan jsonb NOT NULL,                     -- { tilts: [...], rebalance: {band:0.05}, tlh: true }
  expires_at timestamptz,                  -- Optional expiration
  approved_at timestamptz,
  rejected_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_cedric_proposal_user_created ON cedric_proposal(kinde_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cedric_proposal_status ON cedric_proposal(status);

-- 5) Activity feed table (Cedric's actions and communications)
CREATE TABLE IF NOT EXISTS activity_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL,            -- Kinde user ID directly
  alpaca_account_id text,                  -- Associated Alpaca account
  ts timestamptz DEFAULT now(),
  type activity_type NOT NULL,
  title text NOT NULL,
  body text,
  meta jsonb                               -- Additional context data
);

CREATE INDEX IF NOT EXISTS idx_activity_user_ts ON activity_log(kinde_user_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_activity_type ON activity_log(type);

-- 6) Order submission audit log (track Alpaca orders)
CREATE TABLE IF NOT EXISTS order_submission_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL,            -- Kinde user ID directly
  alpaca_account_id text NOT NULL,
  client_order_id text NOT NULL,
  payload jsonb NOT NULL,                  -- Full order details and response
  created_at timestamptz DEFAULT now(),
  UNIQUE (alpaca_account_id, client_order_id)
);

CREATE INDEX IF NOT EXISTS idx_order_submission_user ON order_submission_log(kinde_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_order_submission_alpaca_account ON order_submission_log(alpaca_account_id);

-- 7) Portfolio snapshots (for dashboard performance tracking)
CREATE TABLE IF NOT EXISTS portfolio_snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL,            -- Kinde user ID directly
  alpaca_account_id text NOT NULL,
  total_value_cents bigint NOT NULL,       -- Total portfolio value in cents
  positions jsonb NOT NULL,                -- [{symbol, qty, market_value, cost_basis}]
  performance_data jsonb,                  -- {day_change, total_return, etc}
  as_of timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_user_asof ON portfolio_snapshot(kinde_user_id, as_of DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_alpaca_account ON portfolio_snapshot(alpaca_account_id, as_of DESC);

-- 8) Cedric chat history (for context and learning)
CREATE TABLE IF NOT EXISTS cedric_chat (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL,            -- Kinde user ID directly
  session_id text NOT NULL,                -- Group related messages
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,
  context jsonb,                           -- Portfolio state, market data, etc.
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cedric_chat_user_session ON cedric_chat(kinde_user_id, session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cedric_chat_created_at ON cedric_chat(created_at DESC);

-- 9) User onboarding state tracking
CREATE TABLE IF NOT EXISTS user_onboarding (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL UNIQUE,         -- Kinde user ID (one record per user)
  onboarding_state onboarding_state NOT NULL DEFAULT 'new',
  quiz_data jsonb,                             -- Store quiz responses
  portfolio_preferences jsonb,                 -- Portfolio preferences from quiz
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_onboarding_user_id ON user_onboarding(kinde_user_id);
CREATE INDEX IF NOT EXISTS idx_user_onboarding_state ON user_onboarding(onboarding_state);

-- Trigger to update updated_at on user_onboarding
CREATE OR REPLACE FUNCTION update_user_onboarding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_onboarding_updated_at
  BEFORE UPDATE ON user_onboarding
  FOR EACH ROW EXECUTE FUNCTION update_user_onboarding_updated_at();

-- 9.1) Risk fields on user_onboarding (for faster access and consistency)
ALTER TABLE user_onboarding
  ADD COLUMN IF NOT EXISTS risk_bucket text;
ALTER TABLE user_onboarding
  ADD COLUMN IF NOT EXISTS risk_score integer;

-- 10) Events table for lifecycle logging (rebalance, deposits, executions, notes)
CREATE TABLE IF NOT EXISTS events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kinde_user_id text NOT NULL,
  account_id text,
  ts timestamptz NOT NULL DEFAULT now(),
  type text NOT NULL,
  summary text NOT NULL,
  description text,
  meta_json jsonb NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_user_ts ON events(kinde_user_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_account_ts ON events(account_id, ts DESC);

-- End of Cedric schema additions