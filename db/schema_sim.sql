-- Portfolio AI Stack - Paper Trading Schema (Sim + Prices)
-- Run in Supabase SQL Editor. Safe to run once (idempotent guards included where needed).

-- 1) Enable UUID generation
create extension if not exists pgcrypto;

-- 2) Enums (created conditionally)
-- risk_bucket: used for model_weights and (optionally) risk_assessment reproducibility
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_bucket') THEN
    CREATE TYPE risk_bucket AS ENUM ('Low','Below-Avg','Moderate','Above-Avg','High');
  END IF;
END$$;

-- sim_trade_reason: reason codes for simulated trades
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sim_trade_reason') THEN
    CREATE TYPE sim_trade_reason AS ENUM ('init','rebalance','tlh','user');
  END IF;
END$$;

-- 3) Core simulation tables (no FKs to app_user for now)
-- sim_account: one per user for paper trading
CREATE TABLE IF NOT EXISTS sim_account (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  start_cash_cents bigint NOT NULL CHECK (start_cash_cents >= 0),
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sim_account_user_idx ON sim_account(user_id);

-- sim_trade: source of truth for fills
CREATE TABLE IF NOT EXISTS sim_trade (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL,
  ts timestamptz NOT NULL,
  symbol text NOT NULL,
  side text NOT NULL CHECK (side IN ('BUY','SELL')),
  qty numeric(18,6) NOT NULL CHECK (qty > 0),
  price numeric(14,6) NOT NULL CHECK (price > 0),
  reason sim_trade_reason NOT NULL,
  idempotency_key text NOT NULL,
  UNIQUE (account_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS sim_trade_account_ts_idx ON sim_trade(account_id, ts);
CREATE INDEX IF NOT EXISTS sim_trade_symbol_ts_idx ON sim_trade(symbol, ts);

-- sim_holding: materialized current positions (derivable from sim_trade)
CREATE TABLE IF NOT EXISTS sim_holding (
  account_id uuid NOT NULL,
  symbol text NOT NULL,
  qty numeric(18,6) NOT NULL,
  avg_price numeric(14,6) NOT NULL,
  updated_at timestamptz DEFAULT now(),
  PRIMARY KEY (account_id, symbol)
);

-- sim_cash: account cash
CREATE TABLE IF NOT EXISTS sim_cash (
  account_id uuid PRIMARY KEY,
  cents bigint NOT NULL,
  updated_at timestamptz DEFAULT now()
);

-- Optional cache of derived positions
CREATE TABLE IF NOT EXISTS sim_position_snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL,
  positions jsonb NOT NULL,
  as_of timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sim_position_snapshot_account_asof
  ON sim_position_snapshot(account_id, as_of DESC);

-- 4) Model weights (for reproducibility of targets)
CREATE TABLE IF NOT EXISTS model_weights (
  model_version text NOT NULL,
  bucket risk_bucket NOT NULL,
  symbol text NOT NULL,
  weight numeric(8,6) NOT NULL CHECK (weight >= 0),
  PRIMARY KEY (model_version, bucket, symbol)
);

-- 5) Market data (EOD)
CREATE TABLE IF NOT EXISTS mkt_price (
  symbol text NOT NULL,
  date date NOT NULL,
  close numeric(14,6) NOT NULL CHECK (close > 0),
  PRIMARY KEY (symbol, date)
);
CREATE INDEX IF NOT EXISTS mkt_price_symbol_date_idx ON mkt_price(symbol, date);

CREATE TABLE IF NOT EXISTS benchmark_price (
  name text NOT NULL,            -- e.g., 'SPY','60_40'
  date date NOT NULL,
  close numeric(14,6) NOT NULL,
  PRIMARY KEY (name, date)
);
CREATE INDEX IF NOT EXISTS benchmark_price_name_date_idx ON benchmark_price(name, date);

-- 6) Explanations (optional logging of LLM outputs)
CREATE TABLE IF NOT EXISTS explanation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  account_id uuid,
  ts timestamptz DEFAULT now(),
  topic text NOT NULL,           -- 'why_portfolio','what_changed', etc.
  prompt text NOT NULL,
  response text NOT NULL,
  model_version text NOT NULL
);
CREATE INDEX IF NOT EXISTS explanation_user_ts_idx ON explanation(user_id, ts DESC);

-- 7) Integrations with existing MVP tables
-- Add model_version to risk_assessment for reproducibility (safe default)
ALTER TABLE IF EXISTS risk_assessment
  ADD COLUMN IF NOT EXISTS model_version text DEFAULT 'v1';

-- Helpful indexes for existing tables used by current endpoints
CREATE INDEX IF NOT EXISTS risk_assessment_user_created
  ON risk_assessment(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS portfolio_proposal_user_status
  ON portfolio_proposal(user_id, status);
CREATE INDEX IF NOT EXISTS trade_intent_account_created
  ON trade_intent(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS transfer_user_created
  ON transfer(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS brokerage_account_user
  ON brokerage_account(user_id);

-- End of schema_sim.sql
