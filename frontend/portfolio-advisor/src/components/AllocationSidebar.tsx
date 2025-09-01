'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { PortfolioData } from '@/lib/types';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import PortfolioDonutChart from './PortfolioDonutChart';
interface AllocationSidebarProps {
  portfolioData: PortfolioData;
  onApprove?: () => void;
  user?: any; // Kinde user object
}

// Define sector mappings for ETFs
const ETF_SECTORS: Record<string, { sector: string; color: string }> = {
  // Equity ETFs
  'VTI': { sector: 'US Equity', color: '#6582E4' },
  'VUG': { sector: 'US Growth', color: '#8B5CF6' },
  'VBR': { sector: 'US Small-Cap', color: '#EC4899' },
  'VEA': { sector: 'Int\'l Developed', color: '#10B981' },
  'VSS': { sector: 'Int\'l Small-Cap', color: '#F59E0B' },
  'VWO': { sector: 'Emerging Markets', color: '#EF4444' },
  // Fixed Income ETFs
  'BND': { sector: 'US Bonds', color: '#6366F1' },
  'BNDX': { sector: 'Int\'l Bonds', color: '#14B8A6' },
  'VTIP': { sector: 'Inflation Protected', color: '#A78BFA' },
  // Real Estate ETFs
  'VNQ': { sector: 'US Real Estate', color: '#F97316' },
  'VNQI': { sector: 'Int\'l Real Estate', color: '#84CC16' },
  // Other
  'CASH': { sector: 'Cash & Equivalents', color: '#94A3B8' }
};

