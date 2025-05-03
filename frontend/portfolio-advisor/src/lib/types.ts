// Centralized type definitions for the Portfolio Advisor application

// Matches the UserPreferences model in Python
export interface UserProfile {
  age: number;
  income: string; // Assuming string representation like "$50k-$75k"
  risk_tolerance: string; // e.g., "low", "medium", "high"
  investment_goals: string[]; // e.g., ["retirement", "house"]
  time_horizon: string; // e.g., "5-10 years"
  initial_investment: number;
  monthly_contribution: number;
  sector_preferences?: string[]; // Optional
  avoid_sectors?: string[]; // Optional
}

// Matches the Holding model (implicitly defined in Python recalculate_holdings)
export interface Holding {
  ticker: string;
  name: string;
  value?: number; // Optional, might not always be present
  percentage: number; // Allocation percentage
}

// Matches the PortfolioData model in Python (part of the response)
export interface PortfolioData {
  total_value: number; 
  holdings: Holding[];
  allocations: Record<string, number>; // e.g., { "AAPL": 50, "MSFT": 50 }
  projections: {
    years: number[];
    values: number[];
  };
  recommendations: Array<{ // Keep consistent casing if possible, check backend output
    title: string;
    description: string;
  }>;
  analysis: string;
}

// Matches the structure returned by /api/generate-portfolio and /api/update-portfolio-from-chat
export interface PortfolioResponse {
  portfolioData: PortfolioData;
  userPreferences: UserProfile; // Contains the user profile used/updated
}

// For chat messages (already used in ChatInterface, keep consistent)
export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// For the backend chat history payload
export interface BackendChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

// Add any other shared types here as needed
