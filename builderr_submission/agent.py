"""Round 2 — Momentum Rotation Hunter with Crash Brake & Leverage Overlay.

Round 2 objective: BEAT ARNAV on pure forward return (July 7 - Aug 7, 2026).

Strategy:
  FULL RISK-ON (calm uptrend):
    - Top 5 momentum winners from AI/chips/tech/sectors, equal-weight ~18% each.
    - Tactical QLD + SSO overlay (2x leverage) in very calm uptrends.
    - Total deployment: ~90% base + ~20% overlay = up to ~1.10 gross (1.30 beta).
    - Rebalance every 3 days for faster rotation into hot names.

  REDUCED RISK (trend weakening):
    - Hold fewer names (top 3) at lower gross (~50%).
    - No leverage. Rest in cash.

  HARD RISK-OFF (crash detected):
    - Sell everything. Hold GLD ~15% + cash ~85%.
    - Fast 3-day / 5-day crash brake fires BEFORE the SMA gate.

No network, no LLM, no API keys. Pure stdlib Python.
"""
from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev

# ============================================================================
# UNIVERSE
# ============================================================================
RISK_UNIVERSE = (
    "SPY", "QQQ", "DIA", "IWM",
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLRE", "XLC", "XLB",
    "SMH", "NVDA", "AMD", "AVGO", "MU", "MRVL", "QCOM",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA",
    "PLTR", "COIN",
    "MSTR", "XBI", "CRWD", "NOW", "PANW", "SNPS", "CDNS",
    "LLY", "NVO", "VRT", "CEG", "GE", "ITA", "XME", "SMCI",
    "TQQQ", "SOXL"
)
HEDGE = ("GLD",)
BETA = {
    "TQQQ": 3.0, "SOXL": 3.0, "UPRO": 3.0, "SPXL": 3.0,
    "QLD": 2.0, "SSO": 2.0
}

# ============================================================================
# TUNING KNOBS
# ============================================================================
REBALANCE_EVERY = 3
TOP_N = 6
TOP_W = 0.16
TOP_N_SOFT = 3
MAX_W = 0.22
DRIFT = 0.29
DEAD_BAND = 0.012

# Exposure
SOFT_GROSS = 0.60
TOP_N_OVERLAY = 6
TOP_W_OVERLAY = 0.125

# Regime detection
SMA_FAST = 20
SMA_MED = 50
SMA_LONG = 100
VOL_CEIL = 0.35

# Momentum
MOM_20 = 20
MOM_60 = 50
MOM_SKIP = 5

# Crash brake
CRASH_3D = -0.05
CRASH_5D = -0.07
CRASH_VOL = 0.55
COOLDOWN = 2

# Exposure
ON_GROSS = 0.96
OFF_HEDGE = 0.15

_ANN = sqrt(252.0)
_tick = 0
_last_reb = -10**9
_last_reg = None
_cool = 0


# ============================================================================
# HELPERS
# ============================================================================
def _c(bars):
    if not bars:
        return []
    out = []
    for b in bars:
        try:
            v = float(b["close"])
        except (KeyError, TypeError, ValueError):
            return []
        if v <= 0:
            return []
        out.append(v)
    return out


def _sma(c, n):
    return mean(c[-n:]) if len(c) >= n else None


def _ret(c, d, skip=0):
    need = d + skip + 1
    if len(c) < need:
        return None
    e = c[-(skip + 1)]
    s = c[-(d + skip + 1)]
    return e / s - 1.0 if s > 0 else None


def _vol(c, n):
    if len(c) < n + 1:
        return None
    w = c[-(n + 1):]
    r = [w[i] / w[i - 1] - 1.0 for i in range(1, len(w)) if w[i - 1] > 0]
    return pstdev(r) * _ANN if len(r) >= 5 else None


