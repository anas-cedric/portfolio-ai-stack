# Cedric AI Portfolio Advisor Frontend

A Next.js-based frontend application for collecting user preferences and generating AI-powered portfolio recommendations.

## Overview

This application provides a user interface for the Cedric AI Portfolio Advisor system, allowing users to:

1. Input their financial information and investment preferences
2. Receive personalized portfolio recommendations
3. View detailed portfolio allocations, projections, and advice

## Current State

This is a frontend prototype that demonstrates the user experience for the portfolio recommendation system. Currently, it uses mock data to simulate the backend integration.

In a production environment, this would connect to the backend API that leverages:
- Claude 3.7 for portfolio reasoning
- LangChain/LangGraph for orchestration 
- Supabase for data storage
- Pinecone for vector embeddings

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend/portfolio-advisor
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Start the development server:
```bash
npm run dev
# or
yarn dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Next Steps for Integration

To fully integrate this frontend with the backend portfolio advisor system:

1. Create an API endpoint in the backend that accepts user preferences and returns portfolio recommendations
2. Update the form submission in `src/app/advisor/page.tsx` to call the backend API
3. Implement authentication using Kinde (as specified in the architecture)
4. Add real-time market data display from the Alpaca integration

## Features

- **Responsive design**: Works on mobile, tablet, and desktop
- **Form validation**: Ensures all required fields are properly completed
- **Interactive results**: Tab-based interface to explore different aspects of the recommendation
- **User-friendly visualizations**: Simple charts and progress bars for portfolio allocation

## Folder Structure

```
src/
├── app/                 # Next.js app router pages
│   ├── advisor/         # Portfolio advisor form page
│   └── page.tsx         # Landing page
├── components/          # Reusable UI components
│   └── PortfolioResults.tsx  # Results display component
└── styles/              # Global styles
```

## License

This project is proprietary and confidential. 
