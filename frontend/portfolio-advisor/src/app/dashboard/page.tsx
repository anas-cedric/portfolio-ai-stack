import { requireAuth, getAuthUser } from '@/lib/auth';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Wallet, 
  TrendingUp, 
  PieChart, 
  Settings, 
  Plus,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

export default async function Dashboard() {
  // Require authentication
  await requireAuth();
  const user = await getAuthUser();

  // Check if user has completed onboarding
  // In a real app, you'd check this from database
  const hasCompletedOnboarding = false; // TODO: Check from database

  if (!hasCompletedOnboarding) {
    // Redirect to portfolio quiz if not onboarded
    redirect('/');
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold">Portfolio Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.given_name || user?.email}
              </span>
              <Link href="/api/auth/logout">
                <Button variant="outline" size="sm">Sign Out</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Value</p>
                  <p className="text-2xl font-bold">$0.00</p>
                  <p className="text-xs text-green-600 flex items-center mt-1">
                    <ArrowUpRight className="w-3 h-3 mr-1" />
                    0.00%
                  </p>
                </div>
                <Wallet className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Today's Gain</p>
                  <p className="text-2xl font-bold">$0.00</p>
                  <p className="text-xs text-gray-500 mt-1">0.00%</p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Cash Balance</p>
                  <p className="text-2xl font-bold">$0.00</p>
                  <p className="text-xs text-gray-500 mt-1">Available</p>
                </div>
                <Wallet className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Return</p>
                  <p className="text-2xl font-bold">0.00%</p>
                  <p className="text-xs text-gray-500 mt-1">All Time</p>
                </div>
                <PieChart className="w-8 h-8 text-indigo-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Portfolio Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Holdings */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Holdings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-gray-500">
                  <PieChart className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="font-medium mb-2">No Holdings Yet</p>
                  <p className="text-sm mb-4">Start by funding your account and creating your portfolio</p>
                  <Link href="/onboarding">
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      Get Started
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Actions */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link href="/fund" className="block">
                  <Button className="w-full" variant="outline">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Funds
                  </Button>
                </Link>
                <Link href="/trade" className="block">
                  <Button className="w-full" variant="outline">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Trade
                  </Button>
                </Link>
                <Link href="/portfolio" className="block">
                  <Button className="w-full" variant="outline">
                    <PieChart className="w-4 h-4 mr-2" />
                    View Portfolio
                  </Button>
                </Link>
                <Link href="/settings" className="block">
                  <Button className="w-full" variant="outline">
                    <Settings className="w-4 h-4 mr-2" />
                    Settings
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}