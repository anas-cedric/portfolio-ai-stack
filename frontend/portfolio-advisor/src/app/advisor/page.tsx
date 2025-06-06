'use client';

import { useState, useEffect } from 'react';
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
import { Loader2 } from 'lucide-react';
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
const TOTAL_STEPS = STEPS.length - 1;

export default function AdvisorPage() {
  const [portfolioData, setPortfolioData] = useState<PortfolioState>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [userAge, setUserAge] = useState<number | ''>('');
  const [firstName, setFirstName] = useState<string>('');
  const [lastName, setLastName] = useState<string>('');
  const [birthday, setBirthday] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);


  const handleStart = () => {
    // Clear any contaminated state when starting fresh
    setUserAnswers({});
    setError(null);
    setCurrentStep('stepOne');
  };

  const handleWizardComplete = async (answers: Record<string, string>) => {
    console.log('=== DEBUGGING WIZARD DATA FLOW ===');
    console.log('Raw answers received from ProfileWizard:', answers);
    console.log('Current state - userAge:', userAge, 'type:', typeof userAge);
    console.log('Current state - firstName:', firstName);
    console.log('Current state - lastName:', lastName);
    console.log('Current state - birthday:', birthday);
    
    setUserAnswers(answers);
    
    // Since we already have age from the birthday calculation, proceed to generate portfolio
    setIsLoading(true);
    setError(null);
    
    try {
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'test_api_key_for_development';
      
      // Convert ProfileWizard answers (which should only be risk questions) to expected format
      const riskAnswers: Record<string, string> = {};
      for (const key in answers) {
        console.log(`Processing answer key: "${key}", value: "${answers[key]}"`);
        // ProfileWizard uses question IDs like "1", "2", "3"... "13"
        if (/^\d+$/.test(key)) { // Only include numeric question IDs
          riskAnswers[`q${key}`] = answers[key];
        } else {
          console.warn(`Unexpected non-numeric key in answers: "${key}" with value "${answers[key]}"`);
        }
      }
      
      console.log('Processed risk answers:', riskAnswers);
      
      // Ensure age is a number or undefined
      const ageToSend = (typeof userAge === 'number' && userAge > 0) ? userAge : undefined;
      
      const payload = {
        answers: riskAnswers,
        age: ageToSend,
        firstName: firstName || undefined,
        lastName: lastName || undefined,
        birthday: birthday || undefined
      };
      console.log("Final payload being sent to backend:", JSON.stringify(payload, null, 2));

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
        setPortfolioData(response.data);
        setCurrentStep('results');
        setError(null); 
      } else {
        setError("Failed to generate portfolio. Received unexpected data from the server.");
      }
      setIsLoading(false);
      
    } catch (error) {
      console.error('Error generating portfolio:', error);
      setError('Failed to generate portfolio. Please try again.');
      setIsLoading(false);
    }
  };

  const handleAgeSubmit = async () => {
    if (!firstName.trim() || !lastName.trim() || !birthday) {
      setError('Please enter your first name, last name, and birthday.');
      return;
    }

    // Calculate age from birthday
    const today = new Date();
    const birthDate = new Date(birthday);
    let calculatedAge = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    // Adjust age if birthday hasn't occurred this year yet
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      calculatedAge--;
    }

    // Set the calculated age
    setUserAge(calculatedAge);

    setIsLoading(true);
    setError(null);
    try {
      // Personal data is stored in separate state variables, not in userAnswers
      // Proceed to questionnaire
      setCurrentStep('questionnaire');
      setIsLoading(false);
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

  const handlePortfolioUpdate = (updatedPortfolioResponse: PortfolioResponse) => {
    console.log("AdvisorPage: Received updated portfolio data", updatedPortfolioResponse);
    setPortfolioData(updatedPortfolioResponse); 
  };

  const handleStartOver = () => {
    // Complete state reset
    setPortfolioData(null);
    setError(null);
    setUserAnswers({});
    setUserAge('');
    setFirstName('');
    setLastName('');
    setBirthday('');
    setCurrentStep('welcome');
    setIsLoading(false);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <div className="relative w-full h-screen flex items-center justify-center">
            {/* Glassmorphism Form Card */}
            <div className="relative w-[488px] h-[374px] bg-white/12 backdrop-blur-[60px] border border-white/8 rounded-[24px] p-10 flex flex-col gap-20">
              {/* Logo Container */}
              <div className="relative w-[77px] h-[26px] border border-white rounded-full flex items-center justify-center">
                {/* Paige Logo Text */}
                <span className="text-[14px] leading-[16px] font-normal text-white tracking-[0.08em] uppercase font-inter">
  Paige<span className="align-super text-[10px] ml-1">&reg;</span>
</span>
              </div>

              {/* Content Container */}
              <div className="flex flex-col gap-7">
                {/* Title Container */}
                <div className="flex flex-col gap-3">
                  <h1 className="text-[36px] leading-[44px] font-medium text-white font-inter-display">
                    Welcome to Paige
                  </h1>
                  <p className="text-[16px] leading-[24px] font-normal text-white/80 font-inter">
                    Your AI-powered wealth advisor. Let's get started by understanding your risk tolerance.
                  </p>
                </div>

                {/* Button */}
                <button 
                  onClick={handleStart}
                  className="w-full h-14 bg-white rounded-full flex items-center justify-between px-8 py-4 group hover:bg-white/95 transition-all duration-200"
                >
                  <span className="text-[16px] leading-[24px] font-medium text-[#00121F] font-inter mx-auto">
                    Start Questionnaire
                  </span>
                  <span className="flex items-center justify-center w-7 h-7 ml-2">
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="14" cy="14" r="14" fill="#00121F"/>
    <path d="M10 14H18" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M15 11L18 14L15 17" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
</span>
                </button>
              </div>
            </div>

            {/* Copyright Footer */}
            <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
              <p className="text-[12px] leading-[18px] font-normal text-white/80 font-inter">
                2025 Paige. All Rights Reserved.
              </p>
            </div>
          </div>
        );
      case 'stepOne':
      return (
        <div className="relative w-full h-screen flex items-center justify-center">
          {/* Glassmorphism Card */}
          <div className="relative w-[1440px] h-[800px] bg-transparent rounded-[40px] flex items-center justify-center overflow-hidden">
            {/* Glassmorphism Form */}
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[488px] h-[594px] bg-white/12 border border-white/8 rounded-[24px] backdrop-blur-[60px] flex flex-col items-start p-[40px] gap-[80px] z-10" style={{ boxSizing: 'border-box' }}>
              {/* Top bar with logo */}
              <div className="flex flex-row items-center gap-[80px] w-[408px] h-[26px] p-0" style={{ boxSizing: 'border-box' }}>
                <div className="relative w-[77px] h-[26px] border border-white rounded-full flex items-center justify-center">
                  <span className="text-[14px] leading-[16px] font-normal text-white tracking-[0.08em] uppercase font-inter">
                    Paige<span className="align-super text-[10px] ml-1">&reg;</span>
                  </span>
                </div>
                {/* (Optional: Progress bar, if needed) */}
              </div>
              {/* Form Content */}
              <div className="flex flex-col gap-[28px] w-[408px] items-start">
                {/* Title Container */}
                <div className="flex flex-col gap-3">
                  <h1 className="text-[36px] leading-[44px] font-medium text-white font-inter-display w-[408px]">
                    Tell us about yourself
                  </h1>
                  <p className="text-[16px] leading-[24px] font-normal text-white/80 font-inter w-[408px]">
                    Please enter your details so we can tailor the portfolio allocation.
                  </p>
                </div>
                {/* Inputs */}
                <div className="flex flex-col gap-[12px] w-[408px]">
                  {/* First Name */}
                  <div className="flex flex-col gap-[8px] w-[408px]">
                    <label htmlFor="firstName" className="text-[12px] leading-[18px] text-white/60 font-inter w-[360px]">First Name</label>
                    <div className="flex flex-row items-center bg-white/30 rounded-[99px] w-[408px] h-[56px] min-h-[56px] max-h-[56px] px-6 py-4 gap-[16px]">
                      <input
                        id="firstName"
                        type="text"
                        className="bg-transparent text-white w-full border-none outline-none text-[16px] leading-[24px] font-inter placeholder:text-white/60"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="Enter your first name"
                      />
                    </div>
                  </div>
                  {/* Last Name */}
                  <div className="flex flex-col gap-[8px] w-[408px]">
                    <label htmlFor="lastName" className="text-[12px] leading-[18px] text-white/60 font-inter w-[360px]">Last Name</label>
                    <div className="flex flex-row items-center bg-white/30 rounded-[99px] w-[408px] h-[56px] min-h-[56px] max-h-[56px] px-6 py-4 gap-[16px]">
                      <input
                        id="lastName"
                        type="text"
                        className="bg-transparent text-white w-full border-none outline-none text-[16px] leading-[24px] font-inter placeholder:text-white/60"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Enter your last name"
                      />
                    </div>
                  </div>
                  {/* Birthday */}
                  <div className="flex flex-col gap-[8px] w-[408px]">
                    <label htmlFor="birthday" className="text-[12px] leading-[18px] text-white/60 font-inter w-[360px]">Birthday</label>
                    <div className="flex flex-row items-center bg-white/30 rounded-[99px] w-[408px] h-[56px] min-h-[56px] max-h-[56px] px-6 py-4 gap-[16px]">
                      <input
                        id="birthday"
                        type="date"
                        className="bg-transparent text-white w-full border-none outline-none text-[16px] leading-[24px] font-inter placeholder:text-white/60"
                        value={birthday}
                        onChange={(e) => setBirthday(e.target.value)}
                        placeholder="Enter your birthday"
                      />
                    </div>
                  </div>
                </div>
                {error && (
                  <p className="text-red-500 text-sm text-center">{error}</p>
                )}
                {/* Button Group */}
                <div className="flex flex-row gap-6 mt-6">
                  <button
                    onClick={handleAgeSubmit}
                    className="flex flex-row items-center justify-between w-[408px] h-[56px] min-h-[56px] max-h-[56px] px-[32px] pr-[14px] bg-white rounded-full font-inter font-medium text-[16px] leading-[24px] text-[#00121F] hover:bg-white/90 transition-all duration-200 shadow-md gap-[12px]"
                  >
                    <span className="mx-auto text-[16px] leading-[24px] font-medium text-[#00121F] font-inter">
                      Continue
                    </span>
                    <span className="flex items-center justify-center w-7 h-7 ml-2">
                      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="14" cy="14" r="14" fill="#00121F"/>
  <path d="M10 14H18" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  <path d="M15 11L18 14L15 17" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
</svg>
                    </span>
                  </button>
                </div>
              </div>
              
            </div>
          </div>
          {/* Copyright Footer for Step One */}
          <div className="w-full flex justify-center mt-8 absolute left-0" style={{ bottom: 24 }}>
            <p className="text-[12px] leading-[18px] font-normal text-white/80 font-inter">
              2025 Paige. All Rights Reserved.
            </p>
          </div>
        </div>
      );
    case 'questionnaire':
        return (
          <ProfileWizard
            questions={RISK_QUESTIONS}
            onComplete={handleWizardComplete}
          />
        );
      case 'results':
        return portfolioData?.portfolioData ? (
          <PortfolioAllocationPage 
            portfolioData={portfolioData.portfolioData}
            userPreferences={{
              ...portfolioData.userPreferences,
              firstName: firstName || portfolioData.userPreferences?.firstName
            }}
            onApprove={() => console.log('Portfolio approved!')}
            onPortfolioUpdate={handlePortfolioUpdate}
            onStartOver={handleStartOver}
          />
        ) : (
          <div className="w-full min-h-screen flex items-center justify-center bg-white">
            <p className="text-lg text-gray-600">Loading portfolio data...</p>
          </div>
        );
      default:
        return <p>An unexpected error occurred.</p>;
    }
  };

  // Different layout for results vs. wizard screens
  const pageContainerClass = currentStep === 'results'
    ? "w-full h-screen overflow-hidden" // Fixed height for results page
    : "w-full h-screen overflow-hidden clouds-bg py-4 px-4 flex flex-col items-center justify-center"; // Fixed height, cloud bg, reduced padding for wizard
    
  return (
    <div className={pageContainerClass}>
      {/* The Card component rendered by renderStepContent will use mx-auto for centering */}
      {renderStepContent()}
    </div>
  );
}