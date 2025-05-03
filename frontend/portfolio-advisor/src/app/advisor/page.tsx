'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';
import PortfolioResults from '@/components/PortfolioResults';
import ChatInterface from '@/components/ChatInterface';
import ProfileWizard from '@/components/ProfileWizard';
import { RISK_QUESTIONS } from '@/lib/constants';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';
import { PortfolioResponse, PortfolioData, UserProfile } from '@/lib/types';

type PortfolioState = PortfolioResponse | null;

type Step = 'welcome' | 'questionnaire' | 'ageInput' | 'results';
const STEPS: Step[] = ['welcome', 'questionnaire', 'ageInput', 'results'];
const TOTAL_STEPS = STEPS.length - 1;

export default function AdvisorPage() {
  const [portfolioData, setPortfolioData] = useState<PortfolioState>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [userAge, setUserAge] = useState<number | ''>('');
  const [isLoading, setIsLoading] = useState(false);

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
    // Don't set portfolioData to null here, wait until success/reset

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'test_api_key_for_development';

      const payload = {
        answers: userAnswers,
        age: Number(userAge)
      };
      // Log the exact payload being sent
      console.log("Sending payload to backend:", JSON.stringify(payload, null, 2));

      const response = await axios.post(`${apiUrl}/api/generate-portfolio-from-wizard`, 
        payload, // Send the payload
        {
          headers: {
            'x-api-key': apiKey,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('API Response:', response.data);
      if (response.data) {
        // Store results and proceed after a delay
        setTimeout(() => {
          setPortfolioData(response.data);
          setCurrentStep('results');
          setError(null); // Clear any previous errors
          setIsLoading(false); // Stop loading indicator AFTER delay and state update
        }, 5000); // 5000 milliseconds = 5 seconds delay
      } else {
        setError("Failed to generate portfolio. Received unexpected data from the server.");
        setIsLoading(false); // Stop loading on unexpected data error
      }
    } catch (err: any) {
      console.error('API Error during age submit:', err);
      
      let displayError = "An unknown error occurred while generating the portfolio."; // Default

      const errorData = err.response?.data;
      // Check for FastAPI/Pydantic validation error structure
      if (errorData && Array.isArray(errorData.detail) && errorData.detail.length > 0 && errorData.detail[0].msg) {
        displayError = `Validation Error: ${errorData.detail[0].msg}`;
        // Optional: Add location info if needed: `(${errorData.detail[0].loc.join(' > ')})`
      } else if (typeof errorData?.detail === 'string') {
        // Use detail if it's just a string
        displayError = errorData.detail;
      } else if (err.message) {
        // Fallback to general error message if available
        displayError = err.message;
      }

      setError(displayError); // Ensure setError is always called with a string
      setIsLoading(false); // Stop loading indicator on error
    } finally {
      // Remove setIsLoading(false) from here to allow loading during setTimeout
      // setIsLoading(false);
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
    setPortfolioData(updatedPortfolioResponse); // Update the state with the new full structure
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
          <Card className="w-full max-w-lg mx-auto">
            <CardHeader>
              <CardTitle className="text-center text-2xl">Welcome to Paige</CardTitle>
              <p className="text-center text-sm text-muted-foreground pt-1">
                Your AI-powered wealth advisor. Let's get started by understanding your risk tolerance.
              </p>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Button onClick={handleStart}>Start Questionnaire</Button>
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
          <Card className="w-full max-w-md mx-auto">
            <CardHeader>
              <CardTitle className="text-center text-gray-800">Step 3 of 3: One Last Step</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* --- Conditional Rendering for Loading State --- */}
              {isLoading ? (
                <div className="flex flex-col items-center justify-center p-8 text-center min-h-[150px]"> 
                  <Loader2 className="h-12 w-12 animate-spin text-sky-600 mb-4" />
                  <p className="text-lg font-semibold text-gray-700">Paige is designing your portfolio...</p>
                  <p className="text-sm text-muted-foreground">This may take a moment.</p>
                </div>
              ) : (
                /* --- Show Form only when NOT loading --- */
                <>
                  <p className="text-center text-gray-600">
                    Please enter your age so we can tailor the portfolio allocation.
                  </p>
                  <div className="space-y-2">
                    <Label htmlFor="ageInput" className="text-gray-700">Your Age</Label>
                    <Input
                      id="ageInput"
                      type="number"
                      value={userAge}
                      onChange={(e) => {
                        const value = e.target.value;
                        // If input is empty, set state to empty string
                        // Otherwise, parse to number. If parsing fails (e.g., non-numeric input), 
                        // behavior might depend on browser, but often results in NaN. 
                        // We rely on the input type="number" for basic filtering.
                        setUserAge(value === '' ? '' : parseInt(value, 10));
                      }}
                      placeholder="Enter your age"
                      className="w-full"
                      min="18" // Optional: minimum age
                      max="100" // Optional: maximum age
                    />
                  </div>
                  {error && (
                    <p className="text-red-500 text-sm text-center">{error}</p>
                  )}
                </>
              )}
            </CardContent>
            {/* --- Render Footer only when NOT loading --- */}
            {!isLoading && (
              <CardFooter className="flex justify-center">
                <Button 
                  onClick={handleAgeSubmit}
                  disabled={!userAge} // Keep disabled logic
                >
                  Generate Portfolio
                </Button>
              </CardFooter>
            )}
          </Card>
        );
      case 'results':
        if (portfolioData) {
          return (
            <PortfolioResults
              portfolioData={portfolioData.portfolioData} // Revert to passing nested data
              userPreferences={portfolioData.userPreferences} // Revert to passing nested data
              onReset={handleReset}
              onPortfolioUpdate={handlePortfolioUpdate}
            />
          );
        }
        return <p>Loading results...</p>;
      default:
        return <p>An unexpected error occurred.</p>;
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      {currentStep !== 'welcome' && (
        <h1 className="text-3xl font-bold text-foreground mb-4 text-center">
          Paige, your AI-powered Wealth Advisor
        </h1>
      )}

      {currentStep !== 'welcome' && currentStep !== 'results' && (
        <div className="my-6">
          <Progress value={calculateProgress()} className="w-full" />
          <p className="text-sm text-muted-foreground text-center mt-2">
            Step {STEPS.indexOf(currentStep)} of {TOTAL_STEPS}
          </p>
        </div>
      )}

      {error && currentStep !== 'ageInput' && (
        <div className="bg-red-50 border border-red-200 text-destructive px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <div className="mt-8">
        {renderStepContent()}
      </div>
    </div>
  );
}