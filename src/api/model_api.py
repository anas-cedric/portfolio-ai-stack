"""
Model-related endpoints

GET /v1/portfolios/model?bucket=Moderate&version=v1
Returns model weights for a given risk bucket and model version.
"""
from __future__ import annotations

import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from supabase import create_client, Client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
supabase: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

RISK_BUCKETS = {"Low","Below-Avg","Moderate","Above-Avg","High"}

async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return x_api_key

@router.get("/v1/portfolios/model")
async def get_model_weights(
    bucket: str = Query(..., description="Risk bucket"),
    version: str = Query("v1", description="Model version"),
    api_key: str = Depends(verify_api_key),
):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    if bucket not in RISK_BUCKETS:
        raise HTTPException(status_code=400, detail=f"Invalid bucket. Must be one of {sorted(RISK_BUCKETS)}")

    res = supabase.table("model_weights").select("symbol, weight").eq("model_version", version).eq("bucket", bucket).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="No model weights found")

    weights: Dict[str, float] = {r["symbol"]: float(r["weight"]) for r in rows}
    total = sum(weights.values())

    return {"model_version": version, "bucket": bucket, "weights": weights, "sum": total}
