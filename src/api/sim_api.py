"""
Simulation (paper trading) API endpoints.

Endpoints under /api/v1/sim/*
- POST /api/v1/sim/accounts
- POST /api/v1/sim/accounts/{account_id}/init-portfolio
- GET  /api/v1/sim/accounts/{account_id}
"""
from __future__ import annotations

import os
from datetime import datetime, date
from uuid import UUID
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, Field
from supabase import create_client, Client

router = APIRouter()

# Supabase (server-side writes)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
supabase: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None


async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return x_api_key


# ---------------- Models ----------------
class SimAccountCreate(BaseModel):
    user_id: UUID
    start_cash_cents: int = Field(..., ge=0)

class InitPortfolioRequest(BaseModel):
    targets: Dict[str, float]  # symbol -> weight (0..1 or 0..100)
    as_of: date
    idempotency_key: Optional[str] = None

class SimAccountSummary(BaseModel):
    account_id: UUID
    cash_cents: int
    as_of: date
    holdings: List[Dict[str, Any]]
    market_value_cents: int
    total_value_cents: int


# ---------------- Helpers ----------------
IGNORE_SYMBOLS = {"CASH", "Cash"}


def _normalize_targets(targets: Dict[str, float]) -> Dict[str, float]:
    # Drop cash keys & non-positive weights
    filtered = {s: float(w) for s, w in targets.items() if s not in IGNORE_SYMBOLS and float(w) > 0}
    if not filtered:
        raise HTTPException(status_code=400, detail="No positive target weights provided.")
    total = sum(filtered.values())
    if total > 1.5:  # assume percentages
        filtered = {s: w / 100.0 for s, w in filtered.items()}
        total = sum(filtered.values())
    if total <= 0:
        raise HTTPException(status_code=400, detail="Target weights sum must be > 0")
    # Renormalize to 1.0
    return {s: (w / total) for s, w in filtered.items()}


def _get_price(symbol: str, d: date) -> Optional[float]:
    res = supabase.table("mkt_price").select("close").eq("symbol", symbol).eq("date", d.isoformat()).limit(1).execute()
    if res.data:
        return float(res.data[0]["close"])
    return None


def _get_latest_price(symbol: str, up_to: Optional[date]) -> Optional[Dict[str, Any]]:
    q = supabase.table("mkt_price").select("date, close").eq("symbol", symbol)
    if up_to:
        q = q.lte("date", up_to.isoformat())
    res = q.order("date", desc=True).limit(1).execute()
    if res.data:
        row = res.data[0]
        # Normalize date to ISO string regardless of DB driver's return type
        d = row["date"]
        d_iso = d if isinstance(d, str) else str(d)
        return {"date": d_iso, "close": float(row["close"]) }
    return None


