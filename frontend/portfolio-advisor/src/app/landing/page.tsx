import { getAuthUser } from '@/lib/auth';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, Shield, TrendingUp, Zap, ChevronRight } from 'lucide-react';

export default async function LandingPage() {
  // Check if user is authenticated
  const user = await getAuthUser();

  // If authenticated, redirect to dashboard
  if (user) {
    redirect('/dashboard');
  }

  return (
    <div className="min-h-screen clouds-bg">
      {/* Navigation */}
      <nav className="glass-card mx-4 mt-4 sm:mx-8 sm:mt-8 p-4 rounded-2xl">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">Portfolio Advisor</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/api/auth/login">
              <Button variant="outline" className="font-medium">
                Sign In
              </Button>
            </Link>
            <Link href="/api/auth/register">
              <Button className="bg-blue-600 hover:bg-blue-700 text-white font-medium">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-6">
            Intelligent Portfolio Management
            <span className="block text-blue-600 mt-2">Made Simple</span>
          </h1>
          <p className="text-xl text-gray-700 mb-8 max-w-3xl mx-auto">
            Build a personalized investment portfolio based on your risk profile, goals, and timeline. 
            Get started in minutes with our AI-powered advisor.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/api/auth/register">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-6 text-lg rounded-xl">
                Start Building Your Portfolio
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/">
              <Button size="lg" variant="outline" className="font-semibold px-8 py-6 text-lg rounded-xl bg-white/50 backdrop-blur-sm">
                Try Demo
                <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="glass-card p-8">
            <div className="bg-blue-100 rounded-xl w-14 h-14 flex items-center justify-center mb-4">
              <Shield className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Risk-Adjusted Portfolios</h3>
            <p className="text-gray-700">
              Our algorithm creates portfolios tailored to your risk tolerance and investment timeline.
            </p>
          </div>

          <div className="glass-card p-8">
            <div className="bg-green-100 rounded-xl w-14 h-14 flex items-center justify-center mb-4">
              <TrendingUp className="w-7 h-7 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Automated Rebalancing</h3>
            <p className="text-gray-700">
              Keep your portfolio optimized with intelligent rebalancing suggestions and execution.
            </p>
          </div>

          <div className="glass-card p-8">
            <div className="bg-purple-100 rounded-xl w-14 h-14 flex items-center justify-center mb-4">
              <Zap className="w-7 h-7 text-purple-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">AI-Powered Insights</h3>
            <p className="text-gray-700">
              Get personalized recommendations and market insights powered by advanced AI models.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <Card className="glass-card p-12 text-center">
          <CardContent>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to Start Investing Smarter?
            </h2>
            <p className="text-lg text-gray-700 mb-8">
              Join thousands of investors using our platform to build wealth intelligently.
            </p>
            <Link href="/api/auth/register">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-xl">
                Create Free Account
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <p className="text-sm text-gray-600 mt-4">
              No credit card required • Start with paper trading
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}