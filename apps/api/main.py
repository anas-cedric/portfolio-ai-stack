"""
FastAPI backend for AI-assisted wealth management app
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from supabase import create_client, Client

# Initialize FastAPI app
app = FastAPI(title="Wealth Management API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
PROVIDER = os.getenv("PROVIDER", "alpaca_paper")  # alpaca_paper or atomic
ORDERS_ENABLED = os.getenv("ORDERS_ENABLED", "true").lower() == "true"
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# ==================== Models ====================

class RiskBucket(str, Enum):
    LOW = "Low"
    BELOW_AVG = "Below-Avg"
    MODERATE = "Moderate"
    ABOVE_AVG = "Above-Avg"
    HIGH = "High"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class AccountStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class TransferDirection(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class RiskAssessmentRequest(BaseModel):
    user_id: UUID
    answers: Dict[str, Any]
    method: str = "grable_lytton"

class PortfolioProposalRequest(BaseModel):
    user_id: UUID
    age: int
    risk_bucket: Optional[RiskBucket] = None

class AgreementAcceptRequest(BaseModel):
    user_id: UUID
    agreement_ids: List[UUID]
    ip: Optional[str] = None
    user_agent: Optional[str] = None

class KYCStartRequest(BaseModel):
    user_id: UUID
    personal_info: Dict[str, Any]

class AccountOpenRequest(BaseModel):
    user_id: UUID
    kyc_application_id: UUID

class TransferRequest(BaseModel):
    user_id: UUID
    account_id: UUID
    amount_cents: int
    direction: TransferDirection

class TradeIntentItem(BaseModel):
    symbol: str
    side: OrderSide
    qty: float
    notional: Optional[float] = None

class OrderSubmitRequest(BaseModel):
    user_id: UUID
    account_id: UUID
    trade_intent_id: UUID

class RebalanceCheckRequest(BaseModel):
    account_id: UUID
    force_check: bool = False

class ExplainRequest(BaseModel):
    template: str
    context: Dict[str, Any]

# ==================== Dependency ====================

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for authentication"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    # In production, validate against stored keys
    return x_api_key

# ==================== Helper Functions ====================

def calculate_risk_score(answers: Dict[str, Any]) -> tuple[int, RiskBucket]:
    """Calculate risk score from questionnaire answers"""
    # Implement your existing Grable-Lytton scoring logic here
    # This is a simplified version
    score = sum(int(v) for v in answers.values() if isinstance(v, (int, str)) and str(v).isdigit())
    
    if score <= 18:
        bucket = RiskBucket.LOW
    elif score <= 22:
        bucket = RiskBucket.BELOW_AVG
    elif score <= 28:
        bucket = RiskBucket.MODERATE
    elif score <= 32:
        bucket = RiskBucket.ABOVE_AVG
    else:
        bucket = RiskBucket.HIGH
    
    return score, bucket

def get_glide_path_allocation(bucket: RiskBucket, age: int) -> Dict[str, float]:
    """Get allocation based on risk bucket and age"""
    # Import your existing glide path data
    from src.data.glide_path_allocations import GLIDE_PATH_ALLOCATIONS
    
    bucket_data = GLIDE_PATH_ALLOCATIONS.get(bucket.value, {})
    
    # Find the appropriate age range
    for (age_from, age_to), allocation in bucket_data.items():
        if age_from <= age <= age_to:
            return allocation
    
    # Default allocation if age not found
    return bucket_data.get((33, 37), {})

async def call_claude_explain(template: str, context: Dict[str, Any]) -> str:
    """Call Claude API for explanations"""
    if not CLAUDE_API_KEY:
        return "AI explanation unavailable"
    
    # Build prompt based on template
    prompts = {
        "proposal": f"Based on risk profile ({context.get('bucket')}) and age ({context.get('age')}), "
                   f"explain the portfolio allocation: {context.get('allocation')}",
        "rebalance": f"Explain why rebalancing from {context.get('current')} to {context.get('target')} "
                    f"is recommended due to {context.get('drift')}% drift"
    }
    
    prompt = prompts.get(template, "Provide investment rationale")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("content", [{}])[0].get("text", "")
        except Exception as e:
            print(f"Claude API error: {e}")
    
    return "Portfolio allocation optimized for your risk profile and investment horizon."

# ==================== Routes ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "provider": PROVIDER,
        "orders_enabled": ORDERS_ENABLED,
        "database": "connected" if supabase else "disconnected"
    }

@app.post("/risk/score")
async def score_risk_assessment(
    request: RiskAssessmentRequest,
    api_key: str = Depends(verify_api_key)
):
    """Calculate and store risk assessment"""
    score, bucket = calculate_risk_score(request.answers)
    
    if supabase:
        # Store in database
        result = supabase.table("risk_assessment").insert({
            "user_id": str(request.user_id),
            "method": request.method,
            "raw_answers": request.answers,
            "score": score,
            "bucket": bucket.value
        }).execute()
        
        return {
            "id": result.data[0]["id"],
            "score": score,
            "bucket": bucket.value,
            "created_at": result.data[0]["created_at"]
        }
    
    return {
        "id": str(uuid4()),
        "score": score,
        "bucket": bucket.value,
        "created_at": datetime.utcnow().isoformat()
    }

@app.post("/portfolio/propose")
async def propose_portfolio(
    request: PortfolioProposalRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate portfolio proposal based on risk and age"""
    # Get risk bucket if not provided
    if not request.risk_bucket and supabase:
        # Get latest risk assessment for user
        result = supabase.table("risk_assessment")\
            .select("bucket")\
            .eq("user_id", str(request.user_id))\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            request.risk_bucket = RiskBucket(result.data[0]["bucket"])
    
    if not request.risk_bucket:
        request.risk_bucket = RiskBucket.MODERATE
    
    # Get allocation from glide path
    allocation = get_glide_path_allocation(request.risk_bucket, request.age)
    
    # Build target portfolio
    targets = {}
    for symbol, weight in allocation.items():
        if symbol.upper() in ["VTI", "VEA", "VWO", "BND", "BNDX", "VNQ", "VNQI", "VTIP", "VBR", "VUG", "VSS"]:
            targets[symbol] = weight * 100  # Convert to percentage
    
    # Generate rationale
    rationale = await call_claude_explain("proposal", {
        "bucket": request.risk_bucket.value,
        "age": request.age,
        "allocation": allocation
    })
    
    if supabase:
        # Store proposal
        result = supabase.table("portfolio_proposal").insert({
            "user_id": str(request.user_id),
            "rationale": rationale,
            "targets": targets,
            "status": "awaiting_user"
        }).execute()
        
        proposal_id = result.data[0]["id"]
    else:
        proposal_id = str(uuid4())
    
    return {
        "id": proposal_id,
        "targets": targets,
        "rationale": rationale,
        "risk_bucket": request.risk_bucket.value,
        "status": "awaiting_user"
    }