export default function AllocationSidebar({ portfolioData, onApprove, user }: AllocationSidebarProps) {
  const [isExecuting, setIsExecuting] = React.useState(false);
  const [executionStatus, setExecutionStatus] = React.useState<string | null>(null);
  const router = useRouter();
  
  const handleApproveClick = async () => {
    console.log('Approve button clicked', { hasOnApprove: !!onApprove, hasUser: !!user, user });
    
    if (!user) {
      console.log('Stopping execution - missing user');
      return;
    }
    
    setIsExecuting(true);
    setExecutionStatus('Executing portfolio...');
    
    try {
      // Convert holdings to weights format expected by API
      const weights = portfolioData.holdings.map(holding => ({
        symbol: holding.ticker,
        weight: holding.percentage
      }));
      
      // Call the Alpaca execution API with user info
      console.log('Making API call with weights:', weights);
      
      const response = await fetch('/api/portfolio/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          weights,
          totalInvestment: 10000,
          userId: user.id,
          userEmail: user.email || `${user.id}@example.com`,
          userFirstName: user.given_name || 'User',
          userLastName: user.family_name || 'Account'
        })
      });
      
      console.log('API response status:', response.status);
      const result = await response.json();
      console.log('API response body:', result);
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to execute portfolio');
      }
      
      console.log('Portfolio executed successfully:', result);
      setExecutionStatus('Portfolio executed successfully!');

      // Update onboarding state to portfolio_approved BEFORE navigating, so Dashboard gate allows access
      try {
        const onboardingRes = await fetch('/api/onboarding', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ state: 'portfolio_approved' })
        });
        if (!onboardingRes.ok) {
          const body = await onboardingRes.json().catch(() => ({}));
          console.warn('Failed to set onboarding state to portfolio_approved:', body);
        }
      } catch (e) {
        console.warn('Error updating onboarding state to portfolio_approved:', e);
      }

      // Redirect directly to dashboard with marker param; dashboard will finalize to 'active'
      router.push('/dashboard?from=approval');

      // Optional: notify parent (non-blocking)
      try { onApprove?.(); } catch {}
      
    } catch (error: any) {
      console.error('Failed to execute portfolio:', error);
      setExecutionStatus(`Error: ${error.message}`);
      setIsExecuting(false);
    }
  };
  // Build holdings data (individual assets) - sorted by percentage (highest to lowest)
  const holdingsData = portfolioData.holdings
    .sort((a, b) => b.percentage - a.percentage)
    .map(holding => ({
      name: holding.ticker,
      value: holding.percentage,
      color: ETF_SECTORS[holding.ticker]?.color || '#6B7280'
    }));

  // Build sectors data (aggregated by sector)
  const sectorsMap = new Map<string, { value: number; color: string }>();
  portfolioData.holdings.forEach(holding => {
    const sectorInfo = ETF_SECTORS[holding.ticker];
    if (sectorInfo) {
      const existing = sectorsMap.get(sectorInfo.sector) || { value: 0, color: sectorInfo.color };
      sectorsMap.set(sectorInfo.sector, {
        value: existing.value + holding.percentage,
        color: sectorInfo.color
      });
    }
  });
  
  const sectorsData = Array.from(sectorsMap.entries())
    .map(([sector, data]) => ({
      name: sector,
      value: data.value,
      color: data.color
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <aside className="bg-[#00090F] text-white flex flex-col w-[560px] relative h-full">
      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto p-10 pb-[120px]">
        {/* Title + Tabs */}
        <div className="flex flex-col gap-5 w-full">
          <h2 className="font-inter-display text-[36px] font-medium leading-[44px] w-full">
            Portfolio Allocation
          </h2>
          <Tabs defaultValue="holdings" className="w-full">
            <TabsList className="gap-2 bg-transparent p-0 h-auto w-fit">
              <TabsTrigger 
                value="holdings" 
                className="relative bg-transparent text-white/60 border border-white/20 rounded-full px-4 py-2 font-medium transition-all aria-selected:bg-white aria-selected:text-[#00121F] aria-selected:border-white data-[state=active]:bg-white data-[state=active]:text-[#00121F] data-[state=active]:border-transparent"
              >
                Holdings
              </TabsTrigger>
              <TabsTrigger
                value="sectors"
                className="relative bg-transparent text-white/60 border border-white/20 rounded-full px-4 py-2 font-medium transition-all aria-selected:bg-white aria-selected:text-[#00121F] aria-selected:border-white data-[state=active]:bg-white data-[state=active]:text-[#00121F] data-[state=active]:border-transparent"
              >
                Sectors
              </TabsTrigger>
            </TabsList>
            <TabsContent value="holdings" className="pt-8 w-full flex flex-col items-center gap-6">
              {/* Holdings Donut Chart */}
              <div className="relative w-[320px] h-[320px]">
                <PortfolioDonutChart data={holdingsData} showCenterText={false} />
              </div>
              {/* Holdings Legend */}
              <div className="w-full max-h-[200px] overflow-y-auto dark-scrollbar">
                <div className="space-y-2 pr-2">
                  {holdingsData.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 flex-1">
                        <span
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-white text-sm">{item.name}</span>
                      </div>
                      <span className="text-white/60 text-sm">{item.value.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
            <TabsContent value="sectors" className="pt-8 w-full flex flex-col items-center gap-6">
              {/* Sectors Donut Chart */}
              <div className="relative w-[320px] h-[320px]">
                <PortfolioDonutChart data={sectorsData} showCenterText={false} />
              </div>
              {/* Sectors Legend */}
              <div className="w-full max-h-[200px] overflow-y-auto dark-scrollbar">
                <div className="space-y-2 pr-2">
                  {sectorsData.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 flex-1">
                        <span
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-white text-sm">{item.name}</span>
                      </div>
                      <span className="text-white/60 text-sm">{item.value.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Fixed Approve button at bottom */}
      {onApprove && (
        <div className="absolute bottom-0 left-0 right-0 p-10 bg-[#00090F]">
          {executionStatus && (
            <div className={`mb-4 p-3 rounded-lg text-center ${
              executionStatus.includes('Error') ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'
            }`}>
              {executionStatus}
            </div>
          )}
          <Button
            onClick={handleApproveClick}
            disabled={isExecuting}
            className="bg-[#12A594] hover:bg-[#0e8f80] text-white rounded-full w-full h-14 font-medium text-base disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExecuting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Executing Portfolio...
              </span>
            ) : (
              '✓ Approve & Execute Portfolio'
            )}
          </Button>
        </div>
      )}
    </aside>
  );
}
