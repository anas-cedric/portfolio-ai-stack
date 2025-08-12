-- Initial database schema for AI-assisted wealth app
-- Created: 2025

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User management
CREATE TABLE app_user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_app_user_email ON app_user(email);

-- Risk assessment results
CREATE TABLE risk_assessment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    method VARCHAR(50) NOT NULL, -- 'grable_lytton', 'custom', etc
    raw_answers JSONB NOT NULL,
    score INTEGER NOT NULL,
    bucket VARCHAR(20) NOT NULL CHECK (bucket IN ('Low', 'Below-Avg', 'Moderate', 'Above-Avg', 'High')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_risk_assessment_user_id ON risk_assessment(user_id);
CREATE INDEX idx_risk_assessment_created_at ON risk_assessment(created_at DESC);

-- Model glide paths for different risk buckets and age ranges
CREATE TABLE model_glidepath (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bucket VARCHAR(20) NOT NULL CHECK (bucket IN ('Low', 'Below-Avg', 'Moderate', 'Above-Avg', 'High')),
    age_from INTEGER NOT NULL,
    age_to INTEGER NOT NULL,
    equity_pct DECIMAL(5,2) NOT NULL CHECK (equity_pct >= 0 AND equity_pct <= 100),
    intl_equity_pct DECIMAL(5,2) NOT NULL CHECK (intl_equity_pct >= 0 AND intl_equity_pct <= 100),
    bond_pct DECIMAL(5,2) NOT NULL CHECK (bond_pct >= 0 AND bond_pct <= 100),
    tips_pct DECIMAL(5,2) NOT NULL CHECK (tips_pct >= 0 AND tips_pct <= 100),
    cash_pct DECIMAL(5,2) NOT NULL CHECK (cash_pct >= 0 AND cash_pct <= 100),
    CONSTRAINT sum_to_100 CHECK (equity_pct + bond_pct + tips_pct + cash_pct = 100),
    CONSTRAINT valid_age_range CHECK (age_from < age_to)
);

CREATE INDEX idx_model_glidepath_bucket_age ON model_glidepath(bucket, age_from, age_to);

-- Model portfolios
CREATE TABLE model_portfolio (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    bucket VARCHAR(20) NOT NULL CHECK (bucket IN ('Low', 'Below-Avg', 'Moderate', 'Above-Avg', 'High')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_model_portfolio_bucket ON model_portfolio(bucket);

-- Model portfolio holdings
CREATE TABLE model_holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES model_portfolio(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    target_weight DECIMAL(5,2) NOT NULL CHECK (target_weight > 0 AND target_weight <= 100)
);

CREATE INDEX idx_model_holdings_model_id ON model_holdings(model_id);

-- Agreement tracking
CREATE TABLE agreement_version (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kind VARCHAR(50) NOT NULL, -- 'terms', 'privacy', 'advisory', etc
    version VARCHAR(20) NOT NULL,
    url TEXT,
    effective_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_agreement_version_kind_effective ON agreement_version(kind, effective_at DESC);

-- User agreement acceptances
CREATE TABLE agreement_acceptance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    agreement_id UUID NOT NULL REFERENCES agreement_version(id),
    accepted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip INET,
    user_agent TEXT
);

CREATE INDEX idx_agreement_acceptance_user_id ON agreement_acceptance(user_id);
CREATE INDEX idx_agreement_acceptance_agreement_id ON agreement_acceptance(agreement_id);

-- KYC applications
CREATE TABLE kyc_application (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'alpaca', 'atomic', etc
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected', etc
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_kyc_application_user_id ON kyc_application(user_id);
CREATE INDEX idx_kyc_application_status ON kyc_application(status);

-- Brokerage accounts
CREATE TABLE brokerage_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    external_account_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'closed'
    base_currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_brokerage_account_user_id ON brokerage_account(user_id);
CREATE INDEX idx_brokerage_account_external_id ON brokerage_account(external_account_id);
CREATE INDEX idx_brokerage_account_status ON brokerage_account(status);

-- Funding sources (bank accounts)
CREATE TABLE funding_source (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'verified', 'disabled'
    mask VARCHAR(10), -- last 4 digits
    bank_name VARCHAR(255)
);

CREATE INDEX idx_funding_source_user_id ON funding_source(user_id);
CREATE INDEX idx_funding_source_external_id ON funding_source(external_id);

-- Money transfers
CREATE TABLE transfer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES brokerage_account(id),
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('deposit', 'withdrawal')),
    amount_cents BIGINT NOT NULL CHECK (amount_cents > 0),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    provider_ref VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transfer_user_id ON transfer(user_id);
CREATE INDEX idx_transfer_account_id ON transfer(account_id);
CREATE INDEX idx_transfer_status ON transfer(status);
CREATE INDEX idx_transfer_created_at ON transfer(created_at DESC);

-- Portfolio proposals
CREATE TABLE portfolio_proposal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    model_id UUID REFERENCES model_portfolio(id),
    rationale TEXT,
    targets JSONB NOT NULL, -- {symbol: weight} mapping
    status VARCHAR(50) NOT NULL DEFAULT 'awaiting_user', -- 'awaiting_user', 'approved', 'rejected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_portfolio_proposal_user_id ON portfolio_proposal(user_id);
CREATE INDEX idx_portfolio_proposal_status ON portfolio_proposal(status);
CREATE INDEX idx_portfolio_proposal_created_at ON portfolio_proposal(created_at DESC);

-- Trade intents (orders to be placed)
CREATE TABLE trade_intent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES brokerage_account(id),
    proposal_id UUID REFERENCES portfolio_proposal(id),
    items JSONB NOT NULL, -- [{symbol, side, qty, notional}]
    status VARCHAR(50) NOT NULL DEFAULT 'staged', -- 'staged', 'submitted', 'filled', 'cancelled'
    provider_order_ids JSONB, -- {symbol: order_id} mapping
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    filled_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_trade_intent_user_id ON trade_intent(user_id);
CREATE INDEX idx_trade_intent_account_id ON trade_intent(account_id);
CREATE INDEX idx_trade_intent_status ON trade_intent(status);
CREATE INDEX idx_trade_intent_created_at ON trade_intent(created_at DESC);

-- Position snapshots
CREATE TABLE position_snapshot (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES brokerage_account(id),
    as_of TIMESTAMP WITH TIME ZONE NOT NULL,
    positions JSONB NOT NULL -- [{symbol, qty, market_value, cost_basis}]
);

CREATE INDEX idx_position_snapshot_account_id ON position_snapshot(account_id);
CREATE INDEX idx_position_snapshot_as_of ON position_snapshot(as_of DESC);

-- Audit log for all actions
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
    actor VARCHAR(255), -- system, user email, admin email
    action VARCHAR(100) NOT NULL, -- 'portfolio.approved', 'order.submitted', etc
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers
CREATE TRIGGER update_kyc_application_updated_at BEFORE UPDATE ON kyc_application
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brokerage_account_updated_at BEFORE UPDATE ON brokerage_account
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();