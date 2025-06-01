'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto">
      <Card className="text-center mb-16 p-8">
        <CardHeader>
          <CardTitle className="text-4xl">Paige AI Portfolio Advisor</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xl text-gray-600 mb-8">
            Get personalized investment recommendations powered by AI
          </p>
          <Button asChild>
            <Link href="/advisor">Get Started</Link>
          </Button>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
        <FeatureCard 
          title="Personalized"
          description="Recommendations tailored to your specific financial goals and risk tolerance"
          icon="🎯"
        />
        <FeatureCard 
          title="Data-Driven"
          description="Analysis based on real-time market data and economic indicators"
          icon="📊"
        />
        <FeatureCard 
          title="AI-Powered"
          description="Leveraging advanced AI models like OpenAI o3 for intelligent insights"
          icon="🧠"
        />
      </div>

      <Card className="bg-primary-50 p-8 border border-primary-200">
        <CardHeader>
          <CardTitle className="text-primary-800">How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-4 mt-4 text-left">
            <li className="text-lg">
              <span className="font-medium">Share your preferences:</span> Tell us about your financial goals, risk tolerance, and investment timeline
            </li>
            <li className="text-lg">
              <span className="font-medium">AI analysis:</span> Our system analyzes market conditions and matches them to your preferences
            </li>
            <li className="text-lg">
              <span className="font-medium">Get recommendations:</span> Receive a customized portfolio recommendation with detailed explanations
            </li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}

function FeatureCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <Card className="hover:shadow-lg transition-shadow p-6 text-center">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-primary-800 font-semibold mb-1">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </Card>
  );
}
