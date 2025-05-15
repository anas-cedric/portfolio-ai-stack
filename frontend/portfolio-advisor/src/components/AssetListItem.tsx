'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Info } from 'lucide-react'; // Using lucide-react for icons
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'; // For the info icon

interface AssetListItemProps {
  asset: {
    icon?: React.ReactNode; // Placeholder for the 'V' logo or similar
    name: string;
    ticker: string;
    description?: string; // For the info tooltip
    expenseRatio: number;
    weight: number;
  };
}

const AssetListItem: React.FC<AssetListItemProps> = ({ asset }) => {
  return (
    <Card className="mb-3 hover:shadow-lg transition-shadow duration-200">
      <CardContent className="p-4 flex items-center justify-between">
        <div className="flex items-center">
          {asset.icon && <div className="mr-3 text-2xl text-primary">{asset.icon}</div>}
          <div>
            <div className="flex items-center">
              <h3 className="font-semibold text-base mr-1">{asset.name}</h3>
              {asset.description && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info size={16} className="text-muted-foreground cursor-pointer" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{asset.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{asset.ticker}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="font-semibold text-base">{(asset.weight * 100).toFixed(1)}%</p>
          <p className="text-xs text-muted-foreground">{(asset.expenseRatio * 100).toFixed(2)}% ER</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default AssetListItem;
