# AI-Assisted Wealth Management Platform

A complete wealth management application with Next.js frontend, FastAPI backend, and Supabase PostgreSQL database. Features full onboarding flow, portfolio proposal, account opening, funding, order execution, and intelligent rebalancing.

## 🏗️ Architecture

```
/portfolio-ai-stack/
├── apps/
│   ├── web/          # Next.js 14 frontend (Vercel)
│   └── api/          # FastAPI backend (Railway)
├── packages/
│   └── shared/       # Shared TypeScript types
├── infra/
│   ├── migrations/   # Supabase SQL migrations
│   └── seeds/        # Database seed scripts
├── frontend/portfolio-advisor/  # Existing frontend (kept for compatibility)
└── src/             # Existing Python modules (kept for compatibility)
```

## 🚀 Tech Stack

- **Frontend**: Next.js 14 (App Router), Tailwind CSS, shadcn/ui
- **Backend**: FastAPI (Python 3.11), uvicorn
- **Database**: Supabase PostgreSQL
- **Auth**: Kinde (planned), API key (current)
- **Providers**: Alpaca Paper (dev), Atomic Invest (prod)
- **AI**: Claude 3.5 Sonnet for explanations
- **Deployment**: Vercel (frontend) + Railway (backend)

## 🎯 Features

### Core Workflow
1. **Onboarding**: Legal agreements → KYC verification → account opening
2. **Portfolio Proposal**: Risk assessment → age-based glide path → AI rationale
3. **Funding**: ACH transfers (simulated for paper trading)
4. **Order Execution**: Market orders with real-time status tracking
5. **Portfolio Management**: Position tracking with drift-based rebalancing

### Advanced Features
- **5-Bucket Risk System**: Low → Below-Avg → Moderate → Above-Avg → High
- **Intelligent Rebalancing**: 5pp drift bands, 14-day minimum, $50 min orders
- **AI Explanations**: Claude-generated rationale for all recommendations
- **Provider Abstraction**: Easy switching between Alpaca Paper and Atomic
- **Kill Switch**: Global orders disable for emergency situations

## 📋 10-Step Setup Guide

### Step 1: Prerequisites
```bash
# Install required tools
node -v    # Requires Node.js 18+
python -v  # Requires Python 3.11+
git --version
```

### Step 2: Clone and Setup Repository
```bash
git clone https://github.com/your-username/portfolio-ai-stack.git
cd portfolio-ai-stack

# Install dependencies
npm install                                    # Root dependencies
cd apps/web && npm install && cd ../..        # Frontend dependencies
cd apps/api && pip install -r requirements.txt && cd ../..  # Backend dependencies
```

### Step 3: Configure Supabase Database
1. Create a new Supabase project at https://supabase.com
2. Go to Settings → API and copy your URL and anon key
3. Run the database migration:
```bash
# Using Supabase CLI (recommended)
npx supabase init
npx supabase db reset

# Or manually in Supabase SQL Editor
# Copy and paste /infra/migrations/0001_init.sql
# Copy and paste /infra/seeds/seed_glidepath.sql
```

### Step 4: Setup Alpaca Paper Trading (Development)
1. Sign up at https://alpaca.markets
2. Go to Paper Trading → Generate API Keys
3. Copy your API Key and Secret Key

### Step 5: Get Claude API Key (AI Explanations)
1. Visit https://console.anthropic.com
2. Create API key with sufficient credits
3. Copy your API key

### Step 6: Configure Environment Variables
```bash
# Root environment (copy and customize)
cp .env.example .env

# Backend environment
cp apps/api/.env.example apps/api/.env

# Frontend environment  
cp apps/web/.env.local.example apps/web/.env.local
```

Fill in your actual credentials:
```bash
# In .env and apps/api/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ANTHROPIC_API_KEY=your-claude-key
API_KEY=demo_key_for_development
PROVIDER=alpaca_paper
ORDERS_ENABLED=true

# In apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=demo_key_for_development
NEXT_PUBLIC_PROVIDER=alpaca_paper
```

### Step 7: Start the Backend API
```bash
cd apps/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Verify API is running
curl http://localhost:8000/health
# Should return: {"status":"healthy","provider":"alpaca_paper","orders_enabled":true}
```

### Step 8: Start the Frontend
```bash
cd apps/web
npm run dev

# Or use existing frontend location
cd frontend/portfolio-advisor
npm run dev
```

### Step 9: Test Complete Happy Path Flow
1. Visit http://localhost:3000
2. Complete risk questionnaire → get portfolio proposal
3. Visit http://localhost:3000/onboarding → accept agreements → verify KYC → open account
4. Visit http://localhost:3000/fund → simulate $1000 deposit
5. Visit http://localhost:3000/trade → create and submit initial portfolio orders
6. Visit http://localhost:3000/portfolio → view positions and check rebalancing

### Step 10: Deploy to Production (Optional)
```bash
# Deploy backend to Railway
railway login
railway new
railway add
railway up

# Deploy frontend to Vercel
npm install -g vercel
cd apps/web
vercel --prod

# Update environment variables in both platforms
```

## 🔧 API Endpoints

