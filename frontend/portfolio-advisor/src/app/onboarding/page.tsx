'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

type OnboardingStep = 'agreements' | 'kyc' | 'account' | 'complete';

interface Agreement {
  id: string;
  kind: string;
  version: string;
  url?: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('agreements');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agreements, setAgreements] = useState<Agreement[]>([]);
  const [acceptedAgreements, setAcceptedAgreements] = useState<Set<string>>(new Set());
  const [kycApplicationId, setKycApplicationId] = useState<string | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  
  // Progress calculation
  const stepProgress = {
    agreements: 25,
    kyc: 50,
    account: 75,
    complete: 100
  };

  useEffect(() => {
    // Load user data from session/context
    const storedUserId = localStorage.getItem('user_id');
    if (storedUserId) {
      setUserId(storedUserId);
    } else {
      // Generate new user ID for demo
      const newUserId = crypto.randomUUID();
      localStorage.setItem('user_id', newUserId);
      setUserId(newUserId);
    }

    // Load agreements
    loadAgreements();
  }, []);

  const loadAgreements = async () => {
    // In production, fetch from API
    setAgreements([
      { id: '1', kind: 'terms', version: '1.0', url: '/legal/terms-v1.pdf' },
      { id: '2', kind: 'privacy', version: '1.0', url: '/legal/privacy-v1.pdf' },
      { id: '3', kind: 'advisory', version: '1.0', url: '/legal/advisory-v1.pdf' },
      { id: '4', kind: 'esign', version: '1.0', url: '/legal/esign-v1.pdf' }
    ]);
  };

  const handleAcceptAgreements = async () => {
    if (acceptedAgreements.size !== agreements.length) {
      setError('Please accept all agreements to continue');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/agreements/accept', {
        user_id: userId,
        agreement_ids: Array.from(acceptedAgreements)
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      if (response.data.acceptances) {
        setCurrentStep('kyc');
      }
    } catch (err) {
      setError('Failed to record agreement acceptance');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartKYC = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Get user info from previous steps (stored in localStorage or context)
      const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');

      const response = await axios.post('/api/kyc/start', {
        user_id: userId,
        personal_info: userInfo
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      if (response.data.id) {
        setKycApplicationId(response.data.id);
        
        // For paper trading, auto-proceed to account opening
        if (response.data.status === 'approved') {
          setCurrentStep('account');
          handleOpenAccount(response.data.id);
        }
      }
    } catch (err) {
      setError('Failed to start KYC process');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenAccount = async (kycId?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/accounts/open', {
        user_id: userId,
        kyc_application_id: kycId || kycApplicationId
      }, {
        headers: {
          'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'demo_key'
        }
      });

      if (response.data.id) {
        setAccountId(response.data.id);
        localStorage.setItem('account_id', response.data.id);
        setCurrentStep('complete');
        
        // Redirect to funding after 2 seconds
        setTimeout(() => {
          router.push('/fund');
        }, 2000);
      }
    } catch (err) {
      setError('Failed to open account');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAgreement = (agreementId: string) => {
    const newAccepted = new Set(acceptedAgreements);
    if (newAccepted.has(agreementId)) {
      newAccepted.delete(agreementId);
    } else {
      newAccepted.add(agreementId);
    }
    setAcceptedAgreements(newAccepted);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'agreements':
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Review and Accept Agreements</h2>
            <p className="text-gray-600">Please review and accept the following agreements to continue:</p>
            
            <div className="space-y-3">
              {agreements.map((agreement) => (
                <div key={agreement.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      id={`agreement-${agreement.id}`}
                      checked={acceptedAgreements.has(agreement.id)}
                      onChange={() => toggleAgreement(agreement.id)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <label htmlFor={`agreement-${agreement.id}`} className="cursor-pointer">
                      <span className="font-medium capitalize">{agreement.kind}</span>
                      <span className="text-sm text-gray-500 ml-2">v{agreement.version}</span>
                    </label>
                  </div>
                  {agreement.url && (
                    <a href={agreement.url} target="_blank" rel="noopener noreferrer" 
                       className="text-blue-600 hover:underline text-sm">
                      View PDF
                    </a>
                  )}
                </div>
              ))}
            </div>

            <Button 
              onClick={handleAcceptAgreements}
              disabled={acceptedAgreements.size !== agreements.length || isLoading}
              className="w-full"
            >
              {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Accept and Continue
            </Button>
          </div>
        );

      case 'kyc':
        return (
          <div className="space-y-4 text-center">
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto" />
            <h2 className="text-xl font-semibold">Identity Verification</h2>
            
            {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' ? (
              <>
                <p className="text-gray-600">
                  For paper trading, identity verification is automatically approved.
                </p>
                <Button onClick={() => handleStartKYC()} disabled={isLoading}>
                  {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  Continue to Account Setup
                </Button>
              </>
            ) : (
              <>
                <p className="text-gray-600">
                  We need to verify your identity to comply with regulations.
                </p>
                <Button onClick={() => handleStartKYC()} disabled={isLoading}>
                  {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  Start Verification
                </Button>
              </>
            )}
          </div>
        );

      case 'account':
        return (
          <div className="space-y-4 text-center">
            <Loader2 className="w-12 h-12 text-blue-600 mx-auto animate-spin" />
            <h2 className="text-xl font-semibold">Opening Your Account</h2>
            <p className="text-gray-600">
              We're setting up your brokerage account. This will just take a moment...
            </p>
          </div>
        );

      case 'complete':
        return (
          <div className="space-y-4 text-center">
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto" />
            <h2 className="text-xl font-semibold">Account Ready!</h2>
            <p className="text-gray-600">
              Your account has been successfully created. Redirecting to funding...
            </p>
            {accountId && (
              <p className="text-sm text-gray-500">Account ID: {accountId}</p>
            )}
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Account Setup</h1>
          <p className="text-gray-600">Complete these steps to start investing</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <Progress value={stepProgress[currentStep]} className="h-2" />
          <div className="flex justify-between mt-2 text-sm text-gray-600">
            <span className={currentStep === 'agreements' ? 'font-semibold' : ''}>Agreements</span>
            <span className={['kyc', 'account', 'complete'].includes(currentStep) ? 'font-semibold' : ''}>Verification</span>
            <span className={['account', 'complete'].includes(currentStep) ? 'font-semibold' : ''}>Account</span>
            <span className={currentStep === 'complete' ? 'font-semibold' : ''}>Complete</span>
          </div>
        </div>

        {/* Main Card */}
        <Card>
          <CardContent className="pt-6">
            {renderStepContent()}
          </CardContent>
        </Card>

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

        {/* Demo Mode Banner */}
        {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' && (
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <strong>Demo Mode:</strong> You're using Alpaca Paper Trading. 
              All transactions are simulated and no real money is involved.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}