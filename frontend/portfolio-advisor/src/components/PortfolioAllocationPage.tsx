'use client';

import React from 'react';
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
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" className="opacity-30">
    <circle cx="7" cy="7" r="6.25" stroke="currentColor" strokeWidth="1.5" fill="none"/>
    <circle cx="7" cy="4.5" r="0.875" fill="currentColor"/>
    <line x1="7" y1="6.5" x2="7" y2="10.5" stroke="currentColor" strokeWidth="1.5"/>
  </svg>
);

const PortfolioAllocationPage: React.FC<PortfolioAllocationPageProps> = ({ portfolioData, onApprove, userPreferences, onPortfolioUpdate, onStartOver }) => {
  const [showScrollTop, setShowScrollTop] = React.useState(false);
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);

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
                    <span className="text-sm font-medium">PAIGE®</span>
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
                        <Tooltip>
                          <TooltipTrigger>
                            <InfoIcon />
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Annual fee charged by the fund as a percentage of your investment</p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                    </TableHead>
                    <TableHead className="text-right text-[#00121F]/50 text-xs font-normal pb-3">Weight%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {portfolioData.holdings.map((holding, idx) => (
                    <TableRow key={idx} className="border-b border-[#00121F]/5">
                      <TableCell className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-[#B91C1C] flex items-center justify-center text-white font-bold text-sm">
                            V
                          </div>
                          <div className="flex flex-col">
                            <span className="text-sm text-[#00121F] font-medium">
                              {holding.name || holding.ticker}
                            </span>
                            <span className="text-xs text-[#00121F]/50 uppercase">
                              {holding.ticker}
                            </span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right py-4">
                        <span className="text-sm text-[#00121F]">0.03%</span>
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
          <div className="absolute bottom-0 left-0 right-0 z-40">
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