import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ThankYouPage() {
  return (
    // Use a main tag for semantic structure, consistent background, and flex layout
    <main className="flex items-center justify-center min-h-screen w-full bg-muted/40 p-4 md:p-8">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader>
          <CardTitle className="text-center text-2xl font-bold text-gray-800">Demo Complete</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-6 p-6"> 
          <p className="text-lg text-gray-700"> 
            Thank you for participating in the Paige Wealth Demo!
          </p>
          <p className="text-sm text-gray-500">
            We appreciate your time and feedback.
          </p>
          <Link href="/" passHref> 
            {/* Use default button variant unless outline is specifically desired */}
            <Button variant="default">Return Home</Button> 
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
