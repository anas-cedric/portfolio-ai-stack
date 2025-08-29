'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import Image from 'next/image';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

type OnboardingStep = 'agreements' | 'kyc' | 'account' | 'complete';

interface Agreement {
  id: string;
  title: string;
  version: string;
  pdfUrl: string;
  summary: string;
  required: boolean;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useKindeBrowserClient();
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('agreements');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agreements, setAgreements] = useState<Agreement[]>([]);
  const [acceptedAgreements, setAcceptedAgreements] = useState<Set<string>>(new Set());
  const [kycApplicationId, setKycApplicationId] = useState<string | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  
  // Progress calculation
  const stepProgress = {
    agreements: 25,
    kyc: 50,
    account: 75,
    complete: 100
  };

  const allRequiredChecked = agreements
    .filter(a => a.required)
    .every(a => acceptedAgreements.has(a.id));

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthLoading && !user) {
      router.push('/api/auth/login');
      return;
    }

    // Load agreements when user is authenticated
    if (user?.id) {
      loadAgreements();
    }
  }, [user, isAuthLoading, router]);

  const loadAgreements = async () => {
    try {
      const res = await fetch('/api/agreements');
      const data = await res.json();
      setAgreements(data.agreements || []);
    } catch {
      setAgreements([]);
    }
  };

  const handleAcceptAgreements = async () => {
    const requiredIds = agreements.filter(a => a.required).map(a => a.id);
    const missingRequired = requiredIds.filter(id => !acceptedAgreements.has(id));
    if (missingRequired.length > 0) {
      setError('Please accept all required agreements to continue');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/agreements/accept', {
        user_id: user?.id,
        agreement_ids: Array.from(acceptedAgreements)
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
      // User info will come from Kinde user profile

      const response = await axios.post('/api/kyc/start', {
        user_id: user?.id,
        personal_info: {
          first_name: user?.given_name,
          last_name: user?.family_name,
          email: user?.email
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
        user_id: user?.id,
        kyc_application_id: kycId || kycApplicationId
      });

      if (response.data.id) {
        setAccountId(response.data.id);
        setCurrentStep('complete');
        
        // Auto-redirect to dashboard after 3 seconds
        setTimeout(() => {
          router.push('/dashboard');
        }, 3000);
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
          <div className="space-y-5">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Review and Accept Agreements</h2>
              <p className="text-gray-700 mt-2">Please review and accept the following agreements to continue:</p>
            </div>
            
            <div className="space-y-3">
              {agreements.map((agreement) => (
                <div key={agreement.id} className="flex items-center justify-between p-4 bg-white/50 backdrop-blur-sm border border-white/60 rounded-xl hover:bg-white/60 transition-all">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      id={`agreement-${agreement.id}`}
                      checked={acceptedAgreements.has(agreement.id)}
                      onChange={() => toggleAgreement(agreement.id)}
                      className="w-4 h-4 text-blue-600 bg-white border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                    />
                    <label htmlFor={`agreement-${agreement.id}`} className="cursor-pointer flex-1">
                      <div className="font-semibold text-gray-900">
                        {agreement.title}
                        <span className="text-sm text-gray-600 ml-2 font-normal">v{agreement.version}</span>
                        {agreement.required && <span className="text-red-500 ml-1">*</span>}
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{agreement.summary}</p>
                    </label>
                  </div>
                  {agreement.pdfUrl && (
                    <a href={agreement.pdfUrl} target="_blank" rel="noopener noreferrer" 
                       className="text-blue-600 hover:text-blue-700 font-medium text-sm ml-4 whitespace-nowrap">
                      View PDF
                    </a>
                  )}
                </div>
              ))}
            </div>

            <Button 
              onClick={handleAcceptAgreements}
              disabled={!allRequiredChecked || isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Accept and Continue
            </Button>
          </div>
        );

      case 'kyc':
        return (
          <div className="space-y-6 text-center py-4">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Identity Verification</h2>
              
              {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' ? (
                <p className="text-gray-700 mt-3">
                  For paper trading, identity verification is automatically approved.
                </p>
              ) : (
                <p className="text-gray-700 mt-3">
                  We need to verify your identity to comply with regulations.
                </p>
              )}
            </div>
            
            <Button 
              onClick={() => handleStartKYC()} 
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-xl transition-all disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' ? 'Continue to Account Setup' : 'Start Verification'}
            </Button>
          </div>
        );

      case 'account':
        return (
          <div className="space-y-6 text-center py-8">
            <Loader2 className="w-16 h-16 text-blue-600 mx-auto animate-spin" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Opening Your Account</h2>
              <p className="text-gray-700 mt-3">
                We're setting up your brokerage account. This will just take a moment...
              </p>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="space-y-6 text-center py-8">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Welcome to Portfolio Advisor!</h2>
              <p className="text-gray-700 mt-3">
                Your account is ready. Let's get you started with your personalized portfolio.
              </p>
              {accountId && (
                <div className="mt-4 p-3 bg-white/50 backdrop-blur-sm rounded-lg">
                  <p className="text-sm text-gray-600 font-medium">Account ID: <span className="font-mono text-gray-900">{accountId}</span></p>
                </div>
              )}
            </div>
            <Button 
              onClick={() => router.push('/dashboard')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-xl"
            >
              Go to Dashboard
            </Button>
          </div>
        );
    }
  };

  return (
    <div className="w-full min-h-screen overflow-auto clouds-bg py-8 px-4 flex flex-col items-center">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image 
              src="/images/cedric-logo-new.png" 
              alt="Cedric" 
              width={120} 
              height={120}
            />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Account Setup</h1>
          <p className="text-gray-700 text-lg">Complete these steps to start investing</p>
        </div>

        {/* Progress Bar */}
        <div className="glass-card p-4 mb-8">
          <Progress value={stepProgress[currentStep]} className="h-2" />
          <div className="flex justify-between mt-3 text-sm text-gray-700 font-medium">
            <span className={currentStep === 'agreements' ? 'font-bold text-gray-900' : ''}>Agreements</span>
            <span className={['kyc', 'account', 'complete'].includes(currentStep) ? 'font-bold text-gray-900' : ''}>Verification</span>
            <span className={['account', 'complete'].includes(currentStep) ? 'font-bold text-gray-900' : ''}>Account</span>
            <span className={currentStep === 'complete' ? 'font-bold text-gray-900' : ''}>Complete</span>
          </div>
        </div>

        {/* Main Card with Glass Effect */}
        <div className="glass-card p-8">
          {renderStepContent()}
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

        {/* Demo Mode Banner */}
        {process.env.NEXT_PUBLIC_PROVIDER === 'alpaca_paper' && (
          <div className="mt-6 glass-card p-4 bg-yellow-50/30">
            <p className="text-sm text-yellow-900 font-medium">
              <strong>Demo Mode:</strong> You're using Alpaca Paper Trading. 
              All transactions are simulated and no real money is involved.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}