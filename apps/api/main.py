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
import sys
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from supabase import create_client, Client

# Ensure project root is on sys.path so 'src' package is importable in all environments
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Load .env for local development
load_dotenv()

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

# Include routes from the portfolio generation module so /api/generate-portfolio-from-wizard is available
from src.api.portfolio_api import app as portfolio_generation_app
app.include_router(portfolio_generation_app.router)

# Include simulation (paper trading) endpoints
from src.api import sim_api as sim_router
app.include_router(sim_router.router, prefix="/api")

# Include model endpoints (model weights)
from src.api import model_api as model_router
app.include_router(model_router.router, prefix="/api")

# Health and root endpoints for platform health checks
START_TIME = datetime.utcnow()

@app.get("/health")
async def health():
    """Lightweight health check for Railway."""
    now = datetime.utcnow()
    uptime = (now - START_TIME).total_seconds()
    return {
        "status": "ok",
        "provider": PROVIDER,
        "orders_enabled": ORDERS_ENABLED,
        "database": "connected" if supabase else "disconnected",
        "uptime_seconds": uptime,
        "timestamp": now.isoformat() + "Z"
    }

@app.get("/")
async def root():
    return {"status": "ok", "message": "Wealth Management API"}

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
PROVIDER = os.getenv("PROVIDER", "alpaca_paper")  # alpaca_paper or atomic
ORDERS_ENABLED = os.getenv("ORDERS_ENABLED", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Initialize Supabase client (prefer service role key for server-side writes)
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
    # Accept both real UUIDs and frontend shorthand IDs like '1','2','3','4'
    agreement_ids: List[str]
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
    
    # Get valid API key from environment
    valid_key = os.getenv("VALID_API_KEY", "demo_key")
    
    # In development, accept demo_key
    if os.getenv("RAILWAY_ENVIRONMENT") != "production" and x_api_key == "demo_key":
        return x_api_key
    
    # In production, validate against stored key
    if x_api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
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

async def call_openai_explain(template: str, context: Dict[str, Any]) -> str:
    """Call OpenAI API for explanations"""
    if not OPENAI_API_KEY:
        return "AI explanation unavailable"
    
    # Build prompt based on template
    prompts = {
        "proposal": f"Based on risk profile ({context.get('bucket')}) and age ({context.get('age')}), "
                   f"explain the portfolio allocation: {context.get('allocation')}. Keep response under 200 words.",
        "rebalance": f"Explain why rebalancing from {context.get('current')} to {context.get('target')} "
                    f"is recommended due to {context.get('drift')}% drift. Keep response under 200 words."
    }
    
    prompt = prompts.get(template, "Provide investment rationale")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "o3-mini",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"OpenAI API error: {e}")
    
    return "Portfolio allocation optimized for your risk profile and investment horizon."

# ---------- Agreements helpers ----------
def _is_uuid(val: str) -> bool:
    try:
        UUID(str(val))
        return True
    except Exception:
        return False

# Default agreements used by the frontend UI (ids '1'..'4').
# If these rows are not present in agreement_version, we will create them on demand.
DEFAULT_AGREEMENTS: Dict[str, Dict[str, str]] = {
    "1": {"kind": "terms", "version": "1.0", "url": "/legal/terms-v1.pdf"},
    "2": {"kind": "privacy", "version": "1.0", "url": "/legal/privacy-v1.pdf"},
    "3": {"kind": "advisory", "version": "1.0", "url": "/legal/advisory-v1.pdf"},
    "4": {"kind": "esign", "version": "1.0", "url": "/legal/esign-v1.pdf"},
}

