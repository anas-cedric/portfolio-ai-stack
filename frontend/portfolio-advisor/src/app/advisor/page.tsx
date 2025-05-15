'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';
import PortfolioResults from '@/components/PortfolioResults';
import ChatInterface from '@/components/ChatInterface';
import ProfileWizard from '@/components/ProfileWizard';
import AssetListItem from '@/components/AssetListItem';
import { RISK_QUESTIONS } from '@/lib/constants';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';
import { PortfolioResponse, PortfolioData, UserProfile } from '@/lib/types';

import dynamic from 'next/dynamic';
const PortfolioDonutChart = dynamic(() => import('@/components/PortfolioDonutChart'), {
  ssr: false,
  loading: () => <div className="w-full h-[400px] flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-white" /> <p className="text-white ml-2">Loading Chart...</p></div>,
});

type PortfolioState = PortfolioResponse | null;

type Step = 'welcome' | 'questionnaire' | 'ageInput' | 'results';
const STEPS: Step[] = ['welcome', 'questionnaire', 'ageInput', 'results'];
const TOTAL_STEPS = STEPS.length - 1;

// Predefined colors for the sample data to avoid hydration mismatch
const sampleChartColors = [
  '#10B981', // Emerald 500
  '#F59E0B', // Amber 500
  '#3B82F6', // Blue 500
  '#EC4899', // Pink 500
  '#8B5CF6', // Violet 500
  '#EF4444', // Red 500
  '#6366F1', // Indigo 500
];

