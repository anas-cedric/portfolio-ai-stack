'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react'; // For loading spinner

// Define the structure for each question
interface Question {
  id: string;
  text: string;
  options: { value: string; label: string }[];
}

// Define the 13 risk questions
const riskQuestions: Question[] = [
  {
    id: '1',
    text: 'In general, how would your best friend describe you as a risk taker?',
    options: [
      { value: 'a', label: 'A real gambler' },
      { value: 'b', label: 'Willing to take risks after completing adequate research' },
      { value: 'c', label: 'Cautious' },
      { value: 'd', label: 'A real risk avoider' },
    ],
  },
  {
    id: '2',
    text: 'You are on a TV game show and can choose one of the following; which would you take?',
    options: [
      { value: 'a', label: '$1,000 in cash' },
      { value: 'b', label: 'A 50% chance at winning $5,000' },
      { value: 'c', label: 'A 25% chance at winning $10,000' },
      { value: 'd', label: 'A 5% chance at winning $100,000' },
    ],
  },
  {
    id: '3',
    text: 'You have just finished saving for a once-in-a-lifetime vacation. Three weeks before you plan to leave, you lose your job. You would:',
    options: [
      { value: 'a', label: 'Cancel the vacation' },
      { value: 'b', label: 'Take a much more modest vacation' },
      { value: 'c', label: 'Go as scheduled, reasoning that you need the time to prepare for a job search' },
      { value: 'd', label: 'Extend your vacation, because this might be your last chance to go first-class' },
    ],
  },
   {
    id: '4',
    text: 'If you unexpectedly received $20,000 to invest, what would you do?',
    options: [
      { value: 'a', label: 'Deposit it in a bank account, money market account, or insured CD' },
      { value: 'b', label: 'Invest it in safe high-quality bonds or bond mutual funds' },
      { value: 'c', label: 'Invest it in stocks or stock mutual funds' },
    ],
  },
  {
    id: '5',
    text: 'In terms of experience, how comfortable are you investing in stocks or stock mutual funds?',
    options: [
      { value: 'a', label: 'Not at all comfortable' },
      { value: 'b', label: 'Somewhat comfortable' },
      { value: 'c', label: 'Very comfortable' },
    ],
  },
  {
    id: '6',
    text: 'When you think of the word ‘risk,’ which of the following words comes to mind first?',
    options: [
      { value: 'a', label: 'Loss' },
      { value: 'b', label: 'Uncertainty' },
      { value: 'c', label: 'Opportunity' },
      { value: 'd', label: 'Thrill' },
    ],
  },
  {
    id: '7',
    text: 'Some experts are predicting prices of assets such as gold, jewels, collectibles, and real estate to increase in value; bond prices may fall. Most of your investment assets are now in high-interest government bonds. What would you do?',
    options: [
      { value: 'a', label: 'Hold the bonds' },
      { value: 'b', label: 'Sell the bonds, put half the proceeds into money market accounts, and the other half into hard assets' },
      { value: 'c', label: 'Sell the bonds and put the total proceeds into hard assets' },
      { value: 'd', label: 'Sell the bonds, put all the money into hard assets, and borrow additional money to buy more' },
    ],
  },
  {
    id: '8',
    text: 'Given the best and worst case returns of the four investment choices below, which would you prefer?',
    options: [
      { value: 'a', label: '$200 gain best case; $0 gain/loss worst case' },
      { value: 'b', label: '$800 gain best case; $200 loss worst case' },
      { value: 'c', label: '$2,600 gain best case; $800 loss worst case' },
      { value: 'd', label: '$4,800 gain best case; $2,400 loss worst case' },
    ],
  },
   {
    id: '9',
    text: 'In addition to whatever you own, you have been given $1,000. You are now asked to choose between:',
    options: [
      { value: 'a', label: 'A sure gain of $500' },
      { value: 'b', label: 'A 50% chance to gain $1,000 and a 50% chance to gain nothing.' },
    ],
  },
  {
    id: '10',
    text: 'In addition to whatever you own, you have been given $2,000. You are now asked to choose between:',
    options: [
      { value: 'a', label: 'A sure loss of $500' },
      { value: 'b', label: 'A 50% chance to lose $1,000 and a 50% chance to lose nothing.' },
    ],
  },
  {
    id: '11',
    text: 'Suppose a relative left you an inheritance of $100,000, stipulating that you invest ALL the money in ONE of the following choices. Which one would you select?',
    options: [
      { value: 'a', label: 'A savings account or money market mutual fund' },
      { value: 'b', label: 'A mutual fund that owns stocks and bonds' },
      { value: 'c', label: 'A portfolio of 15 common stocks' },
      { value: 'd', label: 'Commodities like gold, silver, and oil' },
    ],
  },
  {
    id: '12',
    text: 'If you had to invest $20,000, which investment choice would you find most appealing?',
    options: [
      { value: 'a', label: '60% low-risk, 30% medium-risk, 10% high-risk' },
      { value: 'b', label: '30% low-risk, 40% medium-risk, 30% high-risk' },
      { value: 'c', label: '10% low-risk, 40% medium-risk, 50% high-risk' },
      { value: 'd', label: 'Evenly split across low-, medium-, and high-risk investments' },
    ],
  },
  {
    id: '13',
    text: 'Your friend is raising money to fund an exploratory gold-mining venture with a 20% chance of success and huge upside. How much would you invest?',
    options: [
      { value: 'a', label: 'Nothing' },
      { value: 'b', label: 'One month’s salary' },
      { value: 'c', label: 'Three months’ salary' },
      { value: 'd', label: 'Six months’ salary' },
    ],
  },
];

