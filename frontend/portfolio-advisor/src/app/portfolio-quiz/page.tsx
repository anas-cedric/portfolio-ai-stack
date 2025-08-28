'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import { useUserProfile } from "@/contexts/UserContext";
import axios from 'axios';
import Link from 'next/link';
import PortfolioResults from '@/components/PortfolioResults';
import ChatInterface from '@/components/ChatInterface';
import ProfileWizard from '@/components/ProfileWizard';
import AssetListItem from '@/components/AssetListItem';
import PortfolioAllocationPage from '@/components/PortfolioAllocationPage';
import { RISK_QUESTIONS } from '@/lib/constants';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Loader2, ArrowLeft } from 'lucide-react';
import { PortfolioResponse, PortfolioData, UserProfile } from '@/lib/types';
import AllocationSidebar from '@/components/AllocationSidebar';

import dynamic from 'next/dynamic';
const PortfolioDonutChart = dynamic(() => import('@/components/PortfolioDonutChart'), {
  ssr: false,
  loading: () => <div className="w-full h-[400px] flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-white" /> <p className="text-white ml-2">Loading Chart...</p></div>,
});

type PortfolioState = PortfolioResponse | null;
type Step = 'welcome' | 'stepOne' | 'questionnaire' | 'results';
const STEPS: Step[] = ['welcome', 'stepOne', 'questionnaire', 'results'];

