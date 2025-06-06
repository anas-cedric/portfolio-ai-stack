'use client';

import React from 'react';
import Image from 'next/image';
import { Info } from 'lucide-react'; // Using lucide-react for icons
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'; // For the info icon

interface AssetListItemProps {
  asset: {
    icon?: React.ReactNode; // Placeholder for the 'V' logo or similar
    name: string;
    ticker: string;
    description?: string; // For the info tooltip
    weight: number;
    // expenseRatio: number; // removed from display, kept here if needed for future
  };
}

const AssetListItem: React.FC<AssetListItemProps> = ({ asset }) => {
  return (
    <div className="py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50/50 transition-colors duration-200 rounded-lg px-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm overflow-hidden">
            {asset.ticker.startsWith('V') && asset.ticker !== 'VTIP' ? (
              <Image 
                src="/images/vanguard-logo.jpeg" 
                alt="Vanguard" 
                width={40} 
                height={40} 
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                {asset.ticker.charAt(0)}
              </div>
            )}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-gray-900">{asset.name}</h3>
              {asset.description && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info size={14} className="text-gray-400 cursor-pointer hover:text-gray-600" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{asset.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
            <p className="text-sm text-gray-500 font-medium">{asset.ticker}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-gray-900">{(asset.weight * 100).toFixed(1)}%</div>
        </div>
      </div>
    </div>
  );
};

export default AssetListItem;
