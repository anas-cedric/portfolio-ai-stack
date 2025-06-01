'use client';

import React from 'react';
import { PortfolioData } from '@/lib/types';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import PortfolioDonutChart from './PortfolioDonutChart';

interface AllocationSidebarProps {
  portfolioData: PortfolioData;
  onApprove?: () => void;
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

export default function AllocationSidebar({ portfolioData, onApprove }: AllocationSidebarProps) {
  console.log('AllocationSidebar onApprove:', typeof onApprove, !!onApprove);
  // Build holdings data (individual assets)
  const holdingsData = portfolioData.holdings.map(holding => ({
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
    <aside className="bg-[#00090F] text-white flex flex-col gap-8 w-[560px] p-10 relative h-full overflow-y-auto">
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

      {/* Approve button */}
      {onApprove && (
        <div className="w-full flex justify-center mt-auto mb-4">
          <Button
            onClick={onApprove}
            className="bg-[#12A594] hover:bg-[#0e8f80] text-white rounded-full w-full max-w-[400px] h-14 font-medium text-base"
          >
            ✓ Approve Portfolio
          </Button>
        </div>
      )}
    </aside>
  );
}
