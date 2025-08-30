import axios from "axios";

const baseURL = process.env.ALPACA_BASE_URL || "https://broker-api.sandbox.alpaca.markets/v1";
const key = process.env.ALPACA_API_KEY_ID!;
const secret = process.env.ALPACA_API_SECRET!;

export const alpaca = axios.create({
  baseURL,
  timeout: 15000,
  auth: {
    username: key,
    password: secret
  },
  headers: {
    "Content-Type": "application/json"
  }
});

// --- Types ---
export type BrokerAccount = {
  id: string;
  account_number: string;
  status: string; // "APPROVED" in sandbox immediately
  currency?: string;
  buying_power?: string;
  cash?: string;
  portfolio_value?: string;
};

export type CreateAccountReq = {
  contact: {
    email_address: string;
    given_name: string;
    family_name: string;
    phone_number?: string;
    street_address?: string[];
    city?: string;
    state?: string;
    postal_code?: string;
    country?: string;
  };
  identity: {
    given_name?: string;
    family_name?: string;
    date_of_birth: string; // "1990-01-01"
    tax_id?: string;
    tax_id_type?: "USA_SSN" | "USA_EIN";
    country_of_citizenship?: string;
    country_of_tax_residence?: string;
    funding_source?: string[];
  };
  disclosures?: { 
    is_control_person?: boolean; 
    is_affiliated_exchange_or_finra?: boolean;
    is_politically_exposed?: boolean;
    immediate_family_exposed?: boolean;
  };
  agreements?: Array<{ 
    agreement: string; 
    signed_at: string; 
    ip_address: string 
  }>;
  trusted_contact?: {
    given_name: string;
    family_name: string;
    email_address?: string;
  };
};

export type JournalRequest = {
  entry_type: "JNLC" | "JNLS"; // JNLC for cash, JNLS for securities
  from_account: string;
  to_account: string;
  amount?: string; // for JNLC
  symbol?: string; // for JNLS
  qty?: string; // for JNLS
};

export type NotionalOrder = {
  symbol: string;
  side: "buy" | "sell";
  notional: number; // dollars
  time_in_force?: "day" | "gtc" | "ioc" | "fok";
  client_order_id?: string;
  type?: "market" | "limit";
  extended_hours?: boolean;
};

export type Order = {
  id: string;
  client_order_id?: string;
  created_at: string;
  symbol: string;
  notional?: string;
  qty?: string;
  side: "buy" | "sell";
  type: string;
  status: string;
  filled_qty?: string;
  filled_avg_price?: string;
};

export type Position = {
  asset_id: string;
  symbol: string;
  qty: string;
  side: "long" | "short";
  market_value: string;
  cost_basis: string;
  unrealized_pl: string;
  current_price: string;
};

// --- Account Management ---
export async function createPaperAccount(input: CreateAccountReq): Promise<BrokerAccount> {
  const { data } = await alpaca.post("/accounts", input);
  return data;
}

export async function getAccount(id: string): Promise<BrokerAccount> {
  const { data } = await alpaca.get(`/accounts/${id}`);
  return data;
}

export async function listAccounts(query?: { entities?: string[] }): Promise<BrokerAccount[]> {
  const params = query?.entities ? `?entities=${query.entities.join(',')}` : '';
  const { data } = await alpaca.get(`/accounts${params}`);
  return data;
}

// --- Funding ---
export async function createJournalUSD(fromAccountId: string, toAccountId: string, amount: number) {
  const journal: JournalRequest = {
    entry_type: "JNLC",
    from_account: fromAccountId,
    to_account: toAccountId,
    amount: amount.toFixed(2)
  };
  const { data } = await alpaca.post(`/journals`, journal);
  return data;
}

// --- Trading ---
export async function placeOrder(accountId: string, order: NotionalOrder): Promise<Order> {
  const payload = {
    symbol: order.symbol,
    side: order.side,
    type: order.type || "market",
    time_in_force: order.time_in_force || "day",
    notional: Number(order.notional.toFixed(2)),
    client_order_id: order.client_order_id,
    extended_hours: order.extended_hours || false
  };
  const { data } = await alpaca.post(`/trading/accounts/${accountId}/orders`, payload);
  return data;
}

export async function getOrders(accountId: string, status?: string): Promise<Order[]> {
  const params = status ? `?status=${status}` : '';
  const { data } = await alpaca.get(`/trading/accounts/${accountId}/orders${params}`);
  return data;
}

export async function getPositions(accountId: string): Promise<Position[]> {
  const { data } = await alpaca.get(`/trading/accounts/${accountId}/positions`);
  return data;
}

// --- Market Data (for getting current prices) ---
export async function getLatestTrades(symbols: string[]): Promise<Record<string, number>> {
  // Note: This requires Alpaca Data API subscription
  // For now, return mock prices or fetch from your price service
  const prices: Record<string, number> = {};
  
  // TODO: Replace with actual Alpaca Data API call or your price service
  // For paper trading, you could use IEX or other free data sources
  for (const symbol of symbols) {
    // Mock prices for testing
    prices[symbol] = {
      'VTI': 220.50,
      'VUG': 280.30,
      'VBR': 165.20,
      'VEA': 48.50,
      'VSS': 110.40,
      'VWO': 42.30,
      'VNQ': 88.60,
      'VNQI': 52.10,
      'BND': 75.80,
      'BNDX': 51.20,
      'VTIP': 47.90,
      'CASH': 1.00
    }[symbol] || 100.00;
  }
  
  return prices;
}

// --- Utility Functions ---
export function generateClientOrderId(userId: string, symbol: string): string {
  return `${userId}-${symbol}-${Date.now()}`;
}

export function calculateNotionalAmount(totalInvestment: number, allocationPercentage: number): number {
  return Math.round(totalInvestment * allocationPercentage) / 100; // Round to cents
}