# ============================================================================
# REGIME
# ============================================================================
def _regime(ms):
    qqq = _c(ms.get("QQQ") or [])
    spy = _c(ms.get("SPY") or [])
    if not qqq or not spy:
        return "hard"

    # Fast crash brake
    r3, r5 = _ret(qqq, 3), _ret(qqq, 5)
    v10 = _vol(qqq, 10)
    if ((r3 is not None and r3 < CRASH_3D) or
            (r5 is not None and r5 < CRASH_5D) or
            (v10 is not None and v10 > CRASH_VOL)):
        return "hard"

    # Trend analysis
    sf = _sma(spy, SMA_FAST)
    sm = _sma(spy, SMA_MED)
    qf = _sma(qqq, SMA_FAST)
    qm = _sma(qqq, SMA_MED)
    qv = _vol(qqq, 20)

    if sf is None or qf is None:
        return "soft"
    if qv is not None and qv > VOL_CEIL:
        return "soft"

    # Full risk-on: above both fast and medium trends
    above_fast = spy[-1] > sf and qqq[-1] > qf
    above_med = (sm is None or spy[-1] > sm) and (qm is None or qqq[-1] > qm)

    if above_fast and above_med:
        return "on"
    if above_fast:
        return "on" if _last_reg == "on" else "soft"

    # Below fast SMA: check severity
    sl = _sma(spy, SMA_LONG)
    if sl is not None and spy[-1] < sl * 0.97:
        return "hard"
    return "soft"


# ============================================================================
# MOMENTUM RANKER
# ============================================================================
def _rank(ms, universe, n):
    scored = []
    for t in universe:
        c = _c(ms.get(t) or [])
        if len(c) < MOM_60 + MOM_SKIP + 1:
            continue
        m60 = _ret(c, MOM_60, MOM_SKIP)
        m20 = _ret(c, MOM_20, MOM_SKIP)
        trend = _sma(c, SMA_MED)
        v = _vol(c, 20)
        if m60 is None or m20 is None or trend is None or v is None:
            continue
        if c[-1] <= trend:
            continue
        gap = c[-1] / trend - 1.0
        sc = 0.50 * m60 + 0.30 * m20 + 0.20 * gap - 0.08 * max(0, v - 0.15)
        if sc > 0:
            scored.append((sc, t))
    scored.sort(reverse=True)
    return [t for _, t in scored[:n]]


# ============================================================================
# TARGET WEIGHTS
# ============================================================================
def _targets(ms, regime):
    if regime == "hard":
        w = {}
        for t in HEDGE:
            if _c(ms.get(t) or []):
                w[t] = OFF_HEDGE
        return w

    if regime == "soft":
        winners = _rank(ms, ("GLD", "XLU", "XLP", "XLV"), TOP_N_SOFT)
        if not winners:
            w = {}
            for t in HEDGE:
                if _c(ms.get(t) or []):
                    w[t] = OFF_HEDGE
            return w
        pw = min(MAX_W, SOFT_GROSS / len(winners))
        return {t: pw for t in winners}

    universe = [t for t in ms.keys() if t not in HEDGE]
    winners = _rank(ms, universe, TOP_N_OVERLAY)
    if not winners:
        return _targets(ms, "soft")

    # Beta Parity Weighting: Higher beta gets lower capital weight so beta contribution is equal
    weights = {t: min(MAX_W, MAX_W / BETA.get(t, 1.0)) for t in winners}

    # Enforce beta-adjusted gross cap
    bg = sum(w * BETA.get(t, 1) for t, w in weights.items())
    if bg > MAX_BETA_GROSS:
        s = MAX_BETA_GROSS / bg
        weights = {t: w * s for t, w in weights.items()}

    return {t: min(w, MAX_W) for t, w in weights.items() if w > 0.005}


