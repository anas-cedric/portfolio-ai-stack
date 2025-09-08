'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useKindeBrowserClient } from "@kinde-oss/kinde-auth-nextjs";
import { useUserProfile } from "@/contexts/UserContext";
import axios from 'axios';
import Image from 'next/image';
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

function PortfolioQuizContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
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
  // Birth date selection (more intuitive than browser date picker)
  const [birthMonth, setBirthMonth] = useState<string>('');
  const [birthDay, setBirthDay] = useState<string>('');
  const [birthYear, setBirthYear] = useState<string>(String(new Date().getFullYear() - 30));
  const [isLoading, setIsLoading] = useState(false);

  // Redirect to login if not authenticated and handle step parameter
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push('/api/auth/login');
      return;
    }

    // Check for step parameter in URL (from auth redirect)
    const stepParam = searchParams.get('step');
    if (stepParam && STEPS.includes(stepParam as Step)) {
      setCurrentStep(stepParam as Step);
    }
  }, [user, isAuthLoading, router, searchParams]);

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

  // Helper to compute age from ISO date (YYYY-MM-DD)
  const calculateAgeFromDateString = (dateStr: string): number => {
    const today = new Date();
    const birthDate = new Date(dateStr);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  // Helpers for birthday selectors
  const getDaysInMonth = (year: number, month: number): number => {
    return new Date(year, month, 0).getDate(); // month is 1-based here
  };
  const currentYear = new Date().getFullYear();
  const yearOptions: number[] = Array.from({ length: 83 }, (_, i) => (currentYear - 18) - i); // 18..100
  const monthOptions = [
    { value: '01', label: 'January' },
    { value: '02', label: 'February' },
    { value: '03', label: 'March' },
    { value: '04', label: 'April' },
    { value: '05', label: 'May' },
    { value: '06', label: 'June' },
    { value: '07', label: 'July' },
    { value: '08', label: 'August' },
    { value: '09', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' },
  ];
  const maxDays = birthYear && birthMonth ? getDaysInMonth(parseInt(birthYear), parseInt(birthMonth)) : 31;
  const dayOptions: number[] = Array.from({ length: maxDays }, (_, i) => i + 1);

  const handlePersonalInfoSubmit = () => {
    if (!firstName || !lastName || !birthYear || !birthMonth || !birthDay) {
      setError('Please fill in all fields');
      return;
    }

    const birthdayStr = `${birthYear}-${String(birthMonth).padStart(2, '0')}-${String(birthDay).padStart(2, '0')}`;
    const calculatedAge = calculateAgeFromDateString(birthdayStr);

    setBirthday(birthdayStr);
    setUserAge(calculatedAge);

    // Store user data in context for app-wide access
    updateProfile({
      age: calculatedAge,
      firstName,
      lastName,
      birthday: birthdayStr
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
      
      const derivedAge = typeof userAge === 'number'
        ? userAge
        : (birthday ? calculateAgeFromDateString(birthday) : undefined);

      const payload = {
        answers: { ...userAnswers, ...answers, age: derivedAge !== undefined ? String(derivedAge) : '' },
        firstName,
        lastName, 
        birthday,
        age: derivedAge !== undefined ? String(derivedAge) : '',
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

      // ✅ NEW: Mark onboarding state as quiz_completed on the server
      try {
        const quizPayload = {
          quiz_data: { ...userAnswers, ...answers, age: userAge },
          portfolio_preferences: {
            risk_bucket: response.data?.risk_bucket,
            risk_score: typeof response.data?.risk_score === 'number' ? response.data.risk_score : undefined,
            target_weights: response.data?.weights || response.data?.target_weights,
          },
        };
        await fetch('/api/onboarding/quiz-completed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(quizPayload),
        });
      } catch (e) {
        console.warn('Failed to persist quiz completion state:', e);
      }
      
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
    router.push('/dashboard');
  };

  const currentStepIndex = STEPS.indexOf(currentStep);
  const progress = ((currentStepIndex) / (STEPS.length - 1)) * 100;

  const pageContainerClass = currentStep === 'results'
    ? "w-full h-screen overflow-hidden"
    : "w-full h-screen overflow-hidden clouds-bg py-4 px-4 flex flex-col items-center justify-center";
    
  return (
    <div className={pageContainerClass}>
      {/* Top-right auth controls visible across steps */}
      <div className="absolute top-8 right-8 flex items-center space-x-4">
        {user ? (
          <>
            <span className="text-white/80 text-sm">
              {user.given_name || user.email}
            </span>
            <button
              onClick={() => { window.location.href = '/api/auth/logout'; }}
              className="text-white/60 hover:text-white/80 text-sm transition-colors"
            >
              Sign Out
            </button>
          </>
        ) : (
          <>
            <Link href="/api/auth/login">
              <button className="text-white/80 hover:text-white text-sm font-medium transition-colors">
                Sign In
              </button>
            </Link>
            <Link href="/api/auth/register">
              <button className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 backdrop-blur-sm border border-white/20">
                Get Started
              </button>
            </Link>
          </>
        )}
      </div>
      {/* Top-left logo for welcome/stepOne to match home page */}
      {(currentStep === 'welcome' || currentStep === 'stepOne') && (
        <div className="absolute top-8 left-8 flex items-center space-x-3">
          <Image 
            src="/images/cedric-logo-new.png" 
            alt="Cedric" 
            width={120} 
            height={120}
          />
        </div>
      )}

      {currentStep !== 'results' && currentStep !== 'questionnaire' && (
        <div 
          className="flex flex-col items-start gap-12 w-[616px] bg-white/12 border border-white/8 rounded-[24px] backdrop-blur-[60px] p-10"
          style={{
            boxSizing: 'border-box'
          }}
        >
          {/* Card content begins */}

          {/* Main Content */}
          <div className="flex flex-col items-center w-full">
            {currentStep === 'welcome' && (
              <div className="text-center space-y-8 w-full">
                <div className="space-y-4">
                  <h2 className="text-3xl font-bold text-white">
                    Let's Build Your Perfect Portfolio
                  </h2>
                  <p className="text-lg text-white/80 max-w-md mx-auto">
                    Answer a few questions about your investment goals and risk tolerance, 
                    and we'll create a personalized portfolio just for you.
                  </p>
                </div>
                
                <div className="bg-white/10 border border-white/10 rounded-[16px] p-6 space-y-4">
                  <h3 className="font-semibold text-white mb-4">What you'll get:</h3>
                  <ul className="text-left space-y-3 text-white/80">
                    <li className="flex items-center">
                      <span className="w-2 h-2 bg-white rounded-full mr-3"></span>
                      Personalized asset allocation based on your risk profile
                    </li>
                    <li className="flex items-center">
                      <span className="w-2 h-2 bg-white rounded-full mr-3"></span>
                      Diversified portfolio across multiple asset classes
                    </li>
                    <li className="flex items-center">
                      <span className="w-2 h-2 bg-white rounded-full mr-3"></span>
                      Professional-grade investment recommendations
                    </li>
                  </ul>
                </div>

                <button 
                  onClick={handleStart} 
                  className="w-full max-w-sm mx-auto px-8 py-4 bg-white rounded-full transition-all duration-200 hover:bg-white/90"
                >
                  <span className="text-[16px] leading-[24px] font-medium text-slate-900">
                    Get Started
                  </span>
                </button>
              </div>
            )}

            {currentStep === 'stepOne' && (
              <div className="w-full space-y-6">
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold text-white">Personal Information</h2>
                  <p className="text-white/80">Help us personalize your portfolio recommendations</p>
                </div>

                {error && (
                  <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
                    <p className="text-red-200 text-sm">{error}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="firstName" className="text-white/80 text-sm font-medium">First Name</label>
                    <input
                      id="firstName"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      placeholder="Enter your first name"
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder:text-white/40 focus:bg-white/15 focus:border-white/30 focus:outline-none transition-all"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="lastName" className="text-white/80 text-sm font-medium">Last Name</label>
                    <input
                      id="lastName"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      placeholder="Enter your last name"
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder:text-white/40 focus:bg-white/15 focus:border-white/30 focus:outline-none transition-all"
                    />
                  </div>

                  {/* Birthday selectors across full width */}
                  <div className="space-y-2 md:col-span-2">
                    <label className="text-white/80 text-sm font-medium">Birthday</label>
                    <div className="grid grid-cols-3 gap-3">
                      {/* Month */}
                      <select
                        aria-label="Birth month"
                        value={birthMonth}
                        onChange={(e) => {
                          const val = e.target.value;
                          setBirthMonth(val);
                          if (birthYear && birthDay) {
                            const daysLimit = getDaysInMonth(parseInt(birthYear), parseInt(val));
                            if (parseInt(birthDay) > daysLimit) setBirthDay('');
                          }
                        }}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:bg-white/15 focus:border-white/30 focus:outline-none transition-all"
                      >
                        <option value="" className="bg-slate-900 text-white/70">Month</option>
                        {monthOptions.map((m) => (
                          <option key={m.value} value={m.value} className="bg-slate-900 text-white">
                            {m.label}
                          </option>
                        ))}
                      </select>

                      {/* Day */}
                      <select
                        aria-label="Birth day"
                        value={birthDay}
                        onChange={(e) => setBirthDay(e.target.value)}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:bg-white/15 focus:border-white/30 focus:outline-none transition-all"
                      >
                        <option value="" className="bg-slate-900 text-white/70">Day</option>
                        {dayOptions.map((d) => (
                          <option key={d} value={String(d).padStart(2, '0')} className="bg-slate-900 text-white">
                            {d}
                          </option>
                        ))}
                      </select>

                      {/* Year */}
                      <select
                        aria-label="Birth year"
                        value={birthYear}
                        onChange={(e) => {
                          const val = e.target.value;
                          setBirthYear(val);
                          if (birthMonth && birthDay) {
                            const daysLimit = getDaysInMonth(parseInt(val), parseInt(birthMonth));
                            if (parseInt(birthDay) > daysLimit) setBirthDay('');
                          }
                        }}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:bg-white/15 focus:border-white/30 focus:outline-none transition-all"
                      >
                        <option value="" className="bg-slate-900 text-white/70">Year</option>
                        {yearOptions.map((y) => (
                          <option key={y} value={String(y)} className="bg-slate-900 text-white">
                            {y}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flex justify-between items-center pt-4">
                  <button 
                    onClick={() => setCurrentStep('welcome')}
                    className="px-6 py-3 bg-white/20 border border-white/30 rounded-full text-white font-medium hover:bg-white/30 transition-all"
                  >
                    Back
                  </button>
                  
                  <button 
                    onClick={handlePersonalInfoSubmit}
                    className="px-8 py-3 bg-white rounded-full text-slate-900 font-medium hover:bg-white/90 transition-all"
                  >
                    Continue to Questions
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {currentStep === 'questionnaire' && (
        <ProfileWizard
          questions={RISK_QUESTIONS}
          onComplete={handleQuestionnaireComplete}
          isLoading={isLoading}
        />
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
          onApprove={handleProceedToOnboarding}
          onProceedToOnboarding={handleProceedToOnboarding}
          user={user}
        />
      )}
    </div>
  );
}

export default function PortfolioQuizPage() {
  return (
    <Suspense fallback={
      <div className="w-full h-screen flex items-center justify-center clouds-bg">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-white">Loading...</p>
        </div>
      </div>
    }>
      <PortfolioQuizContent />
    </Suspense>
  );
}