def _ensure_agreement_version(kind: str, version: str, url: Optional[str]) -> str:
    """Return the UUID of an agreement_version row for (kind, version), creating it if missing.
    If Supabase is not configured, return a generated UUID to allow the flow to proceed.
    """
    if not supabase:
        return str(uuid4())

    # Try to find an existing version
    try:
        sel = supabase.table("agreement_version").select("id").eq("kind", kind).eq("version", version).limit(1).execute()
        if sel.data:
            return sel.data[0]["id"]
        # Insert a new version with immediate effectiveness
        ins = supabase.table("agreement_version").insert({
            "kind": kind,
            "version": version,
            "url": url,
            "effective_at": datetime.utcnow().isoformat() + "Z",
        }).execute()
        if ins.data and len(ins.data) > 0:
            return ins.data[0]["id"]
        else:
            # If insert didn't return data, generate a UUID as fallback
            print(f"Insert succeeded but no data returned for {kind} {version}")
            return str(uuid4())
    except Exception as e:
        # As a last resort, do not block the flow
        print(f"agreement_version ensure failed for {kind} {version}: {e}")
        return str(uuid4())

def _ensure_app_user(user_id: str) -> None:
    """Ensure an app_user row exists for the given user_id.
    The schema requires a non-null unique email, so for demo we synthesize one.
    """
    if not supabase:
        return
    try:
        # Check if user exists
        sel = (
            supabase.table("app_user")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if sel.data:
            return
        # Insert demo user
        email = f"demo+{user_id}@example.com"
        supabase.table("app_user").insert({
            "id": user_id,
            "email": email,
            "full_name": None,
        }).execute()
    except Exception as e:
        print(f"_ensure_app_user failed for {user_id}: {e}")

# ==================== Routes ====================

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
    rationale = await call_openai_explain("proposal", {
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
    acceptances: List[Dict[str, Any]] = []

    # Ensure user exists to satisfy FK constraints
    _ensure_app_user(str(request.user_id))

    # Resolve incoming IDs to real agreement_version UUIDs
    resolved_ids: List[str] = []
    for raw_id in request.agreement_ids:
        sid = str(raw_id)
        if _is_uuid(sid):
            resolved_ids.append(sid)
        elif sid in DEFAULT_AGREEMENTS:
            meta = DEFAULT_AGREEMENTS[sid]
            resolved_ids.append(_ensure_agreement_version(meta["kind"], meta["version"], meta.get("url")))
        else:
            # Unknown identifier; skip but log
            print(f"Unknown agreement identifier: {sid}")

    if not resolved_ids:
        raise HTTPException(status_code=400, detail="No valid agreement identifiers provided")

    for agreement_uuid in resolved_ids:
        if supabase:
            try:
                result = supabase.table("agreement_acceptance").insert({
                    "user_id": str(request.user_id),
                    "agreement_id": agreement_uuid,
                    "ip": request.ip,
                    "user_agent": request.user_agent,
                }).execute()
                if result.data and len(result.data) > 0:
                    acceptances.append(result.data[0])
                else:
                    # If insert succeeded but no data returned, create a mock response
                    acceptances.append({
                        "id": str(uuid4()),
                        "user_id": str(request.user_id),
                        "agreement_id": agreement_uuid,
                        "accepted_at": datetime.utcnow().isoformat() + "Z",
                    })
            except Exception as e:
                # If FK fails or any other DB error occurs, continue after logging
                print(f"Failed to insert agreement_acceptance for {agreement_uuid}: {e}")
        else:
            acceptances.append({
                "id": str(uuid4()),
                "agreement_id": agreement_uuid,
                "accepted_at": datetime.utcnow().isoformat() + "Z",
            })

    return {"acceptances": acceptances}

@app.post("/kyc/start")
async def start_kyc(
    request: KYCStartRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start KYC process"""
    # Ensure user exists to satisfy FK constraints
    _ensure_app_user(str(request.user_id))

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
    # Ensure user exists to satisfy FK constraints
    _ensure_app_user(str(request.user_id))

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
    # Ensure user exists to satisfy FK constraints
    _ensure_app_user(str(request.user_id))

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
        rationale = await call_openai_explain("rebalance", {
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
    explanation = await call_openai_explain(request.template, request.context)
    return {"explanation": explanation}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)