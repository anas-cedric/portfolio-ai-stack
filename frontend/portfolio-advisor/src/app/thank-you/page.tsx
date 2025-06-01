'use client';

import React from 'react';
import Link from 'next/link';

export default function ThankYouPage() {
  return (
    <div className="w-full h-screen overflow-hidden clouds-bg py-4 px-4 flex flex-col items-center justify-center">
      <div className="relative w-full h-screen flex items-center justify-center">
        {/* Glassmorphism Form Card */}
        <div className="relative w-[488px] bg-white/12 backdrop-blur-[60px] border border-white/8 rounded-[24px] p-10 flex flex-col gap-8">
          {/* Logo Container */}
          <div className="relative w-[77px] h-[26px] border border-white rounded-full flex items-center justify-center">
            {/* Paige Logo Text */}
            <span className="text-[14px] leading-[16px] font-normal text-white tracking-[0.08em] uppercase font-inter">
              Paige<span className="align-super text-[10px] ml-1">&reg;</span>
            </span>
          </div>

          {/* Content Container */}
          <div className="flex flex-col gap-6">
            {/* Title Container */}
            <div className="flex flex-col gap-3">
              <h1 className="text-[36px] leading-[44px] font-medium text-white font-inter-display">
                Thank You
              </h1>
              <p className="text-[16px] leading-[24px] font-normal text-white/80 font-inter">
                Thank you for trying Paige. We appreciate your time and feedback in exploring our AI-powered wealth advisory platform.
              </p>
            </div>

            {/* Button */}
            <Link href="/">
              <button className="w-full h-14 bg-white rounded-full flex items-center justify-between px-8 py-4 group hover:bg-white/95 transition-all duration-200 mt-2">
                <span className="text-[16px] leading-[24px] font-medium text-[#00121F] font-inter mx-auto">
                  Return Home
                </span>
                <span className="flex items-center justify-center w-7 h-7 ml-2">
                  <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="14" cy="14" r="14" fill="#00121F"/>
                    <path d="M10 14H18" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M15 11L18 14L15 17" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
              </button>
            </Link>
          </div>
        </div>

        {/* Copyright Footer */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
          <p className="text-[12px] leading-[18px] font-normal text-white/80 font-inter">
            2025 Paige. All Rights Reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