### Core Endpoints
- `POST /risk/score` - Calculate risk assessment from questionnaire
- `POST /portfolio/propose` - Generate portfolio proposal with AI rationale
- `POST /agreements/accept` - Record legal agreement acceptances
- `POST /kyc/start` - Initiate identity verification
- `POST /accounts/open` - Create brokerage account
- `POST /funding/transfer` - Process deposits/withdrawals
- `POST /orders/submit` - Execute trade intents
- `POST /rebalance/check` - Analyze portfolio drift and suggest trades

### Utility Endpoints
- `GET /health` - Service health check
- `POST /explain` - Generate AI explanations
- `POST /webhooks/provider` - Handle provider callbacks

## 🏦 Provider Integration

### Alpaca Paper (Current)
```python
from apps.api.providers.alpaca_paper import AlpacaPaperProvider

provider = AlpacaPaperProvider()
positions = await provider.fetch_positions(account_id)
orders = await provider.place_orders([{"symbol": "VTI", "side": "buy", "qty": 10}])
```

### Atomic Invest (Future)
```python
from apps.api.providers.atomic import AtomicProvider

# TODO: Implement when Atomic credentials are available
provider = AtomicProvider()
account_id = await provider.open_account(user_id)
```

Switch providers by changing `PROVIDER=atomic` in environment variables.

## 🔄 Rebalancing Logic

The system automatically checks for rebalancing opportunities:

```python
# Drift-based rebalancing rules:
- Trigger: Any asset class >5 percentage points from target
- Minimum: $50 per trade to avoid tiny orders  
- Frequency: ≥14 days between rebalances per account
- Method: Cash-first (use available cash before selling)
- Kill Switch: ORDERS_ENABLED=false disables all trading
```

## 🧠 AI Integration

Claude 3.5 Sonnet generates human-readable explanations:

```python
# Portfolio proposal rationale
"Based on your Moderate risk profile and age 35, we target 65% stocks / 20% bonds / 15% cash. 
Within equities, 40% is international for diversification."

# Rebalancing rationale  
"Your equities drifted to 72% vs target 65% after recent gains. We're trimming VTI and 
adding BND to keep risk on target."
```

## 🔒 Security & Compliance

- **Kill Switch**: `ORDERS_ENABLED=false` stops all order execution
- **Instrument Whitelist**: Only approved ETFs (VTI, VEA, BND, etc.)
- **Order Limits**: Maximum daily notional validation
- **Audit Trail**: All actions logged with user context
- **API Authentication**: Header-based keys (upgrade to Kinde later)

## 🧪 Testing

```bash
# Run backend tests
cd apps/api
python -m pytest tests/

# Run frontend tests  
cd apps/web
npm test

# Integration test: Happy path flow
python scripts/test_happy_path.py
```

## 📊 Monitoring

- **Health Checks**: `/health` endpoint for uptime monitoring
- **Error Tracking**: Sentry integration (configure SENTRY_DSN)
- **Performance**: Built-in FastAPI metrics
- **Audit Logs**: All user actions stored in `audit_log` table

## 🚨 Troubleshooting

### Common Issues

**"Database connection failed"**
```bash
# Check Supabase URL and key
curl -H "apikey: your-anon-key" "https://your-project.supabase.co/rest/v1/"
```

**"Alpaca authentication failed"**  
```bash
# Verify paper trading keys (not live trading!)
curl -H "APCA-API-KEY-ID: your-key" -H "APCA-API-SECRET-KEY: your-secret" \
  "https://paper-api.alpaca.markets/v2/account"
```

**"Orders not executing"**
```bash
# Check kill switch
grep ORDERS_ENABLED .env
# Should be: ORDERS_ENABLED=true
```

**"Frontend can't reach API"**
```bash
# Verify API is running
curl http://localhost:8000/health

# Check CORS settings in main.py
# Should include: allow_origins=["http://localhost:3000"]
```

## 🔄 Next Steps: Switching from Alpaca Paper to Atomic

When Atomic credentials become available:

1. **Update Environment Variables**:
```bash
PROVIDER=atomic
ATOMIC_API_KEY=your-production-key
ATOMIC_SECRET_KEY=your-production-secret
```

2. **Complete Atomic Provider Implementation**:
   - Fill in TODOs in `/apps/api/providers/atomic.py`
   - Implement real KYC, ACH transfers, and order routing
   - Add webhook handlers for account/order updates

3. **Update Frontend Messaging**:
   - Change "Paper Trading" banners to production messaging
   - Update legal disclaimers and risk warnings
   - Add real bank account linking UI

4. **Enhanced Security**:
   - Implement Kinde authentication
   - Add Row Level Security (RLS) policies in Supabase
   - Enable order validation and compliance checks

5. **Production Deployment**:
   - Deploy to Railway (backend) and Vercel (frontend)
   - Configure production database and monitoring
   - Set up automated backups and disaster recovery

## 📚 Documentation

- [API Documentation](apps/api/README.md)
- [Frontend Components](apps/web/README.md)  
- [Database Schema](infra/README.md)
- [Provider Integration Guide](docs/providers.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**