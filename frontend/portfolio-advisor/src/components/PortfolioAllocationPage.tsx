'use client';

import React from 'react';
import Image from 'next/image';
import { ChevronUp } from 'lucide-react';
import { PortfolioData, PortfolioResponse } from '@/lib/types';
import AllocationSidebar from './AllocationSidebar';
import ChatInterface from './ChatInterface';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface PortfolioAllocationPageProps {
  portfolioData: PortfolioData;
  onApprove?: () => void;
  userPreferences?: any;
  onPortfolioUpdate?: (updated: PortfolioResponse) => void;
  onStartOver?: () => void;
}

const InfoIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" className="opacity-60 hover:opacity-100 cursor-pointer transition-opacity">
    <circle cx="7" cy="7" r="6.25" stroke="currentColor" strokeWidth="1.5" fill="none"/>
    <circle cx="7" cy="4.5" r="0.875" fill="currentColor"/>
    <line x1="7" y1="6.5" x2="7" y2="10.5" stroke="currentColor" strokeWidth="1.5"/>
  </svg>
);

// ETF expense ratios based on actual current data
const ETF_EXPENSE_RATIOS: Record<string, number> = {
  'VTI': 0.03,   // Vanguard Total Stock Market ETF
  'VUG': 0.04,   // Vanguard Growth ETF  
  'VBR': 0.07,   // Vanguard Small-Cap Value ETF
  'VEA': 0.05,   // Vanguard FTSE Developed Markets ETF
  'VSS': 0.11,   // Vanguard FTSE All-World ex-US Small-Cap ETF
  'VWO': 0.08,   // Vanguard FTSE Emerging Markets ETF
  'VNQ': 0.12,   // Vanguard Real Estate ETF
  'VNQI': 0.12,  // Vanguard Global ex-U.S. Real Estate ETF
  'BND': 0.035,  // Vanguard Total Bond Market ETF
  'BNDX': 0.05,  // Vanguard Total International Bond ETF
  'VTIP': 0.04,  // Vanguard Short-Term Inflation-Protected Securities ETF
  'CASH': 0.00   // Cash has no expense ratio
};

// ETF descriptions for tooltips
const ETF_DESCRIPTIONS: Record<string, string> = {
  'VTI': 'Tracks the entire U.S. stock market, providing broad exposure to large-, mid-, and small-cap stocks.',
  'VUG': 'Focuses on U.S. large-cap growth stocks with strong earnings growth potential.',
  'VBR': 'Invests in U.S. small-cap value stocks that are trading below their intrinsic value.',
  'VEA': 'Provides exposure to developed international markets in Europe, Asia, and the Pacific.',
  'VSS': 'Tracks small-cap stocks from developed markets outside the United States.',
  'VWO': 'Invests in emerging market stocks from countries like China, India, Taiwan, and Brazil.',
  'VNQ': 'Tracks U.S. real estate investment trusts (REITs) across various property sectors.',
  'VNQI': 'Provides exposure to international real estate markets outside the United States.',
  'BND': 'Tracks the broad U.S. bond market, including government, corporate, and mortgage-backed bonds.',
  'BNDX': 'Invests in international bonds from developed markets, excluding the United States.',
  'VTIP': 'Focuses on short-term Treasury Inflation-Protected Securities (TIPS) to hedge against inflation.',
  'CASH': 'Cash and cash equivalents provide liquidity and stability with minimal risk.'
};

