import { getAuthUser } from '@/lib/auth';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, Shield, TrendingUp, Zap, ChevronRight, BarChart3 } from 'lucide-react';

export default async function HomePage() {
  // Check if user is authenticated
  const user = await getAuthUser();

  // If authenticated, redirect to portfolio quiz
  if (user) {
    redirect('/portfolio-quiz');
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Navigation */}
      <nav className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Image 
                src="/images/cedric-logo.svg" 
                alt="Cedric" 
                width={40} 
                height={40}
                className="rounded-full"
              />
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">Cedric</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/api/auth/login">
                <Button variant="outline" className="font-medium">
                  Sign In
                </Button>
              </Link>
              <Link href="/api/auth/register">
                <Button className="bg-green-600 hover:bg-green-700 text-white font-medium">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 dark:text-slate-100 mb-6">
            Build Your Perfect Portfolio
            <span className="block text-green-600 mt-2">In Minutes, Not Hours</span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-8 max-w-3xl mx-auto">
            Answer a few questions about your goals and risk tolerance. 
            Our AI creates a personalized investment portfolio, then helps you implement it.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/api/auth/register">
              <Button size="lg" className="bg-green-600 hover:bg-green-700 text-white font-semibold px-8 py-6 text-lg">
                Start Building Your Portfolio
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/api/auth/login">
              <Button size="lg" variant="outline" className="font-semibold px-8 py-6 text-lg">
                Already have an account?
                <ChevronRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-4">
            Free account • Paper trading available • No credit card required
          </p>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="text-center">
            <CardContent className="pt-8">
              <div className="bg-green-100 dark:bg-green-900/20 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">1</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3">Answer Questions</h3>
              <p className="text-slate-600 dark:text-slate-400">
                Tell us about your investment goals, timeline, and risk tolerance.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-8">
              <div className="bg-green-100 dark:bg-green-900/20 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3">Get Your Portfolio</h3>
              <p className="text-slate-600 dark:text-slate-400">
                Our AI creates a diversified portfolio tailored to your needs.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-8">
              <div className="bg-green-100 dark:bg-green-900/20 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">3</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3">Start Investing</h3>
              <p className="text-slate-600 dark:text-slate-400">
                Implement your portfolio with our step-by-step guidance.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* CTA */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <Card className="bg-gradient-to-r from-green-600 to-green-700 text-white">
          <CardContent className="text-center py-16">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Start Investing Smarter?
            </h2>
            <p className="text-lg text-green-100 mb-8">
              Join thousands of investors using our platform to build wealth intelligently.
            </p>
            <Link href="/api/auth/register">
              <Button size="lg" className="bg-white text-green-600 hover:bg-slate-50 font-semibold px-8 py-4">
                Create Free Account
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <p className="text-sm text-green-200 mt-4">
              Start with paper trading • No investment required
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}