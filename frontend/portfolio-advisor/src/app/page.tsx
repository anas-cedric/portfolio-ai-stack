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
    <div className="w-full h-screen overflow-hidden clouds-bg py-4 px-4 flex flex-col items-center justify-center">
      {/* Header with Logo */}
      <div className="absolute top-8 left-8 flex items-center space-x-3">
        <div className="border border-white rounded-full px-3 py-1">
          <span className="text-sm font-medium text-white tracking-wider uppercase">
            Cedric
          </span>
        </div>
      </div>

      {/* Auth buttons in top right */}
      <div className="absolute top-8 right-8 flex items-center space-x-4">
        <Link href="/api/auth/login">
          <button className="text-white/80 hover:text-white text-sm font-medium transition-colors">
            Sign In
          </button>
        </Link>
        <Link href="/api/auth/register">
          <button className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 backdrop-blur-sm border border-white/20">
            Get Started
          </button>
        </Link>
      </div>

      {/* Main Content Card */}
      <div 
        className="flex flex-col items-center gap-12 w-[616px] h-[600px] bg-white/12 border border-white/8 rounded-[24px] backdrop-blur-[60px] p-10"
        style={{
          boxSizing: 'border-box'
        }}
      >
        {/* Content */}
        <div className="flex flex-col items-center text-center space-y-8 mt-8">
          <div className="space-y-6">
            <h1 className="text-4xl font-bold text-white leading-tight">
              Build Your Perfect Portfolio
            </h1>
            <p className="text-lg text-white/80 max-w-md leading-relaxed">
              Answer a few questions about your goals and risk tolerance. 
              Our AI creates a personalized investment portfolio, then helps you implement it.
            </p>
          </div>
          
          <div className="bg-white/10 border border-white/10 rounded-[16px] p-6 space-y-4 max-w-md">
            <h3 className="font-semibold text-white">What you'll get:</h3>
            <ul className="text-left space-y-3 text-white/80 text-sm">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-white rounded-full mr-3"></span>
                Personalized asset allocation based on your risk profile
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-white rounded-full mr-3"></span>
                Diversified portfolio across multiple asset classes
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-white rounded-full mr-3"></span>
                Professional-grade investment recommendations
              </li>
            </ul>
          </div>

          <div className="flex flex-col gap-3 w-full max-w-sm">
            <Link href="/api/auth/register" className="w-full">
              <button className="flex items-center justify-center w-full px-8 py-4 bg-white rounded-full transition-all duration-200 hover:bg-white/90">
                <span className="text-[16px] leading-[24px] font-medium text-slate-900">
                  Start Building Your Portfolio
                </span>
                <ArrowRight className="ml-2 w-5 h-5 text-slate-700" />
              </button>
            </Link>
            
            <Link href="/api/auth/login" className="w-full">
              <button className="flex items-center justify-center w-full px-8 py-3 bg-white/20 border border-white/30 rounded-full transition-all duration-200 hover:bg-white/30">
                <span className="text-[14px] leading-[20px] font-medium text-white">
                  Already have an account?
                </span>
                <ChevronRight className="ml-2 w-4 h-4 text-white/80" />
              </button>
            </Link>
          </div>
          
          <p className="text-xs text-white/60">
            Free account • Paper trading available • No credit card required
          </p>
        </div>
      </div>

    </div>
  );
}