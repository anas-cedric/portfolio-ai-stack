'use client';

import React, { useState } from 'react';
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

// Define the type for the answers state
interface Answers {
  [key: string]: string; // Question ID maps to selected option value ('a', 'b', etc.)
}

interface ProfileWizardProps {
  questions: Question[];
  onComplete: (answers: Answers) => void; // Changed signature: expects simple answers object
}

const ProfileWizard: React.FC<ProfileWizardProps> = ({ 
  questions, 
  onComplete 
}) => {
  const [currentStep, setCurrentStep] = useState(0);
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
        <div className="flex items-center justify-center w-[77px] h-[26px] border border-white rounded-full">
          <span className="text-[14px] leading-[16px] font-normal text-white tracking-[0.08em] uppercase font-inter">
            Paige<span className="align-super text-[10px] ml-1">&reg;</span>
          </span>
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

      {/* Question Section */}
      <div className="flex flex-col gap-8 w-[536px]">
        {/* Question */}
        <div className="flex flex-col gap-4 w-[536px]">
          <h2 className="text-[36px] leading-[44px] font-medium text-white font-inter-display">
            {currentQuestion.text}
          </h2>
        </div>

        {/* Options */}
        <div className="flex flex-col gap-3 w-[536px]">
          {currentQuestion.options.map((option) => (
            <div key={option.value} className="flex items-center gap-3 w-[536px]">
              <input
                type="radio"
                id={`${currentQuestion.id}-${option.value}`}
                name={currentQuestion.id}
                value={option.value}
                checked={answers[currentQuestion.id] === option.value}
                onChange={() => handleOptionChange(option.value)}
                className="w-[20px] h-[20px] text-white bg-transparent border-2 border-white rounded-full focus:ring-white focus:ring-2"
              />
              <label
                htmlFor={`${currentQuestion.id}-${option.value}`}
                className="text-[16px] leading-[24px] font-normal text-white font-inter cursor-pointer"
              >
                {option.label}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center w-[536px] mt-auto">
        {/* Back Button */}
        <button
          onClick={handlePrevious}
          disabled={currentStep === 0}
          className={`flex items-center justify-center w-[107px] h-[56px] rounded-full border-2 ${
            currentStep === 0
              ? 'border-white/30 text-white/30 cursor-not-allowed'
              : 'border-white text-white hover:bg-white/10'
          } transition-all duration-200`}
        >
          <span className="text-[16px] leading-[24px] font-medium font-inter">
            Back
          </span>
        </button>

        {/* Next/Submit Button */}
        {isLastStep ? (
          <button
            onClick={handleSubmit}
            disabled={!isCurrentQuestionAnswered}
            className={`flex items-center justify-center w-[154px] h-[56px] rounded-full ${
              isCurrentQuestionAnswered
                ? 'bg-white text-[#00121F] hover:bg-white/90'
                : 'bg-white/30 text-white/50 cursor-not-allowed'
            } transition-all duration-200`}
          >
            <span className="text-[16px] leading-[24px] font-medium font-inter">
              Submit
            </span>
          </button>
        ) : (
          <button
            onClick={handleNext}
            disabled={!isCurrentQuestionAnswered}
            className={`flex items-center justify-center w-[154px] h-[56px] rounded-full ${
              isCurrentQuestionAnswered
                ? 'bg-white text-[#00121F] hover:bg-white/90'
                : 'bg-white/30 text-white/50 cursor-not-allowed'
            } transition-all duration-200`}
          >
            <span className="text-[16px] leading-[24px] font-medium font-inter">
              Next
            </span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ProfileWizard;