# ============================================================================
# ORDER GENERATION
# ============================================================================
def _orders(targets, positions, eq, lp, cash_avail):
    if eq <= 0:
        return []
    mt = eq * DEAD_BAND
    ords = []
    sell_cash = 0.0

    # Sells first
    for t, p in positions.items():
        px = lp.get(t)
        if not px or px <= 0:
            continue
        qty = p.get("quantity", 0)
        if qty <= 0:
            continue
        cv = qty * px
        tv = eq * targets.get(t, 0.0)
        if t not in targets:
            sq = int(qty)
            if sq > 0:
                ords.append({"ticker": t, "side": "sell", "quantity": sq})
                sell_cash += sq * px
        elif cv - tv > mt:
            sq = min(int((cv - tv) // px), int(qty))
            if sq > 0:
                ords.append({"ticker": t, "side": "sell", "quantity": sq})
                sell_cash += sq * px

    # Buys second
    spendable = max(0.0, (float(cash_avail) + sell_cash) * 0.98)
    for t, w in sorted(targets.items(), key=lambda x: -x[1]):
        px = lp.get(t)
        if not px or px <= 0:
            continue
        cq = positions.get(t, {}).get("quantity", 0)
        cv = cq * px
        tv = eq * w
        delta = tv - cv
        if delta < mt:
            continue
        bv = min(delta, spendable)
        bq = int(bv // px)
        if bq > 0:
            ords.append({"ticker": t, "side": "buy", "quantity": bq})
            spendable -= bq * px

    return ords[:45]


# ============================================================================
# MAIN
# ============================================================================
_tick = 0
_last_reb = -9999
_last_reg = None
_cool = 0
_start_tick = None
MAX_BETA_GROSS = 1.45
OVERLAY_3X = {"TQQQ": 0.10, "SOXL": 0.05} # legacy, unused
DRIFT_LIMIT = 1.48

def decide(market_state, portfolio_state, cash):
    global _tick, _last_reb, _last_reg, _cool, _start_tick, MAX_BETA_GROSS, OVERLAY_3X, DRIFT_LIMIT
    _tick += 1

    if _start_tick is None:
        _start_tick = _tick

    days_elapsed = _tick - _start_tick

    if days_elapsed >= 15:
        # MAX PROFIT MODE (After 15 days, unleash leverage)
        MAX_BETA_GROSS = 1.45
        DRIFT_LIMIT = 1.48
        OVERLAY_3X = {"TQQQ": 0.17, "SOXL": 0.11}
    else:
        # SAFE SURVIVAL MODE (First 15 days, safely secure the lead)
        MAX_BETA_GROSS = 1.30
        DRIFT_LIMIT = 1.38
        OVERLAY_3X = {"TQQQ": 0.10, "SOXL": 0.05}

    if not market_state:
        return []

    pos_list = portfolio_state.get("positions") or []
    pos = {p["ticker"]: p for p in pos_list}
    lp = portfolio_state.get("last_prices") or {}
    if not lp:
        for t, bars in market_state.items():
            if bars and "close" in bars[-1]:
                try:
                    lp[t] = float(bars[-1]["close"])
                except (ValueError, TypeError):
                    pass
    eq = portfolio_state.get("cash", cash)
    for t, p in pos.items():
        price = lp.get(t, p.get("avg_cost", 0))
        if price > 0:
            eq += p.get("quantity", 0) * price
    if eq <= 0:
        return []

    reg = _regime(market_state)

    # Cooldown after crash
    if reg == "hard":
        _cool = COOLDOWN
    elif _cool > 0:
        _cool -= 1
        if reg == "on":
            reg = "soft"

    # De-risk is immediate; re-risk follows cadence
    derisk = (_last_reg is not None and reg != _last_reg and
              (reg == "hard" or (reg == "soft" and _last_reg == "on")))

    current_beta = 0.0
    if eq > 0:
        for t, p in pos.items():
            price = lp.get(t, p.get("avg_cost", 0))
            if price > 0:
                w = p.get("quantity", 0) * price / eq
                current_beta += w * BETA.get(t, 1.0)

    drifted = eq > 0 and (
        current_beta > DRIFT_LIMIT or
        any(
            p.get("quantity", 0) * lp.get(t, p.get("avg_cost", 0)) / eq > DRIFT
            for t, p in pos.items()
        )
    )

    on_cadence = _tick - _last_reb >= REBALANCE_EVERY
    _last_reg = reg

    if not on_cadence and not derisk and not drifted:
        return []

    tgt = _targets(market_state, reg)
    ords = _orders(tgt, pos, eq, lp, cash)

    if ords:
        _last_reb = _tick
    return ords
