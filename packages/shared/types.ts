/**
 * Shared TypeScript types for wealth management app
 */

export type RiskBucket = 'Low' | 'Below-Avg' | 'Moderate' | 'Above-Avg' | 'High';

export type AccountStatus = 'pending' | 'active' | 'suspended' | 'closed';

export type TransferDirection = 'deposit' | 'withdrawal';

export type TransferStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type OrderSide = 'buy' | 'sell';

export type OrderStatus = 'staged' | 'submitted' | 'filled' | 'cancelled';

export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface RiskAssessment {
  id: string;
  user_id: string;
  method: string;
  raw_answers: Record<string, any>;
  score: number;
  bucket: RiskBucket;
  created_at: string;
}

export interface GlidePath {
  id: string;
  bucket: RiskBucket;
  age_from: number;
  age_to: number;
  equity_pct: number;
  intl_equity_pct: number;
  bond_pct: number;
  tips_pct: number;
  cash_pct: number;
}

export interface PortfolioProposal {
  id: string;
  user_id: string;
  model_id?: string;
  rationale: string;
  targets: Record<string, number>; // symbol -> weight percentage
  status: 'awaiting_user' | 'approved' | 'rejected';
  created_at: string;
  approved_at?: string;
}

export interface BrokerageAccount {
  id: string;
  user_id: string;
  provider: string;
  external_account_id?: string;
  status: AccountStatus;
  base_currency: string;
  created_at: string;
  updated_at: string;
}

export interface Transfer {
  id: string;
  user_id: string;
  account_id: string;
  direction: TransferDirection;
  amount_cents: number;
  status: TransferStatus;
  provider_ref?: string;
  created_at: string;
}

export interface TradeIntentItem {
  symbol: string;
  side: OrderSide;
  qty?: number;
  notional?: number;
  current_weight?: number;
  target_weight?: number;
}

export interface TradeIntent {
  id: string;
  user_id: string;
  account_id: string;
  proposal_id?: string;
  items: TradeIntentItem[];
  status: OrderStatus;
  provider_order_ids?: Record<string, string>;
  created_at: string;
  submitted_at?: string;
  filled_at?: string;
}

export interface Position {
  symbol: string;
  qty: number;
  market_value: number;
  cost_basis: number;
  unrealized_pl?: number;
  unrealized_plpc?: number;
  current_price: number;
}

export interface PositionSnapshot {
  id: string;
  account_id: string;
  as_of: string;
  positions: Position[];
}

export interface Agreement {
  id: string;
  kind: string;
  version: string;
  url?: string;
  effective_at: string;
}

export interface AuditLogEntry {
  id: string;
  user_id?: string;
  actor: string;
  action: string;
  context?: Record<string, any>;
  created_at: string;
}

export interface RebalanceCheck {
  needs_rebalance: boolean;
  reason?: string;
  max_drift?: number;
  trades?: TradeIntentItem[];
  rationale?: string;
  trade_intent_id?: string;
  next_eligible?: string;
}

export interface AccountSummary {
  id: string;
  status: string;
  buying_power: number;
  cash: number;
  portfolio_value: number;
  pattern_day_trader: boolean;
  trading_blocked: boolean;
  transfers_blocked: boolean;
  account_blocked: boolean;
}