export default function AdvisorPage() {
  const [portfolioData, setPortfolioData] = useState<PortfolioState>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [userAge, setUserAge] = useState<number | ''>('');
  const [isLoading, setIsLoading] = useState(false);

  const sampleAssetData = [
    { name: 'Vanguard Total Bond', ticker: 'BND', description: 'Broad exposure to U.S. investment-grade bonds.', expenseRatio: 0.03 / 100, weight: 0.26, icon: 'V' },
    { name: 'Vanguard Total Intl Bond', ticker: 'BNDX', description: 'Broad exposure to non-U.S. investment-grade bonds.', expenseRatio: 0.07 / 100, weight: 0.156, icon: 'V' },
    { name: 'Vanguard Total Stock Market', ticker: 'VTI', description: 'Exposure to the entire U.S. stock market.', expenseRatio: 0.03 / 100, weight: 0.125, icon: 'V' },
    { name: 'Vanguard Short-Term TIPS', ticker: 'VTIP', description: 'Protection against inflation with U.S. Treasury Inflation-Protected Securities.', expenseRatio: 0.03 / 100, weight: 0.104, icon: 'V' },
    { name: 'Vanguard FTSE Developed', ticker: 'VEA', description: 'Exposure to developed stock markets outside the U.S.', expenseRatio: 0.03 / 100, weight: 0.088, icon: 'V' },
  ];

  const sampleDonutData = sampleAssetData.map((asset, index) => ({
    name: asset.ticker,
    value: asset.weight * 100,
    color: sampleChartColors[index % sampleChartColors.length] // Use predefined colors
  }));

  const handleStart = () => {
    setCurrentStep('questionnaire');
  };

  const handleWizardComplete = (answers: Record<string, string>) => {
    console.log('Wizard completed with answers:', answers);
    setUserAnswers(answers);
    setCurrentStep('ageInput');
  };

  const handleAgeSubmit = async () => {
    if (userAge === '' || userAge <= 0) {
      setError('Please enter a valid age.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'test_api_key_for_development';

      const payload = {
        answers: userAnswers,
        age: Number(userAge)
      };
      console.log("Sending payload to backend:", JSON.stringify(payload, null, 2));

      const response = await axios.post(`/api/generate-portfolio-from-wizard`, 
        payload, 
        {
          headers: {
            'x-api-key': apiKey,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('API Response:', response.data);
      if (response.data) {
        setTimeout(() => {
          setPortfolioData(response.data);
          setCurrentStep('results');
          setError(null); 
          setIsLoading(false); 
        }, 5000); 
      } else {
        setError("Failed to generate portfolio. Received unexpected data from the server.");
        setIsLoading(false); 
      }
    } catch (err: any) {
      console.error('API Error during age submit:', err);
      
      let displayError = "An unknown error occurred while generating the portfolio."; 

      const errorData = err.response?.data;
      if (errorData && Array.isArray(errorData.detail) && errorData.detail.length > 0 && errorData.detail[0].msg) {
        displayError = `Validation Error: ${errorData.detail[0].msg}`;
      } else if (typeof errorData?.detail === 'string') {
        displayError = errorData.detail;
      } else if (err.message) {
        displayError = err.message;
      }

      setError(displayError); 
      setIsLoading(false); 
    } finally {
    }
  };

  const handleReset = () => {
    setPortfolioData(null);
    setError(null);
    setUserAnswers({});
    setUserAge('');
    setCurrentStep('welcome');
    setIsLoading(false);
  };

  const handlePortfolioUpdate = (updatedPortfolioResponse: PortfolioResponse) => {
    console.log("AdvisorPage: Received updated portfolio data", updatedPortfolioResponse);
    setPortfolioData(updatedPortfolioResponse); 
  };

  const calculateProgress = () => {
    const currentStepIndex = STEPS.indexOf(currentStep);
    if (currentStepIndex <= 0) return 0;
    if (currentStep === 'results') return 100;
    return Math.round(((currentStepIndex) / TOTAL_STEPS) * 100);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <Card className="w-full max-w-lg mx-auto bg-white/20 backdrop-blur-md border border-white/30 rounded-lg shadow-lg">
            <CardHeader>
              <CardTitle className="text-center text-2xl text-white drop-shadow-sm">Welcome to Paige</CardTitle>
              <p className="text-center text-sm pt-1 text-white drop-shadow-sm">
                Your AI-powered wealth advisor. Let's get started by understanding your risk tolerance.
              </p>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Button onClick={handleStart} className="bg-white text-blue-600 hover:bg-blue-50">Start Questionnaire</Button>
            </CardContent>
          </Card>
        );
      case 'questionnaire':
        return (
          <ProfileWizard
            questions={RISK_QUESTIONS}
            onComplete={handleWizardComplete}
          />
        );
      case 'ageInput':
        return (
          <Card className="w-full max-w-md mx-auto bg-white/20 backdrop-blur-md border border-white/30 rounded-lg shadow-lg">
            <CardHeader>
              <CardTitle className="text-center text-white drop-shadow-sm">Tell us about yourself</CardTitle>
              <p className="text-center text-sm pt-1 text-white drop-shadow-sm">Please, enter your age so we can tailor the portfolio allocation.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center p-8 text-center min-h-[150px]"> 
                  <Loader2 className="h-12 w-12 animate-spin text-sky-600 mb-4" />
                  <p className="text-lg font-semibold text-gray-700">Paige is designing your portfolio...</p>
                  <p className="text-sm text-muted-foreground">This may take a moment.</p>
                </div>
              ) : (
                <>
                  <p className="text-center text-gray-600">
                    Please enter your age so we can tailor the portfolio allocation.
                  </p>
                  <div className="space-y-2">
                    <Label htmlFor="ageInput" className="text-white font-medium">Your Age</Label>
                    <Input
                      id="ageInput"
                      type="number"
                      className="bg-white/70 text-slate-900 w-full"
                      value={userAge}
                      onChange={(e) => {
                        const value = e.target.value;
                        setUserAge(value === '' ? '' : parseInt(value, 10));
                      }}
                      placeholder="Enter your age"
                      min="18" 
                      max="100" 
                    />
                  </div>
                  {error && (
                    <p className="text-red-500 text-sm text-center">{error}</p>
                  )}
                </>
              )}
            </CardContent>
            {!isLoading && (
              <CardFooter className="flex justify-center">
                <div className="flex space-x-4 justify-between w-full">
                  <Button 
                    variant="outline" 
                    className="bg-white/20 text-white hover:bg-white/30 border-white/30"
                    onClick={() => setCurrentStep('questionnaire')}
                  >
                    Back
                  </Button>
                  <Button 
                    onClick={handleAgeSubmit}
                    disabled={!userAge}
                    className="bg-white text-blue-600 hover:bg-blue-50"
                  >
                    <span>Next</span>
                    <svg className="ml-2 w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 16 16 12 12 8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                  </Button>
                </div>
              </CardFooter>
            )}
          </Card>
        );
      case 'results':
        return (
          <div className="w-full flex-grow flex flex-col"> 
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-3xl font-bold text-gray-800">Your Portfolio Recommendation</h1>
              <Button variant="outline" onClick={() => { setCurrentStep('welcome'); setPortfolioData(null); /* Reset other states if needed */ }}>
                Start Over
              </Button>
            </div>

            <div className="flex-grow grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Left Column: Asset List */}
              <div className="md:col-span-2 space-y-4 overflow-y-auto pr-2" style={{ maxHeight: 'calc(100vh - 250px)' }}>
                <h2 className="text-xl font-semibold text-gray-700 mb-3">Hi, Sergey! Based on your profile, I've designed this portfolio for you:</h2>
                <p className="text-sm text-gray-600 mb-4">The fund employs an indexing investment approach designed to track the performance of the FTSE Developed All Cap ex U.S. Index, a market-capitalization-weighted index that is made up of approximately 3,837 common stocks of large-, mid-, and small-cap companies located in Canada and the major markets of Europe and the Pacific region.</p>
                
                <div className="mb-4">
                  <div className="grid grid-cols-3 mb-2">
                    <div className="text-sm font-medium text-gray-500">Asset</div>
                    <div className="text-sm font-medium text-gray-500 text-right">Expense Ratio</div>
                    <div className="text-sm font-medium text-gray-500 text-right">Weights</div>
                  </div>
                  {sampleAssetData.map((asset, index) => (
                    <AssetListItem key={index} asset={asset} />
                  ))}
                </div>
              </div>

              {/* Right Column: Donut Chart & Legend */}
              <div className="md:col-span-1 w-full flex flex-col space-y-4 p-6 bg-slate-900 rounded-lg">
                <Card className="bg-transparent border-none shadow-none">
                  <CardHeader>
                    <CardTitle className="text-2xl font-semibold text-white">Portfolio Allocation</CardTitle>
                  </CardHeader>
                  <CardContent className="h-[400px]">
                    <PortfolioDonutChart data={sampleDonutData} />
                  </CardContent>
                  <CardFooter>
                    <ul className="text-white text-sm space-y-1">
                      {sampleDonutData.map((entry, idx) => (
                        <li key={idx} className="flex items-center">
                          <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: entry.color }}></span>
                          {entry.name}: {entry.value}%
                        </li>
                      ))}
                    </ul>
                  </CardFooter>
                </Card>
              </div>
            </div>

            {/* Chat Interface at the bottom */}
            <div className="mt-auto pt-6">
              <ChatInterface 
                portfolioData={portfolioData?.portfolioData} 
                userPreferences={portfolioData?.userPreferences}
                onPortfolioUpdate={handlePortfolioUpdate} 
              />
            </div>
          </div>
        );
      default:
        return <p>An unexpected error occurred.</p>;
    }
  };

  // Different layout for results vs. wizard screens
  const pageContainerClass = currentStep === 'results'
    ? "w-full min-h-screen py-8 px-4 flex flex-col items-center overflow-auto" // Scrollable, no bg for results
    : "w-full h-screen overflow-hidden clouds-bg py-4 px-4 flex flex-col items-center justify-center"; // Fixed height, cloud bg, reduced padding for wizard
    
  return (
    <div className={pageContainerClass}>
      {currentStep !== 'welcome' && (
        <h1 className="text-3xl font-bold text-white drop-shadow-sm mb-2 text-center">
          Paige, your AI-powered Wealth Advisor
        </h1>
      )}
      {currentStep !== 'welcome' && currentStep !== 'results' && (
        <Progress value={calculateProgress()} className="w-full max-w-md mx-auto mb-4" />
      )}

      {/* The Card component rendered by renderStepContent will use mx-auto for centering */}
      {renderStepContent()}
    </div>
  );
}