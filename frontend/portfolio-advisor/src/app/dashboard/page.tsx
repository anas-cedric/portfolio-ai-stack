'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, MessageCircle, TrendingUp, DollarSign, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';

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

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useKindeBrowserClient();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [portfolioState, setPortfolioState] = useState<PortfolioState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTimer, setRefreshTimer] = useState<NodeJS.Timeout | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/api/auth/login');
    }
  }, [user, isAuthLoading, router]);

  // Fetch data when user is available
  useEffect(() => {
    if (user?.id) {
      fetchDashboardData();
    }
  }, [user]);

  // Auto-refresh when account is not ACTIVE yet
  useEffect(() => {
    if (portfolioState && portfolioState.status !== 'ACTIVE' && !portfolioState.hasExecutedTrades) {
      const timer = setTimeout(() => {
        fetchDashboardData();
      }, 30000); // Refresh every 30 seconds
      setRefreshTimer(timer);
    } else if (refreshTimer) {
      clearTimeout(refreshTimer);
      setRefreshTimer(null);
    }

    return () => {
      if (refreshTimer) {
        clearTimeout(refreshTimer);
      }
    };
  }, [portfolioState, refreshTimer]);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch activities and proposals in parallel
      const [activitiesRes, proposalsRes] = await Promise.all([
        fetch('/api/activity'),
        fetch('/api/cedric/proposals')
      ]);

      if (!activitiesRes.ok || !proposalsRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const activitiesData = await activitiesRes.json();
      const proposalsData = await proposalsRes.json();

      setActivities(activitiesData.activities || []);
      setProposals(proposalsData.proposals || []);

      // Extract portfolio state from latest activities
      const latestActivity = activitiesData.activities?.[0];
      if (latestActivity?.meta) {
        const meta = latestActivity.meta;
        setPortfolioState({
          status: meta.account_status || meta.initial_status || 'SUBMITTED',
          accountId: meta.alpaca_account_id,
          totalInvestment: meta.total_investment || 10000,
          weights: meta.target_weights || meta.weights,
          hasExecutedTrades: meta.trades_executed || false
        });
      }

      // If user has no activities, they probably haven't completed portfolio approval yet
      if (activitiesData.activities && activitiesData.activities.length === 0) {
        console.log('No activities found, redirecting to portfolio quiz');
        router.push('/portfolio-quiz');
        return;
      }

      // Check if account is ACTIVE but trades not executed yet
      if (portfolioState && portfolioState.status === 'ACTIVE' && !portfolioState.hasExecutedTrades) {
        executePortfolioTrades();
      }

    } catch (error: any) {
      console.error('Failed to fetch dashboard data:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const executePortfolioTrades = async () => {
    if (!portfolioState?.accountId || !portfolioState?.weights) {
      console.warn('Cannot execute trades: missing account ID or weights');
      return;
    }

    try {
      const response = await fetch('/api/portfolio/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          accountId: portfolioState.accountId,
          weights: portfolioState.weights,
          totalInvestment: portfolioState.totalInvestment
        })
      });

      if (response.ok) {
        // Refresh to show executed trades
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Failed to execute portfolio trades:', error);
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
              
              <Link href="/api/auth/logout">
                <button className="text-[#00121F]/60 hover:text-[#00121F]/80 text-sm transition-colors">
                  Sign Out
                </button>
              </Link>
            </div>

            {/* Error display */}
            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="pt-6">
                  <p className="text-red-600 text-sm">{error}</p>
                </CardContent>
              </Card>
            )}

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
                
                {/* Portfolio Weights Preview */}
                {portfolioState?.weights && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-[#00121F]/80">Target Allocation:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {portfolioState.weights.slice(0, 6).map((weight) => (
                        <div key={weight.symbol} className="flex justify-between p-2 bg-slate-50 rounded">
                          <span className="font-medium">{weight.symbol}</span>
                          <span>{weight.weight}%</span>
                        </div>
                      ))}
                      {portfolioState.weights.length > 6 && (
                        <div className="text-[#00121F]/60 text-center col-span-2">
                          +{portfolioState.weights.length - 6} more holdings
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="text-sm text-[#00121F]/60">
                  Simulated paper trading portfolio • Educational purposes only
                </div>
              </CardContent>
            </Card>

            {/* Activity Feed */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {activities.length === 0 ? (
                  <div className="text-center py-8 text-[#00121F]/60">
                    <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No activity yet. Approve a portfolio to get started!</p>
                  </div>
                ) : (
                  activities.map((activity) => (
                    <div key={activity.id} className="border border-[#00121F]/10 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="mt-1">
                          <ActivityIcon type={activity.type} />
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-[#00121F] mb-1">
                            {activity.title}
                          </div>
                          {activity.body && (
                            <div className="text-sm text-[#00121F]/70 mb-2">
                              {activity.body}
                            </div>
                          )}
                          <div className="text-xs text-[#00121F]/50">
                            {new Date(activity.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Chat Interface Placeholder */}
            <Card>
              <CardHeader>
                <CardTitle>Ask Cedric about your portfolio</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-[#00121F]/5 rounded-lg p-4 text-center">
                  <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm text-[#00121F]/60 mb-4">
                    Chat with Cedric about your investment strategy, market conditions, or portfolio performance.
                  </p>
                  <div className="text-xs text-[#00121F]/40">
                    Coming soon: Real-time portfolio chat
                  </div>
                </div>
              </CardContent>
            </Card>
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