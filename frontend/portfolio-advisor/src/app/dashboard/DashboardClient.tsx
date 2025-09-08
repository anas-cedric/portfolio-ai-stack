"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, MessageCircle, TrendingUp, DollarSign, Clock, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import PortfolioDonutChart from '@/components/PortfolioDonutChart';
import ExplainabilityChat from '@/components/ExplainabilityChat';
import { useUserProfile } from '@/contexts/UserContext';
 

type Activity = {
  id: string;
  type: 'info' | 'trade_executed' | 'proposal_created' | 'proposal_approved' | 'proposal_rejected' | 'warning';
  title: string;
  body?: string;
  timestamp: string;
  meta?: any;
};

type AccountStatus = 'SUBMITTED' | 'APPROVED' | 'ACTIVE' | 'ACCOUNT_UPDATED';

type PortfolioState = {
  status: AccountStatus;
  accountId?: string;
  totalInvestment: number;
  weights?: Array<{ symbol: string; weight: number }>;
  hasExecutedTrades?: boolean;
};

type Proposal = {
  id: string;
  rationale: string;
  plan: any;
  status: string;
  createdAt: string;
  expiresAt?: string;
  alpacaAccountId?: string;
};

type Holding = {
  symbol: string;
  qty: number;
  market_value: number;
  percent: number;
};

type HoldingsResponse = {
  accountId: string;
  cash: number;
  portfolio_value: number;
  positions: Holding[];
  cash_percent: number;
  as_of: string;
};

type OrdersResponse = {
  accountId: string;
  open_count: number;
  open_orders: Array<{
    id: string;
    client_order_id?: string;
    symbol: string;
    notional?: string;
    qty?: string;
    side: string;
    type: string;
    status: string;
    created_at: string;
  }>;
  as_of: string;
};

const ActivityIcon = ({ type }: { type: Activity['type'] }) => {
  const iconClass = "w-4 h-4";
  
  switch (type) {
    case 'info':
      return <MessageCircle className={iconClass} />;
    case 'trade_executed':
      return <TrendingUp className={iconClass} />;
    case 'proposal_created':
      return <MessageCircle className={iconClass} />;
    case 'proposal_approved':
      return <TrendingUp className={iconClass + " text-green-600"} />;
    case 'proposal_rejected':
      return <MessageCircle className={iconClass + " text-red-600"} />;
    case 'warning':
      return <MessageCircle className={iconClass + " text-yellow-600"} />;
    default:
      return <MessageCircle className={iconClass} />;
  }
};

