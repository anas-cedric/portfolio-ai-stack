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

  // Dynamically build asset & chart data from backend portfolio when available
  const dynamicAssetData = portfolioData?.portfolioData?.holdings?.map((h, index) => ({
    name: h.name || h.ticker,
    ticker: h.ticker,
    weight: (h.percentage ?? 0) / 100, // convert percent to fraction 0-1
    icon: 'V',
    color: sampleChartColors[index % sampleChartColors.length],
  }));

  const assetDataToDisplay = dynamicAssetData && dynamicAssetData.length > 0 ? dynamicAssetData : [];

  const donutData = assetDataToDisplay.map(a => ({
    name: a.ticker,
    value: a.weight * 100,
    color: a.color!,
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
          <Card className="w-full max-w-lg mx-auto glass-card">
            <CardHeader>
              <CardTitle className="text-center text-3xl font-bold text-white drop-shadow-lg mb-2">Welcome to Paige</CardTitle>
              <p className="text-center text-lg text-white/90 drop-shadow-sm font-medium">
                Your AI-powered wealth advisor. Let's get started by understanding your risk tolerance.
              </p>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Button onClick={handleStart} className="bg-white/90 text-blue-700 hover:bg-white font-semibold px-8 py-3 text-lg rounded-xl shadow-lg backdrop-blur-sm border border-white/50">Start Questionnaire</Button>
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
          <Card className="w-full max-w-md mx-auto glass-card">
            <CardHeader>
              <CardTitle className="text-center text-2xl font-bold text-white drop-shadow-lg mb-2">Tell us about yourself</CardTitle>
              <p className="text-center text-lg text-white/90 drop-shadow-sm font-medium">Please enter your age so we can tailor the portfolio allocation.</p>
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
                    className="bg-white/20 text-white hover:bg-white/30 border-white/40 font-semibold px-6 py-2 rounded-xl"
                    onClick={() => setCurrentStep('questionnaire')}
                  >
                    Back
                  </Button>
                  <Button 
                    onClick={handleAgeSubmit}
                    disabled={!userAge}
                    className="bg-white/90 text-blue-700 hover:bg-white font-semibold px-6 py-2 rounded-xl shadow-lg backdrop-blur-sm border border-white/50"
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
          <div className="w-full min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6"> 
            <div className="max-w-7xl mx-auto">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h1 className="text-4xl font-bold text-gray-900 mb-2">Your Portfolio Recommendation</h1>
                  <p className="text-lg text-gray-600">Designed specifically for your risk profile and goals</p>
                </div>
                <Button variant="outline" className="bg-white shadow-sm hover:shadow-md" onClick={() => { setCurrentStep('welcome'); setPortfolioData(null); }}>
                  Start Over
                </Button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Portfolio Details */}
                <div className="lg:col-span-2 space-y-6">
                  <Card className="bg-white shadow-lg border-0 rounded-2xl p-6">
                    <CardHeader className="pb-4">
                      <CardTitle className="text-2xl font-bold text-gray-900 mb-2">Portfolio Details</CardTitle>
                      <p className="text-gray-600 leading-relaxed">Based on your risk profile, I've designed this diversified portfolio to help you achieve your financial goals while managing risk appropriately.</p>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4 py-3 border-b border-gray-100 font-semibold text-gray-700">
                          <div>Asset</div>
                          <div className="text-right">Allocation</div>
                        </div>
                        {assetDataToDisplay.map((asset, index) => (
                          <AssetListItem key={index} asset={asset} />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Right Column: Chart Visualization */}
                <div className="lg:col-span-1">
                  <Card className="bg-gradient-to-br from-slate-900 to-slate-800 shadow-xl border-0 rounded-2xl overflow-hidden">
                    <CardHeader className="pb-4">
                      <CardTitle className="text-2xl font-bold text-white mb-2">Portfolio Allocation</CardTitle>
                      <p className="text-slate-300 text-sm">Visual breakdown of your investment distribution</p>
                    </CardHeader>
                    <CardContent className="h-[400px] flex items-center justify-center">
                      <PortfolioDonutChart data={donutData} />
                    </CardContent>
                    <CardFooter className="pt-0">
                      <div className="w-full">
                        <h4 className="text-white font-semibold mb-3">Legend</h4>
                        <div className="grid gap-2">
                          {donutData.map((entry, idx) => (
                            <div key={idx} className="flex items-center justify-between bg-white/10 rounded-lg p-2 backdrop-blur-sm">
                              <div className="flex items-center">
                                <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: entry.color }}></span>
                                <span className="text-white text-sm font-medium">{entry.name}</span>
                              </div>
                              <span className="text-white font-semibold">{entry.value.toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardFooter>
                  </Card>
                </div>
              </div>

              {/* Chat Interface */}
              <div className="mt-8">
                <Card className="bg-white shadow-lg border-0 rounded-2xl overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-100">
                    <CardTitle className="text-xl font-bold text-gray-900">Chat with Paige</CardTitle>
                    <p className="text-gray-600 text-sm">Ask questions or request adjustments to your portfolio</p>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ChatInterface 
                      portfolioData={portfolioData?.portfolioData} 
                      userPreferences={portfolioData?.userPreferences}
                      onPortfolioUpdate={handlePortfolioUpdate} 
                    />
                  </CardContent>
                </Card>
              </div>
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