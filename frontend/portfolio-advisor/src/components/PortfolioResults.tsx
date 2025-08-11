'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ChatInterface from './ChatInterface';
import PortfolioPieChart from './PortfolioPieChart';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { PortfolioData, UserProfile, PortfolioResponse } from '@/lib/types';

interface PortfolioResultsProps {
  portfolioData: PortfolioData;
  userPreferences: UserProfile;
  onReset: () => void;
  onPortfolioUpdate?: (updatedPortfolio: PortfolioResponse) => void;
}

export default function PortfolioResults({
  portfolioData,
  userPreferences,
  onReset,
  onPortfolioUpdate,
}: PortfolioResultsProps) {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const router = useRouter();

  const handleApprove = () => {
    setShowConfirmation(true);
  };

  const handleConfirmationRedirect = () => {
    router.push('/thank-you');
  };

  return (
    <Card className="p-6">
      <CardHeader className="flex flex-row justify-between items-center mb-4"> 
        <CardTitle className="text-black">Your Portfolio Recommendation</CardTitle>
        <Button variant="secondary" onClick={onReset}>Start Over</Button>
      </CardHeader>

      <CardContent>
        {/* Removed surrounding Card so ChatInterface bottom bar can render flush with parent page */}
        <div className="mt-4">
          <ChatInterface 
            portfolioData={portfolioData} 
            userPreferences={userPreferences} 
            onApprove={handleApprove} 
            onPortfolioUpdate={onPortfolioUpdate}
          />
        </div>
        <Card className="mt-6"> 
          <CardHeader>
            <CardTitle className="text-lg">Allocation</CardTitle> 
          </CardHeader>
          <CardContent>
            <PortfolioPieChart allocations={portfolioData.allocations} />
          </CardContent>
        </Card>
      </CardContent>

      <AlertDialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Demo Complete!</AlertDialogTitle>
            <AlertDialogDescription>
              You have successfully completed the Cedric AI Wealth Advisor demo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={handleConfirmationRedirect}>OK</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}