# ---------------- Endpoints ----------------
@router.post("/v1/sim/accounts")
async def create_sim_account(payload: SimAccountCreate, api_key: str = Depends(verify_api_key)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    acc = supabase.table("sim_account").insert({
        "user_id": str(payload.user_id),
        "start_cash_cents": int(payload.start_cash_cents),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }).execute()
    if not acc.data:
        raise HTTPException(status_code=500, detail=f"Failed to create sim_account: {acc.error}")

    account_id = acc.data[0]["id"]
    cash = supabase.table("sim_cash").insert({
        "account_id": account_id,
        "cents": int(payload.start_cash_cents),
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }).execute()
    if cash.error:
        supabase.table("sim_account").delete().eq("id", account_id).execute()
        raise HTTPException(status_code=500, detail=f"Failed to init sim_cash: {cash.error}")

    return {"account_id": account_id, "cash_cents": int(payload.start_cash_cents)}


@router.post("/v1/sim/accounts/{account_id}/init-portfolio")
async def init_portfolio(account_id: UUID, payload: InitPortfolioRequest, api_key: str = Depends(verify_api_key)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    acc = supabase.table("sim_account").select("id").eq("id", str(account_id)).limit(1).execute()
    if not acc.data:
        raise HTTPException(status_code=404, detail="Account not found")

    cash_row = supabase.table("sim_cash").select("cents").eq("account_id", str(account_id)).limit(1).execute()
    if not cash_row.data:
        raise HTTPException(status_code=400, detail="Account cash not initialized")
    cash_cents = int(cash_row.data[0]["cents"])  # available

    targets = _normalize_targets(payload.targets)
    as_of = payload.as_of
    idem_base = payload.idempotency_key or f"init-{as_of.isoformat()}"

    # Prices
    prices: Dict[str, float] = {}
    missing: List[str] = []
    for sym in targets.keys():
        p = _get_price(sym, as_of)
        if p is None:
            missing.append(sym)
        else:
            prices[sym] = p
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing EOD prices for {as_of}: {', '.join(missing)}")

    total_cash = cash_cents / 100.0
    trades: List[Dict[str, Any]] = []
    spent = 0.0

    for sym, w in targets.items():
        tgt_val = total_cash * w
        price = prices[sym]
        if price <= 0:
            continue
        qty = max(0.0, tgt_val / price)
        if qty <= 0:
            continue
        cost = qty * price
        spent += cost
        trades.append({
            "account_id": str(account_id),
            "ts": datetime.combine(as_of, datetime.min.time()).isoformat() + "Z",
            "symbol": sym,
            "side": "BUY",
            "qty": qty,
            "price": price,
            "reason": "init",
            "idempotency_key": f"{idem_base}-{sym}",
        })

    if not trades:
        raise HTTPException(status_code=400, detail="No trades generated (check targets/prices/cash)")

    # Idempotency filter
    existing = supabase.table("sim_trade").select("idempotency_key").eq("account_id", str(account_id)).execute()
    existing_keys = {row["idempotency_key"] for row in (existing.data or [])}
    new_trades = [t for t in trades if t["idempotency_key"] not in existing_keys]

    if new_trades:
        ins = supabase.table("sim_trade").insert(new_trades).execute()
        if ins.error:
            raise HTTPException(status_code=500, detail=f"Failed to insert trades: {ins.error}")

    # Holdings upsert
    symbols = [t["symbol"] for t in trades]
    hold = supabase.table("sim_holding").select("symbol, qty, avg_price").eq("account_id", str(account_id)).in_("symbol", symbols).execute()
    existing_map = {r["symbol"]: r for r in (hold.data or [])}

    upserts = []
    for t in trades:
        sym = t["symbol"]
        buy_qty = float(t["qty"])
        buy_price = float(t["price"])
        if sym in existing_map and float(existing_map[sym]["qty"]) > 0:
            old_qty = float(existing_map[sym]["qty"])
            old_avg = float(existing_map[sym]["avg_price"])
            new_qty = old_qty + buy_qty
            new_avg = (old_qty * old_avg + buy_qty * buy_price) / new_qty
        else:
            new_qty = buy_qty
            new_avg = buy_price
        upserts.append({
            "account_id": str(account_id),
            "symbol": sym,
            "qty": new_qty,
            "avg_price": new_avg,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })

    if upserts:
        up = supabase.table("sim_holding").upsert(upserts, on_conflict="account_id,symbol").execute()
        if up.error:
            raise HTTPException(status_code=500, detail=f"Failed to upsert holdings: {up.error}")

    # Cash update
    new_cash_cents = max(0, int(round((total_cash - spent) * 100)))
    upd = supabase.table("sim_cash").update({
        "cents": new_cash_cents,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }).eq("account_id", str(account_id)).execute()
    if upd.error:
        raise HTTPException(status_code=500, detail=f"Failed to update cash: {upd.error}")

    return {"status": "ok", "trades_inserted": len(new_trades), "cash_cents": new_cash_cents}


@router.get("/v1/sim/accounts/{account_id}", response_model=SimAccountSummary)
async def get_sim_account(account_id: UUID, as_of: Optional[date] = Query(default=None), api_key: str = Depends(verify_api_key)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    cash_row = supabase.table("sim_cash").select("cents").eq("account_id", str(account_id)).limit(1).execute()
    if not cash_row.data:
        raise HTTPException(status_code=404, detail="Account not found or no cash")
    cash_cents = int(cash_row.data[0]["cents"]) 

    hold = supabase.table("sim_holding").select("symbol, qty, avg_price").eq("account_id", str(account_id)).execute()
    holdings = hold.data or []

    detailed: List[Dict[str, Any]] = []
    equity_value = 0.0
    price_date: Optional[str] = None

    for h in holdings:
        sym = h["symbol"]
        qty = float(h["qty"]) if h["qty"] is not None else 0.0
        avg_price = float(h["avg_price"]) if h["avg_price"] is not None else 0.0
        price_row = _get_latest_price(sym, as_of)
        price = float(price_row["close"]) if price_row else 0.0
        if price_row and not price_date:
            price_date = price_row["date"]
        mv = qty * price
        equity_value += mv
        detailed.append({
            "symbol": sym,
            "qty": qty,
            "avg_price": avg_price,
            "price": price,
            "market_value": mv,
        })

    total_value = equity_value + (cash_cents / 100.0)
    resolved_as_of = as_of or (price_date and date.fromisoformat(price_date)) or date.today()
    return {
        "account_id": str(account_id),
        "cash_cents": cash_cents,
        "as_of": resolved_as_of,
        "holdings": detailed,
        "market_value_cents": int(round(equity_value * 100)),
        "total_value_cents": int(round(total_value * 100)),
    }