function DashboardContent() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useKindeBrowserClient();
  const { profile, updateProfile } = useUserProfile();
  const [riskProfileStr, setRiskProfileStr] = useState<string | undefined>(profile?.riskProfile);
  useEffect(() => {
    setRiskProfileStr(profile?.riskProfile);
  }, [profile?.riskProfile]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [portfolioState, setPortfolioState] = useState<PortfolioState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [holdings, setHoldings] = useState<HoldingsResponse | null>(null);
  const [isHoldingsLoading, setIsHoldingsLoading] = useState(false);
  const [orders, setOrders] = useState<OrdersResponse | null>(null);
  const [isOrdersLoading, setIsOrdersLoading] = useState(false);
  const eventSrcRef = useRef<EventSource | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastEventIdRef = useRef<string | null>(null);
  const lastEventULIDRef = useRef<string | null>(null);
  const lastMessageAtRef = useRef<number>(Date.now());
  const healthTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isManuallyClosedRef = useRef(false);
  const prevAccountIdRef = useRef<string | null>(null);
  const supabaseRiskLoadedRef = useRef(false);

  // Authentication is handled by server wrapper + middleware; this page assumes an authenticated + authorized user

  // Fetch data when user is available
  useEffect(() => {
    if (user?.id) {
      // Fetch risk bucket from Supabase onboarding and hydrate context immediately
      (async () => {
        try {
          const resp = await fetch('/api/onboarding/me', { credentials: 'include' });
          if (resp.ok) {
            const data = await resp.json();
            const rb = typeof data?.risk_bucket === 'string' ? data.risk_bucket : undefined;
            const rs = typeof data?.risk_score === 'number' ? data.risk_score : undefined;
            if (rb && rb !== 'unknown') {
              if (rb !== riskProfileStr) setRiskProfileStr(rb);
              updateProfile({ riskProfile: rb });
            }
            supabaseRiskLoadedRef.current = true;
            // If later you decide to store riskScore in context, you can update it here too
          }
        } catch (e) {
          console.warn('Failed to fetch onboarding risk info:', e);
        }
      })();

      fetchDashboardData();
    }
  }, [user]);

  // Open SSE stream for account status updates with auto-reconnect and since-token resumption
  useEffect(() => {
    if (!portfolioState?.accountId) return;

    // Reset since tokens when switching accounts
    if (prevAccountIdRef.current !== portfolioState.accountId) {
      lastEventIdRef.current = null;
      lastEventULIDRef.current = null;
      prevAccountIdRef.current = portfolioState.accountId;
    }

    // Helpers
    const cleanupEventSourceOnly = () => {
      if (eventSrcRef.current) {
        try { eventSrcRef.current.close(); } catch {}
        eventSrcRef.current = null;
      }
    };

    const cleanupAll = () => {
      isManuallyClosedRef.current = true;
      cleanupEventSourceOnly();
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (healthTimerRef.current) {
        clearInterval(healthTimerRef.current);
        healthTimerRef.current = null;
      }
    };

    const buildUrl = () => {
      const params = new URLSearchParams({ accountId: portfolioState.accountId! });
      if (lastEventULIDRef.current) {
        params.set('since_ulid', lastEventULIDRef.current);
      } else if (lastEventIdRef.current) {
        params.set('since_id', lastEventIdRef.current);
      }
      return `/api/alpaca/accounts/status/sse?${params.toString()}`;
    };

    const scheduleReconnect = () => {
      if (isManuallyClosedRef.current) return;
      const attempt = (reconnectAttemptRef.current = reconnectAttemptRef.current + 1);
      const backoff = Math.min(30000, 1000 * Math.pow(2, attempt - 1));
      const jitter = Math.floor(Math.random() * 250);
      const delay = backoff + jitter;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, delay);
      console.warn(`SSE reconnect scheduled in ${delay}ms (attempt ${attempt})`);
    };

    const connect = () => {
      isManuallyClosedRef.current = false;
      const url = buildUrl();

      // Close any existing connection before opening a new one
      cleanupEventSourceOnly();

      const es = new EventSource(url);
      eventSrcRef.current = es;

      es.onopen = () => {
        reconnectAttemptRef.current = 0;
        lastMessageAtRef.current = Date.now();
        console.log('SSE connected for account', portfolioState.accountId);
      };

      es.onmessage = async (evt) => {
        lastMessageAtRef.current = Date.now();

        // Track last event identifiers for since-token reconnects
        if (evt.lastEventId) {
          lastEventIdRef.current = evt.lastEventId;
        }

        try {
          const payload = JSON.parse(evt.data);
          if (payload?.ulid && typeof payload.ulid === 'string') {
            lastEventULIDRef.current = payload.ulid;
          } else if (payload?.id && typeof payload.id === 'string') {
            lastEventIdRef.current = payload.id;
          }
          console.log('SSE account event:', payload);
        } catch {
          // heartbeat or non-JSON payloads
        }

        try {
          const res = await fetch('/api/portfolio/status/check', { method: 'POST', credentials: 'include' });
          if (res.ok) {
            await res.json();
          }
        } catch (e) {
          console.warn('Status reconcile failed:', e);
        }

        await fetchDashboardData();
      };

      // Heartbeats or explicit ping events advance health tracking
      es.addEventListener('ping', () => {
        lastMessageAtRef.current = Date.now();
      });

      es.onerror = (err) => {
        console.warn('SSE error:', err);
        cleanupEventSourceOnly();
        scheduleReconnect();
      };
    };

    // Start connection
    connect();

    // Health monitor: restart if no messages for 60s
    healthTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - lastMessageAtRef.current;
      if (elapsed > 60000 && !isManuallyClosedRef.current) {
        console.warn('SSE health check timeout; restarting connection');
        cleanupEventSourceOnly();
        scheduleReconnect();
      }
    }, 15000);

    return () => {
      cleanupAll();
    };
  }, [portfolioState?.accountId]);

  // Removed 15s polling; SSE will drive updates

  const fetchHoldings = async (accountId: string) => {
    try {
      setIsHoldingsLoading(true);
      const res = await fetch('/api/portfolio/holdings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId }),
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setHoldings(data);
      }
    } catch (e) {
      console.warn('Failed to fetch holdings:', e);
    } finally {
      setIsHoldingsLoading(false);
    }
  };

  const fetchOrders = async (accountId: string) => {
    try {
      setIsOrdersLoading(true);
      const res = await fetch('/api/portfolio/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId }),
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setOrders(data);
      }
    } catch (e) {
      console.warn('Failed to fetch orders:', e);
    } finally {
      setIsOrdersLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch activities, proposals, and live status in parallel
      const [activitiesRes, proposalsRes, statusRes] = await Promise.all([
        fetch('/api/activity', { credentials: 'include' }),
        fetch('/api/cedric/proposals', { credentials: 'include' }),
        fetch('/api/portfolio/status/check', { method: 'POST', credentials: 'include' })
      ]);

      if (!activitiesRes.ok || !proposalsRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const activitiesData = await activitiesRes.json();
      const proposalsData = await proposalsRes.json();
      let statusData: any = null;
      try {
        statusData = statusRes.ok ? await statusRes.json() : null;
      } catch {}

      setActivities(activitiesData.activities || []);
      setProposals(proposalsData.proposals || []);

      // Derive risk profile from latest known sources only if Supabase onboarding isn't available
      if (!supabaseRiskLoadedRef.current) {
        try {
          let derivedRisk: string | undefined = undefined;
          const actsArr: Activity[] = Array.isArray(activitiesData.activities) ? activitiesData.activities : [];
          for (const a of actsArr) {
            const m = (a as any)?.meta || {};
            const cand = m.risk_bucket || m.risk_profile || m.derived_risk_level || m.risk_tolerance;
            if (typeof cand === 'string' && cand.trim()) { derivedRisk = cand.trim(); break; }
          }
          const firstProposal: any = Array.isArray(proposalsData?.proposals) && proposalsData.proposals.length > 0 ? proposalsData.proposals[0] : null;
          const proposalRisk = firstProposal?.risk_bucket || firstProposal?.plan?.risk_bucket || firstProposal?.plan?.preferences?.risk_bucket;
          if (!derivedRisk && typeof proposalRisk === 'string' && proposalRisk.trim()) {
            derivedRisk = proposalRisk.trim();
          }
          if ((!riskProfileStr || riskProfileStr === 'unknown') && derivedRisk && derivedRisk !== riskProfileStr) {
            setRiskProfileStr(derivedRisk);
            // Persist to user profile for reuse across pages
            updateProfile({ riskProfile: derivedRisk });
          }
        } catch (e) {
          // Non-fatal: risk derivation is best-effort
        }
      }

      // Extract portfolio state from latest activities
      const latestActivity = activitiesData.activities?.[0];
      if (latestActivity?.meta) {
        const meta = latestActivity.meta;
        let nextState: PortfolioState = {
          status: meta.account_status || meta.initial_status || 'SUBMITTED',
          accountId: meta.alpaca_account_id,
          totalInvestment: meta.total_investment || 10000,
          weights: meta.target_weights || meta.weights,
          hasExecutedTrades: meta.trades_executed || false
        };

        // Override with live status info when available
        if (statusData?.currentStatus) {
          nextState.status = statusData.currentStatus as AccountStatus;
        }
        if (statusData?.accountId && !nextState.accountId) {
          nextState.accountId = statusData.accountId as string;
        }

        // Fallbacks: scan activities for missing fields, then previous state, then proposals for weights
        const acts: Activity[] = activitiesData.activities || [];

        // Account ID fallback from any recent activity, or previous state, then proposals
        if (!nextState.accountId) {
          for (const a of acts) {
            if (a?.meta?.alpaca_account_id) {
              nextState.accountId = a.meta.alpaca_account_id;
              break;
            }
          }
          if (!nextState.accountId && portfolioState?.accountId) {
            nextState.accountId = portfolioState.accountId;
          }
          if (!nextState.accountId) {
            const proposalAcct = proposalsData?.proposals?.find((p: any) => p?.alpacaAccountId)?.alpacaAccountId;
            if (proposalAcct) nextState.accountId = proposalAcct;
          }
        }

        // Weights fallback from activities -> previous state -> proposals
        if (!nextState.weights || nextState.weights.length === 0) {
          let weightsFromActivities: any[] | undefined;
          for (const a of acts) {
            const w = a?.meta?.target_weights || a?.meta?.weights;
            if (Array.isArray(w) && w.length > 0) { weightsFromActivities = w; break; }
          }

          let weightsFromProposals: any[] | undefined;
          const plan = proposalsData?.proposals?.[0]?.plan;
          if (!weightsFromActivities && plan) {
            if (Array.isArray(plan?.weights) && plan.weights.length > 0) {
              weightsFromProposals = plan.weights;
            } else if (Array.isArray(plan?.target_weights) && plan.target_weights.length > 0) {
              weightsFromProposals = plan.target_weights;
            } else if (plan?.weights && typeof plan.weights === 'object') {
              const entries = Object.entries(plan.weights).map(([symbol, weight]) => ({ symbol, weight }));
              if (entries.length > 0) weightsFromProposals = entries as any[];
            } else if (plan?.target_allocation && typeof plan.target_allocation === 'object') {
              const entries = Object.entries(plan.target_allocation).map(([symbol, weight]) => ({ symbol, weight }));
              if (entries.length > 0) weightsFromProposals = entries as any[];
            }
          }

        
          nextState.weights = (weightsFromActivities || portfolioState?.weights || weightsFromProposals) as Array<{ symbol: string; weight: number }> | undefined;
        }

        // totalInvestment fallback from activities -> previous state
        if (!nextState.totalInvestment || nextState.totalInvestment === 10000) {
          for (const a of acts) {
            if (typeof a?.meta?.total_investment === 'number') {
              nextState.totalInvestment = a.meta.total_investment;
              break;
            }
          }
          if (!nextState.totalInvestment && portfolioState?.totalInvestment) {
            nextState.totalInvestment = portfolioState.totalInvestment;
          }
        }

        // hasExecutedTrades fallback from any activity or previous state
        if (!nextState.hasExecutedTrades) {
          const executedInActivities = acts.some(a => a.type === 'trade_executed' || a?.meta?.trades_executed === true);
          nextState.hasExecutedTrades = executedInActivities || !!portfolioState?.hasExecutedTrades || false;
        }

        setPortfolioState(nextState);

        // If account is ACTIVE and trades not executed yet, trigger execution
        if (nextState.status === 'ACTIVE' && !nextState.hasExecutedTrades && nextState.accountId && nextState.weights && nextState.weights.length > 0) {
          await executePortfolioTrades(nextState);
        }
        // If trades have executed, fetch holdings summary and any open orders
        if (nextState.hasExecutedTrades && nextState.accountId) {
          await fetchHoldings(nextState.accountId);
          await fetchOrders(nextState.accountId);
        }
      } else {
        // No latest meta - attempt to derive minimal state from proposals/previous state
        const plan = proposalsData?.proposals?.[0]?.plan;
        let weightsFromProposals: any[] | undefined;
        if (plan) {
          if (Array.isArray(plan?.weights) && plan.weights.length > 0) {
            weightsFromProposals = plan.weights;
          } else if (Array.isArray(plan?.target_weights) && plan.target_weights.length > 0) {
            weightsFromProposals = plan.target_weights;
          } else if (plan?.weights && typeof plan.weights === 'object') {
            const entries = Object.entries(plan.weights).map(([symbol, weight]) => ({ symbol, weight }));
            if (entries.length > 0) weightsFromProposals = entries as any[];
          } else if (plan?.target_allocation && typeof plan.target_allocation === 'object') {
            const entries = Object.entries(plan.target_allocation).map(([symbol, weight]) => ({ symbol, weight }));
            if (entries.length > 0) weightsFromProposals = entries as any[];
          }
        }

        const proposalAcct = proposalsData?.proposals?.find((p: any) => p?.alpacaAccountId)?.alpacaAccountId;
        const derivedState: PortfolioState = {
          status: 'SUBMITTED',
          accountId: proposalAcct || portfolioState?.accountId,
          totalInvestment: portfolioState?.totalInvestment || 10000,
          weights: (portfolioState?.weights || weightsFromProposals) as Array<{ symbol: string; weight: number }> | undefined,
          hasExecutedTrades: portfolioState?.hasExecutedTrades || false
        };

        // Override with live status info when available
        if (statusData?.currentStatus) {
          derivedState.status = statusData.currentStatus as AccountStatus;
        }
        if (statusData?.accountId && !derivedState.accountId) {
          derivedState.accountId = statusData.accountId as string;
        }

        setPortfolioState(derivedState);
      }

      // If no activities, show default setup state
      if (
        activitiesData.activities &&
        activitiesData.activities.length === 0 &&
        (!proposalsData.proposals || proposalsData.proposals.length === 0)
      ) {
        console.log('No activities found, showing default setup state');
        setPortfolioState({
          status: 'SUBMITTED',
          totalInvestment: 10000,
          hasExecutedTrades: false
        });
      }

      // No-op: execution decision handled above using fresh nextState

    } catch (error: any) {
      console.error('Failed to fetch dashboard data:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProposalAction = async (proposalId: string, action: 'approve' | 'reject') => {
    try {
      const response = await fetch(`/api/cedric/proposals/${proposalId}/${action}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to ${action} proposal`);
      }

      // Refresh data after action
      await fetchDashboardData();

    } catch (error: any) {
      console.error(`Failed to ${action} proposal:`, error);
      setError(error.message);
    }
  };

  const executePortfolioTrades = async (stateOverride?: PortfolioState) => {
    const s = stateOverride ?? portfolioState;
    if (!s?.accountId) {
      console.warn('Cannot execute trades: missing account ID');
      return;
    }
    if (!Array.isArray(s?.weights) || s.weights.length === 0) {
      console.warn('Cannot execute trades: missing or empty weights');
      return;
    }

    try {
      const response = await fetch('/api/portfolio/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          accountId: s.accountId,
          weights: s.weights,
          totalInvestment: s.totalInvestment
        })
      });

      if (response.ok) {
        // Refresh to show executed trades
        await fetchDashboardData();
        if (s.accountId) {
          await fetchHoldings(s.accountId);
          await fetchOrders(s.accountId);
        }
      }
    } catch (error) {
      console.error('Failed to execute portfolio trades:', error);
    }
  };

  // Show loading while checking auth
  if (isAuthLoading || isLoading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-[#E6EFF3]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-700">Loading your portfolio dashboard...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated
  if (!user) {
    return null;
  }

  return (
    <div className="w-full h-screen bg-[#E6EFF3] flex overflow-hidden">
      {/* Left section - Activity feed and chat */}
      <div className="flex-1 flex flex-col h-full">
        <div className="flex-1 overflow-y-auto p-8">
          <div className="w-full max-w-[800px] mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-4">
                <Image 
                  src="/images/cedric-logo-new.png" 
                  alt="Cedric" 
                  width={60} 
                  height={60}
                />
                <div>
                  <h1 className="text-2xl font-bold text-[#00121F]">
                    Welcome back, {user.given_name || user.email}!
                  </h1>
                  <p className="text-[#00121F]/60">Cedric is monitoring your portfolio</p>
                </div>
              </div>
              
              <button
                onClick={() => { window.location.href = '/api/auth/logout'; }}
                className="text-[#00121F]/60 hover:text-[#00121F]/80 text-sm transition-colors"
              >
                Sign Out
              </button>
            </div>

            {/* Portfolio Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Portfolio Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-2xl font-semibold text-[#00121F] mb-2">
                  ${portfolioState?.totalInvestment.toLocaleString() || '10,000'}.00
                </div>
                
                {/* Account Status Indicator */}
                {portfolioState && (
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border">
                    {portfolioState.status === 'SUBMITTED' && (
                      <>
                        <Clock className="w-5 h-5 text-blue-500 animate-pulse" />
                        <div>
                          <div className="font-medium text-sm">Account Setup in Progress</div>
                          <div className="text-xs text-[#00121F]/60">
                            Your paper trading account is being created (usually takes 1-2 minutes)
                          </div>
                        </div>
                      </>
                    )}
                    {portfolioState.status === 'APPROVED' && (
                      <>
                        <Clock className="w-5 h-5 text-orange-500 animate-pulse" />
                        <div>
                          <div className="font-medium text-sm">Account Funding in Progress</div>
                          <div className="text-xs text-[#00121F]/60">
                            Funding your account and preparing to execute trades (2-4 minutes remaining)
                          </div>
                        </div>
                      </>
                    )}
                    {portfolioState.status === 'ACTIVE' && !portfolioState.hasExecutedTrades && (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <div>
                          <div className="font-medium text-sm">Executing Your Portfolio</div>
                          <div className="text-xs text-[#00121F]/60">
                            Account is funded! Placing your investment orders now...
                          </div>
                        </div>
                      </>
                    )}
                    {portfolioState.hasExecutedTrades && (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <div>
                          <div className="font-medium text-sm">Portfolio Active</div>
                          <div className="text-xs text-[#00121F]/60">
                            Your investments have been placed and Cedric is monitoring your portfolio
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
                
                {/* Allocation Preview (pending vs current vs target) */}
                {(() => {
                  const hasHoldings = !!(holdings && Array.isArray(holdings.positions) && holdings.positions.length > 0);
                  const hasWeights = !!(portfolioState?.weights && portfolioState.weights.length > 0);
                  if (!hasHoldings && !hasWeights) return null;

                  const isPending = !hasHoldings && !!orders && (orders.open_count ?? 0) > 0;
                  const label = isPending ? 'Pending Allocation' : (hasHoldings ? 'Current Allocation' : 'Target Allocation');

                  let pairs: Array<{ name: string; value: number }> = [];
                  if (hasHoldings) {
                    pairs = [
                      ...holdings!.positions.map((p) => ({ name: p.symbol, value: p.percent })),
                      { name: 'Cash', value: holdings!.cash_percent }
                    ];
                  } else if (isPending && orders) {
                    // Compute from open orders' notional relative to totalInvestment; include Cash as residual
                    const ti = portfolioState?.totalInvestment || 10000;
                    const map = new Map<string, number>();
                    for (const o of orders.open_orders || []) {
                      if (!o || !o.symbol || o.symbol === 'CASH') continue;
                      const notional = o.notional ? Number(o.notional) : 0;
                      if (!Number.isFinite(notional) || notional <= 0) continue;
                      map.set(o.symbol, (map.get(o.symbol) || 0) + notional);
                    }
                    let sumPct = 0;
                    pairs = Array.from(map.entries()).map(([sym, notional]) => {
                      const pct = Math.max(0, (notional / ti) * 100);
                      sumPct += pct;
                      return { name: sym, value: pct };
                    });
                    const cashPct = Math.max(0, 100 - sumPct);
                    pairs.push({ name: 'Cash', value: cashPct });
                    if (pairs.length === 1) {
                      // Fallback to target weights if orders had no notionals
                      const nonCash = (portfolioState!.weights || []).filter((w) => w.symbol !== 'CASH');
                      const sumNonCash = nonCash.reduce((s, w) => s + (w.weight || 0), 0);
                      const cashWeight = Math.max(0, 100 - sumNonCash);
                      pairs = [
                        ...nonCash.map((w) => ({ name: w.symbol, value: w.weight })),
                        { name: 'Cash', value: cashWeight }
                      ];
                    }
                  } else if (hasWeights) {
                    const nonCash = portfolioState!.weights!.filter((w) => w.symbol !== 'CASH');
                    const sumNonCash = nonCash.reduce((s, w) => s + (w.weight || 0), 0);
                    const cashWeight = Math.max(0, 100 - sumNonCash);
                    pairs = [
                      ...nonCash.map((w) => ({ name: w.symbol, value: w.weight })),
                      { name: 'Cash', value: cashWeight }
                    ];
                  }

                  return (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-[#00121F]/80">{label}:</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {pairs.slice(0, 6).map((item) => (
                          <div key={item.name} className="flex justify-between p-2 bg-slate-50 rounded">
                            <span className="font-medium">{item.name}</span>
                            <span>{item.value.toFixed(2)}%</span>
                          </div>
                        ))}
                        {pairs.length > 6 && (
                          <div className="text-[#00121F]/60 text-center col-span-2">
                            +{pairs.length - 6} more holdings
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </CardContent>
            </Card>

            {/* Holdings and Allocation */}
            {portfolioState?.hasExecutedTrades && (
              (() => {
                const showPending = (!holdings || holdings.positions.length === 0) && !!orders && orders.open_count > 0;
                if (showPending) {
                  const palette = ['#2563EB', '#16A34A', '#F59E0B', '#EF4444', '#10B981', '#8B5CF6', '#06B6D4', '#D946EF', '#F97316', '#84CC16'];
                  const ti = portfolioState?.totalInvestment || 10000;
                  const map = new Map<string, number>();
                  for (const o of (orders?.open_orders || [])) {
                    if (!o || !o.symbol || o.symbol === 'CASH') continue;
                    const notional = o.notional ? Number(o.notional) : 0;
                    if (!Number.isFinite(notional) || notional <= 0) continue;
                    map.set(o.symbol, (map.get(o.symbol) || 0) + notional);
                  }
                  let sumPct = 0;
                  let chartData = Array.from(map.entries()).map(([sym, notional], i) => {
                    const pct = Math.max(0, (notional / ti) * 100);
                    sumPct += pct;
                    return { name: sym, value: pct, color: palette[i % palette.length] };
                  });
                  if (chartData.length === 0) {
                    const weights = portfolioState?.weights || [];
                    const nonCash = weights.filter((w) => w.symbol !== 'CASH');
                    const sumNonCash = nonCash.reduce((s, w) => s + (w.weight || 0), 0);
                    const cashWeight = Math.max(0, 100 - sumNonCash);
                    chartData = [
                      ...nonCash.map((w, i) => ({ name: w.symbol, value: w.weight, color: palette[i % palette.length] })),
                      { name: 'Cash', value: cashWeight, color: '#9CA3AF' }
                    ];
                  } else {
                    const cashPct = Math.max(0, 100 - sumPct);
                    chartData.push({ name: 'Cash', value: cashPct, color: '#9CA3AF' });
                  }
                  return (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingUp className="w-5 h-5" />
                          Pending Portfolio
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {isOrdersLoading && (
                          <div className="flex items-center gap-2 text-sm text-[#00121F]/60 mb-2">
                            <Loader2 className="w-4 h-4 animate-spin" /> Checking pending orders...
                          </div>
                        )}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <div className="h-[320px]">
                            <PortfolioDonutChart data={chartData} showCenterText={false} />
                          </div>
                          <div className="text-sm text-[#00121F]/70 space-y-2">
                            <div>Orders submitted and pending fills. Once positions are established, this will switch to your actual holdings.</div>
                            <div className="text-[#00121F]/60">Open orders: {orders?.open_count ?? 0} • As of {orders?.as_of ? new Date(orders.as_of).toLocaleString() : '-'}</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                }
                // Current Holdings
                return (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Current Holdings
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {isHoldingsLoading && (
                        <div className="flex items-center gap-2 text-sm text-[#00121F]/60 mb-2">
                          <Loader2 className="w-4 h-4 animate-spin" /> Updating holdings...
                        </div>
                      )}
                      {holdings ? (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Holdings table */}
                          <div>
                            <div className="text-sm text-[#00121F]/60 mb-2">As of {new Date(holdings.as_of).toLocaleString()}</div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="text-left text-[#00121F]/60">
                                    <th className="py-2">Symbol</th>
                                    <th className="py-2">Qty</th>
                                    <th className="py-2">Market Value</th>
                                    <th className="py-2">% of Portfolio</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {holdings.positions.map((p) => (
                                    <tr key={p.symbol} className="border-t">
                                      <td className="py-2 font-medium">{p.symbol}</td>
                                      <td className="py-2">{p.qty}</td>
                                      <td className="py-2">${p.market_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                                      <td className="py-2">{p.percent.toFixed(2)}%</td>
                                    </tr>
                                  ))}
                                  <tr className="border-t">
                                    <td className="py-2 font-medium">Cash</td>
                                    <td className="py-2">—</td>
                                    <td className="py-2">${holdings.cash.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                                    <td className="py-2">{holdings.cash_percent.toFixed(2)}%</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          </div>

                          {/* Pie chart */}
                          <div className="h-[320px]">
                            {(() => {
                              const palette = ['#2563EB', '#16A34A', '#F59E0B', '#EF4444', '#10B981', '#8B5CF6', '#06B6D4', '#D946EF', '#F97316', '#84CC16'];
                              const data = [
                                ...holdings.positions.map((p, i) => ({ name: p.symbol, value: p.percent, color: palette[i % palette.length] })),
                                { name: 'Cash', value: holdings.cash_percent, color: '#9CA3AF' }
                              ];
                              return <PortfolioDonutChart data={data} showCenterText={false} />;
                            })()}
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-[#00121F]/60">No holdings yet. Your portfolio will appear here after trade execution.</div>
                      )}
                    </CardContent>
                  </Card>
                );
              })()
            )}

            {/* Explainability Chat */}
            {(() => {
              const isActive = portfolioState?.status === 'ACTIVE';
              const hasPending = (orders?.open_count ?? 0) > 0;
              const enabled = !!(isActive && (hasPending || portfolioState?.hasExecutedTrades));
              let reasonDisabled = '';
              if (!enabled) {
                if (!isActive) {
                  if (portfolioState?.status === 'APPROVED') {
                    reasonDisabled = 'Funding in progress. Chat will activate once orders are submitted.';
                  } else {
                    reasonDisabled = 'Awaiting account funding. Chat activates after funding and when trades are pending or executed.';
                  }
                } else if (!hasPending && !portfolioState?.hasExecutedTrades) {
                  reasonDisabled = 'Preparing your orders. Chat will activate once trades are pending or executed.';
                }
              }
              return (
                <div className="mt-6">
                  <ExplainabilityChat
                    enabled={enabled}
                    reasonDisabled={reasonDisabled}
                    accountId={portfolioState?.accountId || null}
                    status={portfolioState?.status || null}
                    hasExecutedTrades={!!portfolioState?.hasExecutedTrades}
                    holdings={holdings}
                    orders={orders}
                    userName={user?.given_name || user?.email || ''}
                    userEmail={user?.email || ''}
                    riskProfile={riskProfileStr || profile?.riskProfile}
                  />
                </div>
              );
            })()}
          </div>
        </div>
      </div>

      {/* Right section - Proposals */}
      <div className="w-[400px] bg-[#00090F] text-white p-8 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">Cedric's Proposals</h2>
        
        {proposals.length === 0 ? (
          <div className="text-center py-12">
            <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-white/60 text-sm">
              Cedric is watching the markets. When he has suggestions for your portfolio, they'll appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {proposals.map((proposal) => (
              <Card key={proposal.id} className="bg-white/10 border-white/20">
                <CardHeader>
                  <CardTitle className="text-white text-sm">
                    Portfolio Adjustment
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-white/80 text-sm">
                    {proposal.rationale}
                  </p>
                  
                  <pre className="bg-black/20 p-3 rounded text-xs text-white/70 overflow-auto">
                    {JSON.stringify(proposal.plan, null, 2)}
                  </pre>
                  
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleProposalAction(proposal.id, 'approve')}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                      size="sm"
                    >
                      Approve
                    </Button>
                    <Button
                      onClick={() => handleProposalAction(proposal.id, 'reject')}
                      variant="outline"
                      className="flex-1 border-white/30 text-white hover:bg-white/10"
                      size="sm"
                    >
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <div className="mt-8 pt-8 border-t border-white/20">
          <p className="text-xs text-white/40 text-center">
            This is an <strong>educational simulation</strong>. No real money is invested. 
            Nothing here is investment advice.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardClient() {
  return <DashboardContent />;
}