@app.post("/agreements/accept")
async def accept_agreements(
    request: AgreementAcceptRequest,
    api_key: str = Depends(verify_api_key)
):
    """Record agreement acceptances"""
    acceptances = []
    
    for agreement_id in request.agreement_ids:
        if supabase:
            result = supabase.table("agreement_acceptance").insert({
                "user_id": str(request.user_id),
                "agreement_id": str(agreement_id),
                "ip": request.ip,
                "user_agent": request.user_agent
            }).execute()
            acceptances.append(result.data[0])
        else:
            acceptances.append({
                "id": str(uuid4()),
                "agreement_id": str(agreement_id),
                "accepted_at": datetime.utcnow().isoformat()
            })
    
    return {"acceptances": acceptances}

@app.post("/kyc/start")
async def start_kyc(
    request: KYCStartRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start KYC process"""
    if PROVIDER == "alpaca_paper":
        # For paper trading, auto-approve
        status = "approved"
        kyc_data = {
            "provider": "alpaca_paper",
            "auto_approved": True,
            **request.personal_info
        }
    else:
        # For Atomic, this would call their API
        status = "pending"
        kyc_data = {
            "provider": "atomic",
            "submitted_at": datetime.utcnow().isoformat(),
            **request.personal_info
        }
    
    if supabase:
        result = supabase.table("kyc_application").insert({
            "user_id": str(request.user_id),
            "provider": PROVIDER,
            "status": status,
            "payload": kyc_data
        }).execute()
        
        return result.data[0]
    
    return {
        "id": str(uuid4()),
        "status": status,
        "provider": PROVIDER,
        "created_at": datetime.utcnow().isoformat()
    }

@app.post("/accounts/open")
async def open_account(
    request: AccountOpenRequest,
    api_key: str = Depends(verify_api_key)
):
    """Open brokerage account"""
    # Import provider
    if PROVIDER == "alpaca_paper":
        from apps.api.providers.alpaca_paper import AlpacaPaperProvider
        provider = AlpacaPaperProvider()
    else:
        from apps.api.providers.atomic import AtomicProvider
        provider = AtomicProvider()
    
    # Open account with provider
    external_account_id = await provider.open_account(str(request.user_id))
    
    if supabase:
        result = supabase.table("brokerage_account").insert({
            "user_id": str(request.user_id),
            "provider": PROVIDER,
            "external_account_id": external_account_id,
            "status": "active" if PROVIDER == "alpaca_paper" else "pending"
        }).execute()
        
        return result.data[0]
    
    return {
        "id": str(uuid4()),
        "external_account_id": external_account_id,
        "status": "active",
        "provider": PROVIDER
    }

@app.post("/funding/transfer")
async def create_transfer(
    request: TransferRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create funding transfer"""
    if PROVIDER == "alpaca_paper":
        # Simulate instant deposit for paper trading
        status = "completed"
        await asyncio.sleep(0.5)  # Simulate processing
    else:
        # For Atomic, would initiate ACH
        status = "pending"
    
    if supabase:
        result = supabase.table("transfer").insert({
            "user_id": str(request.user_id),
            "account_id": str(request.account_id),
            "direction": request.direction.value,
            "amount_cents": request.amount_cents,
            "status": status,
            "provider_ref": f"{PROVIDER}_{uuid4()}"
        }).execute()
        
        return result.data[0]
    
    return {
        "id": str(uuid4()),
        "amount_cents": request.amount_cents,
        "status": status,
        "created_at": datetime.utcnow().isoformat()
    }

@app.post("/orders/submit")
async def submit_orders(
    request: OrderSubmitRequest,
    api_key: str = Depends(verify_api_key)
):
    """Submit trade intent orders"""
    if not ORDERS_ENABLED:
        raise HTTPException(status_code=503, detail="Orders are currently disabled")
    
    # Get trade intent
    if supabase:
        result = supabase.table("trade_intent")\
            .select("*")\
            .eq("id", str(request.trade_intent_id))\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Trade intent not found")
        
        trade_intent = result.data
    else:
        # Mock data for testing
        trade_intent = {
            "items": [
                {"symbol": "VTI", "side": "buy", "qty": 10},
                {"symbol": "BND", "side": "buy", "qty": 5}
            ]
        }
    
    # Submit orders through provider
    if PROVIDER == "alpaca_paper":
        from apps.api.providers.alpaca_paper import AlpacaPaperProvider
        provider = AlpacaPaperProvider()
        order_ids = await provider.place_orders(trade_intent["items"])
    else:
        order_ids = {item["symbol"]: str(uuid4()) for item in trade_intent["items"]}
    
    # Update trade intent status
    if supabase:
        supabase.table("trade_intent").update({
            "status": "submitted",
            "provider_order_ids": order_ids,
            "submitted_at": datetime.utcnow().isoformat()
        }).eq("id", str(request.trade_intent_id)).execute()
        
        # Log audit
        supabase.table("audit_log").insert({
            "user_id": str(request.user_id),
            "actor": "system",
            "action": "order.submitted",
            "context": {"trade_intent_id": str(request.trade_intent_id), "order_ids": order_ids}
        }).execute()
    
    return {
        "trade_intent_id": str(request.trade_intent_id),
        "order_ids": order_ids,
        "status": "submitted"
    }

@app.post("/rebalance/check")
async def check_rebalance(
    request: RebalanceCheckRequest,
    api_key: str = Depends(verify_api_key)
):
    """Check if rebalancing is needed"""
    # Get current positions
    if supabase:
        # Get latest position snapshot
        position_result = supabase.table("position_snapshot")\
            .select("positions")\
            .eq("account_id", str(request.account_id))\
            .order("as_of", desc=True)\
            .limit(1)\
            .execute()
        
        if not position_result.data:
            return {"needs_rebalance": False, "reason": "No positions found"}
        
        positions = position_result.data[0]["positions"]
        
        # Get target allocation
        account_result = supabase.table("brokerage_account")\
            .select("user_id")\
            .eq("id", str(request.account_id))\
            .single()\
            .execute()
        
        proposal_result = supabase.table("portfolio_proposal")\
            .select("targets")\
            .eq("user_id", account_result.data["user_id"])\
            .eq("status", "approved")\
            .order("approved_at", desc=True)\
            .limit(1)\
            .execute()
        
        if not proposal_result.data:
            return {"needs_rebalance": False, "reason": "No approved proposal found"}
        
        targets = proposal_result.data[0]["targets"]
    else:
        # Mock data
        positions = [
            {"symbol": "VTI", "qty": 100, "market_value": 22000},
            {"symbol": "BND", "qty": 50, "market_value": 4000}
        ]
        targets = {"VTI": 60, "BND": 40}
    
    # Calculate current weights
    total_value = sum(p["market_value"] for p in positions)
    current_weights = {p["symbol"]: (p["market_value"] / total_value * 100) for p in positions}
    
    # Check drift (5 percentage point threshold)
    max_drift = 0
    rebalance_trades = []
    
    for symbol, target_weight in targets.items():
        current_weight = current_weights.get(symbol, 0)
        drift = abs(current_weight - target_weight)
        
        if drift > 5:  # 5 percentage point drift threshold
            max_drift = max(max_drift, drift)
            
            # Calculate rebalance trade
            target_value = total_value * (target_weight / 100)
            current_value = current_weight * total_value / 100
            trade_value = target_value - current_value
            
            if abs(trade_value) >= 50:  # Minimum $50 trade
                rebalance_trades.append({
                    "symbol": symbol,
                    "side": "buy" if trade_value > 0 else "sell",
                    "notional": abs(trade_value),
                    "current_weight": round(current_weight, 2),
                    "target_weight": target_weight
                })
    
    # Check 14-day spacing
    if supabase and rebalance_trades:
        last_rebalance = supabase.table("trade_intent")\
            .select("created_at")\
            .eq("account_id", str(request.account_id))\
            .eq("status", "filled")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if last_rebalance.data:
            last_date = datetime.fromisoformat(last_rebalance.data[0]["created_at"].replace("Z", "+00:00"))
            if datetime.utcnow() - last_date < timedelta(days=14):
                return {
                    "needs_rebalance": False,
                    "reason": "Last rebalance was less than 14 days ago",
                    "next_eligible": (last_date + timedelta(days=14)).isoformat()
                }
    
    if rebalance_trades:
        # Generate explanation
        rationale = await call_claude_explain("rebalance", {
            "current": current_weights,
            "target": targets,
            "drift": max_drift
        })
        
        # Create staged trade intent
        if supabase:
            result = supabase.table("trade_intent").insert({
                "user_id": account_result.data["user_id"],
                "account_id": str(request.account_id),
                "items": rebalance_trades,
                "status": "staged"
            }).execute()
            
            trade_intent_id = result.data[0]["id"]
        else:
            trade_intent_id = str(uuid4())
        
        return {
            "needs_rebalance": True,
            "max_drift": round(max_drift, 2),
            "trades": rebalance_trades,
            "rationale": rationale,
            "trade_intent_id": trade_intent_id
        }
    
    return {
        "needs_rebalance": False,
        "reason": "Portfolio is within drift tolerance"
    }

@app.post("/webhooks/provider")
async def handle_provider_webhook(request: Request):
    """Handle provider webhooks"""
    body = await request.json()
    
    event_type = body.get("event_type")
    
    if event_type == "order.fill":
        # Update trade intent status
        if supabase:
            order_id = body.get("order_id")
            supabase.table("trade_intent").update({
                "status": "filled",
                "filled_at": datetime.utcnow().isoformat()
            }).contains("provider_order_ids", {body.get("symbol"): order_id}).execute()
    
    elif event_type == "kyc.status_changed":
        # Update KYC application
        if supabase:
            supabase.table("kyc_application").update({
                "status": body.get("status")
            }).eq("external_id", body.get("application_id")).execute()
    
    elif event_type == "account.position_update":
        # Store position snapshot
        if supabase:
            supabase.table("position_snapshot").insert({
                "account_id": body.get("account_id"),
                "as_of": datetime.utcnow().isoformat(),
                "positions": body.get("positions")
            }).execute()
    
    return {"status": "processed"}

@app.post("/explain")
async def generate_explanation(
    request: ExplainRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate AI explanations"""
    explanation = await call_claude_explain(request.template, request.context)
    return {"explanation": explanation}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)