export default function PortfolioQuizPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading, getAccessToken } = useKindeBrowserClient();
  const { updateProfile } = useUserProfile();
  const [portfolioData, setPortfolioData] = useState<PortfolioState>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [userAge, setUserAge] = useState<number | ''>('');
  const [firstName, setFirstName] = useState<string>('');
  const [lastName, setLastName] = useState<string>('');
  const [birthday, setBirthday] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/api/auth/login');
    }
  }, [user, isAuthLoading, router]);

  // Pre-populate user info from Kinde if available
  useEffect(() => {
    if (user) {
      if (user.given_name) setFirstName(user.given_name);
      if (user.family_name) setLastName(user.family_name);
      if (user.email && !firstName && !lastName) {
        // Fallback: use email prefix as first name if no other name available
        const emailPrefix = user.email.split('@')[0];
        setFirstName(emailPrefix);
      }
    }
  }, [user, firstName, lastName]);

  // Show loading while checking auth
  if (isAuthLoading) {
    return (
      <div className="w-full h-screen flex items-center justify-center clouds-bg">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!user) {
    return null;
  }

  const handleStart = () => {
    setCurrentStep('stepOne');
  };

  const handleWizardComplete = async (answers: Record<string, string>) => {
    console.log('Wizard completed with answers:', answers);
    setUserAnswers(answers);
    setCurrentStep('questionnaire');
  };

  const handlePersonalInfoSubmit = () => {
    if (!firstName || !lastName || !birthday || userAge === '') {
      setError('Please fill in all fields');
      return;
    }

    const today = new Date();
    const birthDate = new Date(birthday);
    const calculatedAge = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      setUserAge(calculatedAge - 1);
    } else {
      setUserAge(calculatedAge);
    }

    // ✅ GOOD: Store user data in context for app-wide access
    updateProfile({
      age: typeof userAge === 'number' ? userAge : calculatedAge,
      firstName,
      lastName,
      birthday
    });

    setCurrentStep('questionnaire');
  };

  const handleQuestionnaireComplete = async (answers: Record<string, string>) => {
    if (!user?.id) {
      setError('Authentication error. Please try again.');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const accessToken = await getAccessToken();
      
      const payload = {
        answers: { ...userAnswers, ...answers, age: userAge.toString() },
        firstName,
        lastName, 
        birthday,
        age: userAge.toString(),
        user_id: user.id
      };

      console.log('Sending payload:', payload);

      const response = await axios.post('/api/generate-portfolio-from-wizard', payload, {
        headers: {
          'Authorization': accessToken ? `Bearer ${accessToken}` : undefined,
          'Content-Type': 'application/json'
        }
      });

      console.log('Portfolio generated successfully:', response.data);
      setPortfolioData(response.data);
      
      // ✅ GOOD: Mark portfolio as generated in context
      updateProfile({
        portfolioGenerated: true,
        riskProfile: response.data.risk_bucket || 'unknown'
      });
      
      setCurrentStep('results');
    } catch (error) {
      console.error('Error generating portfolio:', error);
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        setError(`Error: ${error.response.data.detail}`);
      } else {
        setError('Failed to generate portfolio. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleProceedToOnboarding = () => {
    router.push('/onboarding');
  };

  const currentStepIndex = STEPS.indexOf(currentStep);
  const progress = ((currentStepIndex) / (STEPS.length - 1)) * 100;

  const pageContainerClass = currentStep === 'results'
    ? "w-full h-screen overflow-hidden"
    : "w-full h-screen overflow-hidden clouds-bg py-4 px-4 flex flex-col items-center justify-center";
    
  return (
    <div className={pageContainerClass}>
      {currentStep !== 'results' && (
        <div className="relative w-full max-w-4xl mx-auto">
          {/* Header with User Info and Logout */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-4">
              {currentStep !== 'welcome' && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    const currentIndex = STEPS.indexOf(currentStep);
                    if (currentIndex > 0) {
                      setCurrentStep(STEPS[currentIndex - 1]);
                    }
                  }}
                  className="glass-card"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
              )}
              <div className="text-sm text-gray-700">
                Welcome, {user.given_name || user.email}
              </div>
            </div>
            <Link href="/api/auth/logout">
              <Button variant="outline" size="sm" className="glass-card">
                Sign Out
              </Button>
            </Link>
          </div>

          {/* Progress Bar */}
          {currentStep !== 'welcome' && (
            <div className="glass-card p-4 mb-8">
              <div className="flex justify-between text-sm text-gray-700 mb-2">
                <span>Portfolio Generation</span>
                <span>{Math.round(progress)}% Complete</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {/* Main Content Card */}
          <div className="glass-card-questionnaire p-8">
            {currentStep === 'welcome' && (
              <div className="text-center space-y-6">
                <div className="space-y-4">
                  <h1 className="text-4xl font-bold text-gray-900">
                    Let's Build Your Perfect Portfolio
                  </h1>
                  <p className="text-xl text-gray-700">
                    Answer a few questions about your investment goals and risk tolerance, 
                    and we'll create a personalized portfolio just for you.
                  </p>
                </div>
                
                <div className="bg-white/50 backdrop-blur-sm rounded-xl p-6 space-y-3">
                  <h3 className="font-semibold text-gray-900">What you'll get:</h3>
                  <ul className="text-left space-y-2 text-gray-700">
                    <li className="flex items-center">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
                      Personalized asset allocation based on your risk profile
                    </li>
                    <li className="flex items-center">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
                      Diversified portfolio across multiple asset classes
                    </li>
                    <li className="flex items-center">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
                      Professional-grade investment recommendations
                    </li>
                  </ul>
                </div>

                <Button 
                  onClick={handleStart} 
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-xl"
                >
                  Get Started
                </Button>
              </div>
            )}

            {currentStep === 'stepOne' && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <h2 className="text-3xl font-bold text-gray-900">Personal Information</h2>
                  <p className="text-gray-700">Help us personalize your portfolio recommendations</p>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                    <p className="text-red-600 text-sm">{error}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="firstName" className="text-gray-700 font-medium">First Name</Label>
                    <Input
                      id="firstName"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="bg-white/70 border-white/80 focus:bg-white transition-all"
                      placeholder="Enter your first name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="lastName" className="text-gray-700 font-medium">Last Name</Label>
                    <Input
                      id="lastName"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="bg-white/70 border-white/80 focus:bg-white transition-all"
                      placeholder="Enter your last name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="birthday" className="text-gray-700 font-medium">Birthday</Label>
                    <Input
                      id="birthday"
                      type="date"
                      value={birthday}
                      onChange={(e) => setBirthday(e.target.value)}
                      className="bg-white/70 border-white/80 focus:bg-white transition-all"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="age" className="text-gray-700 font-medium">Age</Label>
                    <Input
                      id="age"
                      type="number"
                      min="18"
                      max="100"
                      value={userAge}
                      onChange={(e) => setUserAge(e.target.value === '' ? '' : parseInt(e.target.value))}
                      className="bg-white/70 border-white/80 focus:bg-white transition-all"
                      placeholder="Enter your age"
                    />
                  </div>
                </div>

                <Button 
                  onClick={handlePersonalInfoSubmit}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl"
                >
                  Continue to Questions
                </Button>
              </div>
            )}

            {currentStep === 'questionnaire' && (
              <ProfileWizard
                questions={RISK_QUESTIONS}
                onComplete={handleQuestionnaireComplete}
                isLoading={isLoading}
              />
            )}
          </div>
        </div>
      )}

      {currentStep === 'results' && portfolioData && (
        <PortfolioAllocationPage 
          portfolioData={portfolioData}
          userPreferences={{ 
            firstName, 
            lastName, 
            age: userAge, 
            riskAnswers: userAnswers 
          }}
          onProceedToOnboarding={handleProceedToOnboarding}
        />
      )}
    </div>
  );
}