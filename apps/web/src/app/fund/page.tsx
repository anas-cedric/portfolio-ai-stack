'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Loader2, DollarSign, CreditCard, Building2, CheckCircle, AlertCircle } from 'lucide-react';

interface Transfer {
  id: string;
  amount_cents: number;
  status: string;
  created_at: string;
}

export default function FundPage() {
  const router = useRouter();
  const [amount, setAmount] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [accountId, setAccountId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    // Load user and account data
    const storedUserId = localStorage.getItem('user_id');
    const storedAccountId = localStorage.getItem('account_id');
    
    if (!storedUserId || !storedAccountId) {
      router.push('/onboarding');
      return;
    }
    
    setUserId(storedUserId);
    setAccountId(storedAccountId);
    
    // Load transfer history
    loadTransferHistory(storedAccountId);
  }, [router]);

  const loadTransferHistory = async (accId: string) => {
    try {
      // In production, fetch from API
      // const response = await axios.get(`/api/transfers/${accId}`);
      // setTransfers(response.data);
    } catch (err) {
      console.error('Failed to load transfer history:', err);
    }
  };

  const handleDeposit = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const amountCents = Math.round(parseFloat(amount) * 100);
      
      const response = await axios.post('/api/funding/transfer', {
        user_id: userId,
        account_id: accountId,
        amount_cents: amountCents,
        direction: 'deposit'
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      if (response.data.id) {
        setSuccess(true);
        setAmount('');
        
        // Add to transfer history
        setTransfers([response.data, ...transfers]);
        
        // Redirect to trading after 2 seconds
        setTimeout(() => {
          router.push('/trade');
        }, 2000);
      }
    } catch (err) {
      setError('Failed to process deposit');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(cents / 100);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Fund Your Account</h1>
          <p className="text-gray-600">Add money to start building your portfolio</p>
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Deposit Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <DollarSign className="w-5 h-5 mr-2" />
                Make a Deposit
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="bank" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="bank">Bank Transfer</TabsTrigger>
                  <TabsTrigger value="card" disabled>Card</TabsTrigger>
                </TabsList>
                
                <TabsContent value="bank" className="space-y-4">
                  {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' ? (
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>Paper Trading:</strong> This is a simulated deposit. 
                        No real money will be transferred.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3 p-3 border rounded-lg">
                        <Building2 className="w-5 h-5 text-gray-500" />
                        <div>
                          <p className="font-medium">Chase Checking ****1234</p>
                          <p className="text-sm text-gray-500">Primary account</p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <Label htmlFor="amount">Amount</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
                      <Input
                        id="amount"
                        type="number"
                        placeholder="0.00"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        className="pl-10"
                        min="0"
                        step="0.01"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2">
                    <Button variant="outline" onClick={() => setAmount('100')}>$100</Button>
                    <Button variant="outline" onClick={() => setAmount('500')}>$500</Button>
                    <Button variant="outline" onClick={() => setAmount('1000')}>$1,000</Button>
                  </div>
                  
                  <Button 
                    onClick={handleDeposit}
                    disabled={!amount || isLoading}
                    className="w-full"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' ? 'Simulate Deposit' : 'Deposit Funds'}
                  </Button>
                </TabsContent>
                
                <TabsContent value="card">
                  <div className="text-center py-8 text-gray-500">
                    <CreditCard className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>Card deposits coming soon</p>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Transfer History */}
          <Card>
            <CardHeader>
              <CardTitle>Transfer History</CardTitle>
            </CardHeader>
            <CardContent>
              {transfers.length > 0 ? (
                <div className="space-y-3">
                  {transfers.map((transfer) => (
                    <div key={transfer.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{formatCurrency(transfer.amount_cents)}</p>
                        <p className="text-sm text-gray-500">{formatDate(transfer.created_at)}</p>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        transfer.status === 'completed' 
                          ? 'bg-green-100 text-green-800'
                          : transfer.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {transfer.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No transfers yet</p>
                  <p className="text-sm mt-2">Make your first deposit to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <div>
                <p className="font-medium text-green-800">Deposit successful!</p>
                <p className="text-sm text-green-700 mt-1">Redirecting to trading...</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="mt-8 flex justify-between">
          <Button variant="outline" onClick={() => router.push('/portfolio')}>
            View Portfolio
          </Button>
          <Button onClick={() => router.push('/trade')}>
            Start Trading
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