const PortfolioAllocationPage: React.FC<PortfolioAllocationPageProps> = ({ portfolioData, onApprove, userPreferences, onPortfolioUpdate, onStartOver }) => {
  const [showScrollTop, setShowScrollTop] = React.useState(false);
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);
  
  const vanguardTickers = ['VTI', 'VUG', 'VBR', 'VEA', 'VSS', 'VWO', 'VNQ', 'VNQI', 'BND', 'BNDX', 'VTIP'];

  React.useEffect(() => {
    const handleScroll = () => {
      if (scrollContainerRef.current) {
        setShowScrollTop(scrollContainerRef.current.scrollTop > 300);
      }
    };

    const scrollContainer = scrollContainerRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll);
      return () => scrollContainer.removeEventListener('scroll', handleScroll);
    }
  }, []);

  const scrollToTop = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  if (!portfolioData) {
    return <p>No portfolio data.</p>;
  }

  return (
    <TooltipProvider>
      <div className="w-full h-screen bg-[#E6EFF3] flex overflow-hidden">
        {/* Left section - White section with table */}
        <div className="flex-1 flex flex-col relative h-full">
          {/* Scrollable content area */}
          <div ref={scrollContainerRef} className="flex-1 overflow-y-auto light-scrollbar">
            <div className="p-8 pb-[100px]">
              <div className="w-full max-w-[744px] mx-auto">
              {/* Header section */}
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-2">
                  <div className="border border-black/20 rounded-full px-3 py-1">
                    <span className="text-sm font-medium">PAIGE</span>
                  </div>
                </div>
                <button 
                  onClick={onStartOver}
                  className="flex items-center gap-2 text-[#00121F]/60 hover:text-[#00121F]/80 transition-colors"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 8H13M3 8L6 5M3 8L6 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span className="text-sm">Start Over</span>
                </button>
              </div>

              <h1 className="text-[36px] leading-[44px] font-medium text-[#00121F] mb-2">
                Your Portfolio Recommendation
              </h1>
              
              <p className="text-base leading-6 text-[#00121F] mb-2">
                Hi{userPreferences?.firstName ? `, ${userPreferences.firstName}` : ''}! Based on your profile, I've designed this portfolio for you:
              </p>
              
              <p className="text-base leading-6 text-[#00121F] mb-6">
                Here's your recommended portfolio allocation:
              </p>

              {/* Allocation table */}
              <Table className="w-full mb-8">
                <TableHeader>
                  <TableRow className="border-b border-[#00121F]/10">
                    <TableHead className="text-[#00121F]/50 text-xs font-normal pb-3">Asset</TableHead>
                    <TableHead className="text-right text-[#00121F]/50 text-xs font-normal pb-3">
                      <div className="flex items-center justify-end gap-1">
                        Expense Ratio
                        <Tooltip delayDuration={300}>
                          <TooltipTrigger asChild>
                            <button 
                              type="button" 
                              className="inline-flex items-center hover:bg-gray-100 rounded p-1 -m-1 transition-colors"
                              aria-label="More information about expense ratios"
                            >
                              <InfoIcon />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="bg-gray-900 text-white border-gray-800">
                            <p>The annual fee charged by the fund as a percentage of your investment. Lower expense ratios mean more of your money stays invested.</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                    </TableHead>
                    <TableHead className="text-right text-[#00121F]/50 text-xs font-normal pb-3">Weight%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {portfolioData.holdings
                    .sort((a, b) => b.percentage - a.percentage)
                    .map((holding, idx) => (
                    <TableRow key={idx} className="border-b border-[#00121F]/5">
                      <TableCell className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm overflow-hidden">
                            {vanguardTickers.includes(holding.ticker) ? (
                              <Image 
                                src="/images/vanguard-logo.jpeg" 
                                alt="Vanguard" 
                                width={40} 
                                height={40} 
                                className="object-cover"
                              />
                            ) : (
                              <div className="w-full h-full bg-[#B91C1C] flex items-center justify-center text-white font-bold text-sm">
                                {holding.ticker.charAt(0)}
                              </div>
                            )}
                          </div>
                          <div className="flex flex-col flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-[#00121F] font-medium">
                                {holding.name || holding.ticker}
                              </span>
                              {ETF_DESCRIPTIONS[holding.ticker] && (
                                <Tooltip delayDuration={300}>
                                  <TooltipTrigger asChild>
                                    <button 
                                      type="button" 
                                      className="inline-flex items-center hover:bg-gray-100 rounded p-1 -m-1 transition-colors"
                                      aria-label={`More information about ${holding.ticker}`}
                                    >
                                      <InfoIcon />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="top" className="max-w-[300px] bg-gray-900 text-white border-gray-800">
                                    <p>{ETF_DESCRIPTIONS[holding.ticker]}</p>
                                  </TooltipContent>
                                </Tooltip>
                              )}
                            </div>
                            <span className="text-xs text-[#00121F]/50 uppercase">
                              {holding.ticker}
                            </span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right py-4">
                        <span className="text-sm text-[#00121F]">
                          {(ETF_EXPENSE_RATIOS[holding.ticker] || 0.03).toFixed(2)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right py-4">
                        <span className="text-sm text-[#00121F] font-medium">{holding.percentage.toFixed(1)}%</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              </div>
            </div>
          </div>

          {/* Fixed chat area at bottom using ChatInterface component */}
          <div className="absolute bottom-0 left-0 right-0 z-40 bg-gradient-to-t from-[#E6EFF3] via-[#E6EFF3] to-transparent pt-8 pb-6">
            <div className="max-w-[744px] mx-auto px-8">
              <ChatInterface 
                portfolioData={portfolioData} 
                userPreferences={userPreferences}
                onPortfolioUpdate={onPortfolioUpdate}
                onApprove={onApprove}
              />
            </div>
          </div>

          {/* Scroll to top button */}
          {showScrollTop && (
            <button
              onClick={scrollToTop}
              className="fixed bottom-24 right-8 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-all duration-200 z-50"
              aria-label="Scroll to top"
            >
              <ChevronUp className="w-6 h-6 text-gray-700" />
            </button>
          )}
        </div>

        {/* Right section - Black section with chart */}
        <AllocationSidebar portfolioData={portfolioData} onApprove={onApprove} />
      </div>
    </TooltipProvider>
  );
};

export default PortfolioAllocationPage;