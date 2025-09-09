import hashlib
from typing import Dict, List, Any, Optional, Tuple

# Symbols we ignore for trading math (treated as passive buckets)
IGNORED_TICKERS = {"CASH"}


def decision_hash(inputs: Dict[str, Any]) -> str:
    """Create a stable hash for idempotency from a dict of simple types."""
    # Canonicalize: sort keys recursively and stringify
    def _serialize(obj):
        if isinstance(obj, dict):
            return {k: _serialize(obj[k]) for k in sorted(obj.keys())}
        if isinstance(obj, list):
            return [_serialize(x) for x in obj]
        return obj

    canonical = _serialize(inputs)
    payload = str(canonical).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _weights_from_holdings(holdings: List[Dict[str, Any]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Build (current_weights %, current_values $) from holdings.
    If percentage not present, derive from values.
    """
    values: Dict[str, float] = {}
    total = 0.0
    for h in holdings or []:
        ticker = str(h.get("ticker", "")).upper()
        if not ticker:
            continue
        val = float(h.get("value", 0) or 0)
        values[ticker] = values.get(ticker, 0.0) + val
        total += val

    weights: Dict[str, float] = {}
    if total > 0:
        for t, v in values.items():
            weights[t] = round(100.0 * v / total, 6)
    else:
        # If total is zero, fall back to provided percentages if available
        for h in holdings or []:
            t = str(h.get("ticker", "")).upper()
            pct = float(h.get("percentage", 0) or 0)
            weights[t] = pct
            values[t] = float(h.get("value", 0) or 0)

    return weights, values


def _drift(current_w: Dict[str, float], target_w: Dict[str, float]) -> Tuple[Dict[str, float], float, str]:
    """Return per-symbol drift map (current - target), max drift magnitude, and ticker."""
    tickers = set(current_w.keys()) | set(target_w.keys())
    drift: Dict[str, float] = {}
    max_abs = 0.0
    max_sym = ""
    for t in tickers:
        if t in IGNORED_TICKERS:
            continue
        c = float(current_w.get(t, 0) or 0)
        tgt = float(target_w.get(t, 0) or 0)
        d = c - tgt
        drift[t] = d
        if abs(d) > max_abs:
            max_abs = abs(d)
            max_sym = t
    return drift, max_abs, max_sym


def _fetch_prices_if_needed(tickers: List[str], prices: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Fetch prices via Alpaca if not provided. Gracefully degrade on failure."""
    result: Dict[str, float] = {}
    if prices:
        for t, p in prices.items():
            try:
                result[str(t).upper()] = float(p)
            except Exception:
                pass
    try:
        from src.data_integration.alpaca_market_data import AlpacaMarketData  # type: ignore
        client = AlpacaMarketData()
        for t in tickers:
            if t in IGNORED_TICKERS:
                continue
            if t in result and result[t] > 0:
                continue
            try:
                p = client.get_current_price(t)
                if p:
                    result[t] = float(p)
            except Exception:
                continue
    except Exception:
        # Alpaca not configured; return whatever we have
        pass
    return result


def _apply_turnover_cap(deltas: Dict[str, float], portfolio_value: float, turnover_cap: float) -> Tuple[Dict[str, float], float]:
    """Scale deltas so that sum(|delta|)/V <= cap. Returns (scaled_deltas, scale_factor)."""
    if turnover_cap is None or turnover_cap <= 0:
        return deltas, 1.0
    gross = sum(abs(v) for v in deltas.values())
    if portfolio_value <= 0 or gross <= 0:
        return deltas, 1.0
    limit = turnover_cap * portfolio_value
    if gross <= limit:
        return deltas, 1.0
    scale = limit / gross
    return {k: v * scale for k, v in deltas.items()}, scale


def _round_shares(shares: float, fractional: bool) -> float:
    if shares is None:
        return 0.0
    if fractional:
        # round to 3 decimals for cleaner UI
        return round(shares, 3)
    # whole shares only
    from math import floor
    s = abs(shares)
    s = floor(s)
    return s if shares >= 0 else -s


def preview_rebalance_decision(
    updated_portfolio: Dict[str, Any],
    drift_threshold: float = 0.03,
    min_trade_usd: float = 50.0,
    turnover_cap: float = 0.15,
    fractional: bool = True,
    prices: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute drift and propose trades. Returns a dict with decision, trades, reason, hash.
    Expects updated_portfolio to contain 'holdings' and 'allocations' (target %).
    """
    holdings = updated_portfolio.get("holdings") or []
    allocations = updated_portfolio.get("allocations") or {}
    if not isinstance(allocations, dict) or not holdings:
        return {
            "decision": "error",
            "error": "updated_portfolio must include holdings and allocations"
        }

    current_w, current_values = _weights_from_holdings(holdings)
    target_w = {str(k).upper(): float(v) for k, v in allocations.items()}

    # Portfolio value (sum of all, including cash)
    V = sum(float(v) for v in current_values.values())

    drift_map, max_abs_drift, max_sym = _drift(current_w, target_w)

    decision = "no_action" if max_abs_drift <= (drift_threshold * 100.0) else "rebalance"

    trades: List[Dict[str, Any]] = []
    turnover = 0.0
    scaled = False
    scale_factor = 1.0
    used_prices: Dict[str, float] = {}

    if decision == "rebalance" and V > 0:
        # Dollar deltas to reach target
        raw_deltas: Dict[str, float] = {}
        all_syms = set(current_values.keys()) | set(target_w.keys())
        for t in all_syms:
            if t in IGNORED_TICKERS:
                continue
            Vi = float(current_values.get(t, 0.0))
            tgt_pct = float(target_w.get(t, 0.0)) / 100.0
            Vi_target = V * tgt_pct
            delta = Vi_target - Vi
            raw_deltas[t] = delta

        # Apply turnover cap
        turnover = sum(abs(x) for x in raw_deltas.values()) / V if V > 0 else 0.0
        deltas, scale_factor = _apply_turnover_cap(raw_deltas, V, turnover_cap)
        scaled = (scale_factor != 1.0)

        # Fetch prices if needed
        used_prices = _fetch_prices_if_needed(list(deltas.keys()), prices)

        # Build trades
        for t, d in deltas.items():
            if abs(d) < min_trade_usd:
                continue
            side = "buy" if d > 0 else "sell"
            px = float(used_prices.get(t, 0) or 0)
            shares = (d / px) if px > 0 else None
            shares = _round_shares(shares, fractional) if shares is not None else None
            trades.append({
                "ticker": t,
                "side": side,
                "notional": round(abs(d), 2),
                "price": px if px > 0 else None,
                "shares": shares,
            })

    summary = (
        f"Max drift {max_abs_drift:.2f}% on {max_sym or 'N/A'}; "
        f"threshold {(drift_threshold*100.0):.2f}% → decision: {decision}."
    )

    dec_hash = decision_hash({
        "current_w": current_w,
        "target_w": target_w,
        "V": round(V, 2),
        "drift_threshold": drift_threshold,
        "min_trade_usd": min_trade_usd,
        "turnover_cap": turnover_cap,
    })

    return {
        "decision": decision,
        "max_drift_pct": round(max_abs_drift, 4),
        "max_drift_symbol": max_sym,
        "drift_threshold_pct": round(drift_threshold*100.0, 4),
        "drift_map": drift_map,
        "portfolio_value": round(V, 2),
        "turnover": round(turnover, 6),
        "scaled": scaled,
        "scale_factor": round(scale_factor, 6),
        "trades": trades,
        "prices": used_prices,
        "decision_hash": dec_hash,
        "summary": summary,
    }