// Define the type for the answers state
interface Answers {
  [key: string]: string; // Question ID maps to selected option value ('a', 'b', etc.)
}

interface ProfileWizardProps {
  questions: Question[];
  onComplete: (answers: Answers) => void; // Changed signature: expects simple answers object
  isLoading?: boolean; // Optional loading state
}

const ProfileWizard: React.FC<ProfileWizardProps> = ({ 
  questions, 
  onComplete,
  isLoading = false
}) => {
  const [currentStep, setCurrentStep] = useState(0); // 0-based index for riskQuestions
  const [answers, setAnswers] = useState<Answers>({});

  const totalQuestions = questions.length;
  const currentQuestion = questions[currentStep];
  const progress = ((currentStep + 1) / totalQuestions) * 100;
  const isLastStep = currentStep === totalQuestions - 1;

  const handleOptionChange = (value: string) => {
    setAnswers((prevAnswers) => ({
      ...prevAnswers,
      [currentQuestion.id]: value,
    }));
  };

  const handleSubmit = () => { 
    console.log("Submitting answers from ProfileWizard:", answers); 
    onComplete(answers);
  };

  const handleNext = () => {
    if (currentStep < totalQuestions - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const isCurrentQuestionAnswered = answers[currentQuestion.id] !== undefined;

  return (
    <div 
      className="absolute flex flex-col items-start gap-12 w-[616px] h-[667px] bg-white/12 border border-white/8 rounded-[24px] backdrop-blur-[60px] p-10"
      style={{
        left: 'calc(50% - 616px/2)',
        top: 'calc(50% - 667px/2)',
        boxSizing: 'border-box'
      }}
    >
      {/* Top Section */}
      <div className="flex flex-row justify-between items-center w-[536px] h-[26px]">
        {/* Logo */}
        <div className="flex items-center">
          <Image 
            src="/images/cedric-logo-full.png" 
            alt="Cedric" 
            width={100} 
            height={32}
            className="opacity-90"
            style={{ mixBlendMode: 'multiply' }}
          />
        </div>
        
        {/* Progress */}
        <div className="flex flex-row items-center gap-4 w-[225px] h-[20px]">
          <span className="w-[109px] h-[20px] text-[14px] leading-[20px] font-normal text-white/80 font-inter">
            Question {currentStep + 1} of {totalQuestions}
          </span>
          <div className="flex flex-row items-center w-[100px] h-[8px] bg-white/20 rounded-full">
            {Array.from({ length: totalQuestions }, (_, index) => (
              <div
                key={index}
                className={`flex-1 h-[8px] ${
                  index <= currentStep ? 'bg-white' : 'bg-transparent'
                } ${
                  index === 0 ? 'rounded-l-full' : 
                  index === totalQuestions - 1 ? 'rounded-r-full' : ''
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="flex flex-col items-start gap-7 w-[536px] h-[513px]">
        {/* Question Text */}
        <h2 className="w-[536px] text-[22px] leading-[140%] font-medium text-white font-inter-display">
          {currentQuestion.text}
        </h2>

        {/* Options List */}
        <div className="flex flex-col items-start gap-3 w-[536px]">
          {currentQuestion.options.map((option) => {
            const isSelected = answers[currentQuestion.id] === option.value;
            return (
              <div
                key={option.value}
                className={`flex flex-row items-start justify-between w-[536px] bg-white/10 border border-white/10 rounded-[16px] p-4 cursor-pointer transition-all duration-200 ${
                  isSelected ? 'bg-white/20 border-white/20' : 'hover:bg-white/15'
                }`}
                onClick={() => handleOptionChange(option.value)}
                style={{ minHeight: '56px' }}
              >
                <span className="flex-1 text-[16px] leading-[24px] font-medium text-white font-inter pr-2">
                  {option.label}
                </span>
                <div className="flex items-center justify-center w-[24px] h-[24px] p-[2px]">
                  <div 
                    className={`w-[20px] h-[20px] rounded-full border transition-all duration-200 ${
                      isSelected 
                        ? 'bg-white border-white' 
                        : 'bg-white/10 border-white/30'
                    }`}
                  >
                    {isSelected && (
                      <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                        <div className="w-[8px] h-[8px] rounded-full bg-blue-600" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Button Group */}
        <div className="flex flex-row justify-between items-start gap-6 w-[536px] h-[56px]">
          {/* Back Button */}
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className={`flex items-center justify-center px-8 py-4 h-[56px] bg-white/30 rounded-full transition-all duration-200 ${
              currentStep === 0 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-white/40'
            }`}
          >
            <span className="text-[16px] leading-[24px] font-medium text-white font-inter">
              Back
            </span>
          </button>

          {/* Next/Finish Button */}
          <button
            onClick={isLastStep ? handleSubmit : handleNext}
            disabled={!isCurrentQuestionAnswered || isLoading}
            className={`flex items-center justify-between px-8 py-4 h-[56px] w-[288px] bg-white rounded-full transition-all duration-200 ${
              !isCurrentQuestionAnswered || isLoading
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-white/90'
            }`}
          >
            {isLoading && isLastStep ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-[#00121F]" />
                <span className="text-[16px] leading-[24px] font-medium text-[#00121F] font-inter ml-2">
                  Generating...
                </span>
              </>
            ) : (
              <>
                <span className="text-[16px] leading-[24px] font-medium text-[#00121F] font-inter">
                  {isLastStep ? 'Finish' : 'Next'}
                </span>
                <div className="w-[28px] h-[28px] bg-gray-400 rounded-full flex items-center justify-center">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path 
                      d="M8.59 16.59L13.17 12L8.59 7.41L10 6L16 12L10 18L8.59 16.59Z" 
                      fill="white"
                    />
                  </svg>
                </div>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileWizard;
