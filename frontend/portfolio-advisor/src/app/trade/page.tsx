'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import { useUserProfile } from "@/contexts/UserContext";
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Loader2, TrendingUp, TrendingDown, DollarSign, Activity, CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface TradeIntentItem {
  symbol: string;
  side: 'buy' | 'sell';
  qty?: number;
  notional?: number;
  current_weight?: number;
  target_weight?: number;
}

interface TradeIntent {
  id: string;
  items: TradeIntentItem[];
  status: string;
  rationale?: string;
  created_at: string;
}

interface PortfolioProposal {
  id: string;
  targets: Record<string, number>;
  rationale: string;
  risk_bucket: string;
}

export default function TradePage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useKindeBrowserClient();
  const { profile } = useUserProfile();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [tradeIntents, setTradeIntents] = useState<TradeIntent[]>([]);
  const [portfolioProposal, setPortfolioProposal] = useState<PortfolioProposal | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  const [selectedTradeIntent, setSelectedTradeIntent] = useState<TradeIntent | null>(null);

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthLoading && !user) {
      router.push('/api/auth/login');
      return;
    }
    
    // Use Kinde user ID and create mock account ID
    if (user?.id) {
      const mockAccountId = `account_${user.id}`;
      setAccountId(mockAccountId);
      
      // Load portfolio data
      loadPortfolioProposal(user.id);
      checkRebalance(mockAccountId);
    }
  }, [user, isAuthLoading, router]);

  const loadPortfolioProposal = async (uId: string) => {
    try {
      // ✅ GOOD: Get user's actual age from context (collected during onboarding)
      const userAge = profile?.age;
      
      // ❌ ISSUE CALLED OUT: Don't proceed if we don't have user age
      if (!userAge) {
        console.error('User age not available - redirect to portfolio quiz');
        router.push('/portfolio-quiz');
        return;
      }
      
      const response = await axios.post('/api/portfolio/propose', {
        user_id: uId,
        age: userAge
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      setPortfolioProposal(response.data);
    } catch (err) {
      console.error('Failed to load portfolio proposal:', err);
    }
  };

  const checkRebalance = async (accId: string) => {
    try {
      const response = await axios.post('/api/rebalance/check', {
        account_id: accId
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      if (response.data.needs_rebalance && response.data.trade_intent_id) {
        // Mock trade intent for demo
        const mockTradeIntent: TradeIntent = {
          id: response.data.trade_intent_id,
          items: response.data.trades,
          status: 'staged',
          rationale: response.data.rationale,
          created_at: new Date().toISOString()
        };
        setTradeIntents([mockTradeIntent]);
      }
    } catch (err) {
      console.error('Failed to check rebalance:', err);
    }
  };

  const createInitialOrders = async () => {
    if (!portfolioProposal) return;

    setIsLoading(true);
    setError(null);

    try {
      // Convert portfolio proposal to trade items
      const items: TradeIntentItem[] = Object.entries(portfolioProposal.targets).map(([symbol, weight]) => ({
        symbol,
        side: 'buy' as const,
        notional: Math.round((weight / 100) * 10000), // Assume $10k portfolio
        target_weight: weight
      }));

      // Create mock trade intent for initial portfolio
      const mockTradeIntent: TradeIntent = {
        id: crypto.randomUUID(),
        items,
        status: 'staged',
        rationale: portfolioProposal.rationale,
        created_at: new Date().toISOString()
      };

      setTradeIntents([mockTradeIntent, ...tradeIntents]);
      setSelectedTradeIntent(mockTradeIntent);
    } catch (err) {
      setError('Failed to create initial orders');
    } finally {
      setIsLoading(false);
    }
  };

  const submitOrders = async (tradeIntent: TradeIntent) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/orders/submit', {
        user_id: user?.id,
        account_id: accountId,
        trade_intent_id: tradeIntent.id
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      if (response.data.status === 'submitted') {
        // Update trade intent status
        setTradeIntents(intents => 
          intents.map(intent => 
            intent.id === tradeIntent.id 
              ? { ...intent, status: 'submitted' }
              : intent
          )
        );
        
        setSuccess(true);
        
        // Redirect to portfolio after 3 seconds
        setTimeout(() => {
          router.push('/portfolio');
        }, 3000);
      }
    } catch (err) {
      setError('Failed to submit orders');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'staged':
        return 'bg-blue-100 text-blue-800';
      case 'submitted':
        return 'bg-orange-100 text-orange-800';
      case 'filled':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'staged':
        return <Clock className="w-4 h-4" />;
      case 'submitted':
        return <Activity className="w-4 h-4" />;
      case 'filled':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Center</h1>
          <p className="text-gray-600">Review and submit your portfolio orders</p>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Trade Intents List */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Staged Orders</span>
                  {tradeIntents.length === 0 && portfolioProposal && (
                    <Button onClick={createInitialOrders} disabled={isLoading}>
                      {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                      Create Initial Portfolio
                    </Button>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {tradeIntents.length > 0 ? (
                  <div className="space-y-4">
                    {tradeIntents.map((tradeIntent) => (
                      <div 
                        key={tradeIntent.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                          selectedTradeIntent?.id === tradeIntent.id 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => setSelectedTradeIntent(tradeIntent)}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <Badge variant="secondary" className={getStatusColor(tradeIntent.status)}>
                              {getStatusIcon(tradeIntent.status)}
                              <span className="ml-1 capitalize">{tradeIntent.status}</span>
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {tradeIntent.items.length} orders
                            </span>
                          </div>
                          <span className="text-sm text-gray-500">
                            {new Date(tradeIntent.created_at).toLocaleDateString()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          {tradeIntent.items.slice(0, 4).map((item, index) => (
                            <div key={index} className="text-sm">
                              <div className="flex items-center">
                                {item.side === 'buy' ? (
                                  <TrendingUp className="w-3 h-3 text-green-600 mr-1" />
                                ) : (
                                  <TrendingDown className="w-3 h-3 text-red-600 mr-1" />
                                )}
                                <span className="font-medium">{item.symbol}</span>
                              </div>
                              {item.notional && (
                                <div className="text-gray-500">
                                  {formatCurrency(item.notional)}
                                </div>
                              )}
                            </div>
                          ))}
                          {tradeIntent.items.length > 4 && (
                            <div className="text-sm text-gray-500">
                              +{tradeIntent.items.length - 4} more
                            </div>
                          )}
                        </div>

                        {tradeIntent.rationale && (
                          <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                            {tradeIntent.rationale}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">No staged orders</p>
                    <p className="text-sm text-gray-400 mt-1">
                      Orders will appear here when generated
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Order Details */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Order Details</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedTradeIntent ? (
                  <div className="space-y-4">
                    {/* Status */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Status:</span>
                      <Badge className={getStatusColor(selectedTradeIntent.status)}>
                        {getStatusIcon(selectedTradeIntent.status)}
                        <span className="ml-1 capitalize">{selectedTradeIntent.status}</span>
                      </Badge>
                    </div>

                    {/* Orders List */}
                    <div>
                      <h4 className="font-medium mb-2">Orders ({selectedTradeIntent.items.length})</h4>
                      <div className="space-y-2">
                        {selectedTradeIntent.items.map((item, index) => (
                          <div key={index} className="flex items-center justify-between text-sm">
                            <div className="flex items-center">
                              {item.side === 'buy' ? (
                                <TrendingUp className="w-3 h-3 text-green-600 mr-1" />
                              ) : (
                                <TrendingDown className="w-3 h-3 text-red-600 mr-1" />
                              )}
                              <span className="font-medium">{item.symbol}</span>
                            </div>
                            <div className="text-right">
                              {item.notional && (
                                <div>{formatCurrency(item.notional)}</div>
                              )}
                              {item.target_weight && (
                                <div className="text-gray-500">{item.target_weight}%</div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Total */}
                    <div className="border-t pt-3">
                      <div className="flex justify-between font-medium">
                        <span>Total Investment:</span>
                        <span>
                          {formatCurrency(
                            selectedTradeIntent.items.reduce((sum, item) => sum + (item.notional || 0), 0)
                          )}
                        </span>
                      </div>
                    </div>

                    {/* Rationale */}
                    {selectedTradeIntent.rationale && (
                      <div className="border-t pt-3">
                        <h4 className="font-medium mb-2">Rationale</h4>
                        <p className="text-sm text-gray-600">{selectedTradeIntent.rationale}</p>
                      </div>
                    )}

                    {/* Action Button */}
                    {selectedTradeIntent.status === 'staged' && (
                      <Button 
                        onClick={() => submitOrders(selectedTradeIntent)}
                        disabled={isLoading}
                        className="w-full"
                      >
                        {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                        Submit Orders
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Select an order to view details</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Demo Mode Notice */}
            {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' && (
              <Card className="mt-4">
                <CardContent className="pt-6">
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      <strong>Paper Trading Mode</strong><br />
                      All orders are simulated. No real money involved.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <div>
                <p className="font-medium text-green-800">Orders submitted successfully!</p>
                <p className="text-sm text-green-700 mt-1">
                  Your orders are being processed. Redirecting to portfolio...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 flex justify-between">
          <Button variant="outline" onClick={() => router.push('/fund')}>
            Back to Funding
          </Button>
          <Button onClick={() => router.push('/portfolio')}>
            View Portfolio
          </Button>
        </div>

        {/* Error Dialog */}
        <AlertDialog open={!!error}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                <AlertCircle className="w-5 h-5 text-red-600 inline mr-2" />
                Error
              </AlertDialogTitle>
              <AlertDialogDescription>{error}</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogAction onClick={() => setError(null)}>OK</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}