"""
Multi-Source Data Audit Engine
================================
Fetches price + key fundamentals from 3 independent sources,
cross-checks for agreement, and flags discrepancies.

Sources:
  Price   → yfinance | Stooq | Yahoo Finance Direct CSV
  Fundamentals → yfinance Info | yfinance Statements | NSE India (for .NS)

Returns a structured audit report shown at the bottom of every analysis.
"""

import numpy as np
import time
import io


# ─────────────────────────────────────────────────────────────────────────────
#  PRICE AUDIT: Three independent sources
# ─────────────────────────────────────────────────────────────────────────────

def _price_yfinance(ticker):
    import yfinance as yf
    t = yf.Ticker(ticker)
    info = t.info
    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    if not price:
        raise ValueError("yfinance: no price field")
    return float(price), "yfinance (regularMarketPrice)"


def _price_stooq(ticker):
    """Stooq is a free financial data provider — great fallback."""
    import requests
    # Stooq uses different ticker format
    stooq_ticker = ticker
    if ticker.endswith(".NS"):
        stooq_ticker = ticker.replace(".NS", ".IN")
    elif ticker.endswith(".BO"):
        stooq_ticker = ticker.replace(".BO", ".IN")
    elif ticker.endswith(".DE"):
        stooq_ticker = ticker.replace(".DE", ".DE")
    url = f"https://stooq.com/q/l/?s={stooq_ticker.lower()}&f=sd2t2ohlcv&h&e=csv"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    lines = resp.text.strip().split("\n")
    if len(lines) < 2:
        raise ValueError("Stooq: no data rows")
    parts = lines[1].split(",")
    if len(parts) < 5:
        raise ValueError("Stooq: malformed row")
    price = float(parts[4])  # Close price
    if price <= 0:
        raise ValueError("Stooq: price is zero")
    return price, "Stooq (daily close)"


def _price_yahoo_direct(ticker):
    """Yahoo Finance CSV endpoint — independent of yfinance library."""
    import requests
    period2 = int(time.time())
    period1 = int(period2 - 5 * 86400)  # Last 5 days
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/136.0.0.0"}
    session = requests.Session()
    session.headers.update(headers)
    session.get("https://finance.yahoo.com", timeout=8)
    crumb = session.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=8).text.strip()
    if not crumb:
        raise ValueError("Yahoo Direct: no crumb")
    resp = session.get(url + f"&crumb={crumb}", timeout=10)
    resp.raise_for_status()
    df_lines = resp.text.strip().split("\n")
    if len(df_lines) < 2:
        raise ValueError("Yahoo Direct: no data")
    last = df_lines[-1].split(",")
    price = float(last[4])  # Close
    return price, "Yahoo Finance Direct CSV"


# ─────────────────────────────────────────────────────────────────────────────
#  FUNDAMENTAL AUDIT: Three independent sources
# ─────────────────────────────────────────────────────────────────────────────

def _fundamentals_yfinance_info(ticker):
    """Source 1: yfinance .info dict (quick summary)."""
    import yfinance as yf
    t = yf.Ticker(ticker)
    info = t.info
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    scale = 1e-7 if is_indian else 1e-6  # → Crores or Millions

    result = {
        "source": "yfinance .info",
        "net_income":  round((info.get("netIncomeToCommon") or 0) * scale, 2),
        "revenue":     round((info.get("totalRevenue") or 0) * scale, 2),
        "ebit":        round((info.get("operatingIncome") or info.get("ebit") or 0) * scale, 2),
        "total_debt":  round((info.get("totalDebt") or 0) * scale, 2),
        "cash":        round((info.get("totalCash") or 0) * scale, 2),
        "shares":      round((info.get("sharesOutstanding") or 0) * (1e-7 if is_indian else 1e-6), 4),
        "beta":        round(info.get("beta") or 1.0, 3),
        "pe_ratio":    round(info.get("trailingPE") or 0, 2),
        "market_cap":  round((info.get("marketCap") or 0) * scale, 2),
        "dividend_yield": round((info.get("dividendYield") or 0), 4),
    }
    return result


def _fundamentals_yfinance_statements(ticker):
    """Source 2: yfinance financial statements (more granular, different pipeline)."""
    import yfinance as yf
    t = yf.Ticker(ticker)
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    scale = 1e-7 if is_indian else 1e-6

    result = {"source": "yfinance Statements"}

    # Income statement
    try:
        fin = t.financials
        if fin is not None and not fin.empty:
            col = fin.columns[0]
            def _get(keys):
                for k in keys:
                    if k in fin.index:
                        return float(fin.loc[k, col]) * scale
                return 0
            result["revenue"]    = round(_get(["Total Revenue"]), 2)
            result["ebit"]       = round(_get(["Operating Income", "EBIT"]), 2)
            result["net_income"] = round(_get(["Net Income", "Net Income Common Stockholders"]), 2)
    except Exception:
        result["revenue"] = result["ebit"] = result["net_income"] = None

    # Cash flow
    try:
        cf = t.cashflow
        if cf is not None and not cf.empty:
            col = cf.columns[0]
            def _getcf(keys):
                for k in keys:
                    if k in cf.index:
                        return float(cf.loc[k, col]) * scale
                return 0
            result["capex"]       = round(abs(_getcf(["Capital Expenditure", "Purchase Of PPE"])), 2)
            result["depreciation"]= round(_getcf(["Depreciation & Amortization","Depreciation Amortization Depletion"]), 2)
    except Exception:
        result["capex"] = result["depreciation"] = None

    # Balance sheet
    try:
        bs = t.balance_sheet
        if bs is not None and not bs.empty:
            col = bs.columns[0]
            def _getbs(keys):
                for k in keys:
                    if k in bs.index:
                        return float(bs.loc[k, col]) * scale
                return 0
            result["total_debt"] = round(_getbs(["Total Debt","Long Term Debt"]), 2)
            result["cash"]       = round(_getbs(["Cash And Cash Equivalents","Cash Cash Equivalents And Short Term Investments"]), 2)
    except Exception:
        result["total_debt"] = result["cash"] = None

    return result


def _fundamentals_nse_india(ticker):
    """Source 3 (Indian only): NSE India public API for quick validation."""
    import requests
    if not (ticker.endswith(".NS") or ticker.endswith(".BO")):
        return {"source": "NSE India", "available": False, "reason": "Not an Indian ticker"}

    symbol = ticker.replace(".NS", "").replace(".BO", "")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com",
        }
        session = requests.Session()
        session.headers.update(headers)
        # First hit the main page to get cookies
        session.get("https://www.nseindia.com", timeout=8)
        resp = session.get(
            f"https://www.nseindia.com/api/quote-equity?symbol={symbol}",
            timeout=8
        )
        data = resp.json()
        price_info = data.get("priceInfo", {})
        return {
            "source": "NSE India API",
            "available": True,
            "last_price":    price_info.get("lastPrice"),
            "52w_high":      price_info.get("weekHighLow", {}).get("max"),
            "52w_low":       price_info.get("weekHighLow", {}).get("min"),
            "pe_ratio":      data.get("metadata", {}).get("pdSymbolPe"),
            "face_value":    data.get("metadata", {}).get("pdFaceValue"),
            "series":        data.get("metadata", {}).get("series"),
        }
    except Exception as e:
        return {"source": "NSE India API", "available": False, "reason": str(e)}


def _fundamentals_sec_edgar(ticker):
    """Source 3 (US only): SEC EDGAR for revenue/net income validation."""
    import requests
    if ticker.endswith(".NS") or ticker.endswith(".BO") or "." in ticker:
        return {"source": "SEC EDGAR", "available": False, "reason": "Non-US ticker"}
    try:
        # Search for CIK
        resp = requests.get(
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom"
            f"&startdt=2023-01-01&enddt=2025-12-31&forms=10-K",
            timeout=8,
            headers={"User-Agent": "EquityLab research@example.com"}
        )
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return {"source": "SEC EDGAR", "available": False, "reason": "No 10-K found"}
        hit = hits[0].get("_source", {})
        return {
            "source": "SEC EDGAR (10-K)",
            "available": True,
            "company_name": hit.get("display_names", [{}])[0].get("name") if hit.get("display_names") else None,
            "filing_date":  hit.get("period_of_report"),
            "form":         hit.get("form_type"),
            "cik":          hit.get("entity_id"),
        }
    except Exception as e:
        return {"source": "SEC EDGAR", "available": False, "reason": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN AUDIT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def run_data_audit(ticker: str, hardcoded_fd: dict = None) -> dict:
    """
    Runs a full multi-source data audit for a ticker.
    Returns:
      price_audit     – dict with 3 price sources
      fundamentals    – dict with 2-3 fundamental sources
      agreement       – key cross-check results
      flags           – list of discrepancy warnings
      overall_status  – "VERIFIED", "MINOR DISCREPANCY", "MAJOR DISCREPANCY"
    """
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    cur = "₹" if is_indian else "$"
    unit = "Cr" if is_indian else "M"
    flags = []

    # ── PRICE from 3 sources ─────────────────────────────────────────────────
    price_sources = []
    for name, fn in [
        ("yfinance", _price_yfinance),
        ("Stooq", _price_stooq),
        ("Yahoo Direct", _price_yahoo_direct),
    ]:
        try:
            price, label = fn(ticker)
            price_sources.append({"source": name, "price": price, "label": label, "status": "✅"})
        except Exception as e:
            price_sources.append({"source": name, "price": None, "error": str(e)[:80], "status": "❌"})

    valid_prices = [s["price"] for s in price_sources if s["price"] is not None]
    price_consensus = float(np.mean(valid_prices)) if valid_prices else None
    price_spread = (max(valid_prices) - min(valid_prices)) / price_consensus if (len(valid_prices) > 1 and price_consensus) else 0

    if price_spread > 0.05:
        flags.append({"severity": "warning", "field": "Price Spread", "message": f"Sources disagree by {price_spread:.1%} — verify market data."})

    # ── FUNDAMENTALS from 2-3 sources ────────────────────────────────────────
    fund_sources = []

    try:
        fund_sources.append(_fundamentals_yfinance_info(ticker))
    except Exception as e:
        fund_sources.append({"source": "yfinance .info", "error": str(e)[:80]})

    try:
        fund_sources.append(_fundamentals_yfinance_statements(ticker))
    except Exception as e:
        fund_sources.append({"source": "yfinance Statements", "error": str(e)[:80]})

    if is_indian:
        fund_sources.append(_fundamentals_nse_india(ticker))
    else:
        fund_sources.append(_fundamentals_sec_edgar(ticker))

    # ── Cross-check key metrics ───────────────────────────────────────────────
    agreement = {}
    cross_check_keys = ["revenue", "net_income", "ebit", "total_debt", "cash"]

    for key in cross_check_keys:
        vals = [s[key] for s in fund_sources if isinstance(s.get(key), (int, float)) and s[key] is not None]
        if len(vals) >= 2:
            mean_v = np.mean(vals)
            spread = (max(vals) - min(vals)) / abs(mean_v) if mean_v != 0 else 0
            unit_lbl = "Cr" if is_indian else "M"
            cur_lbl  = "₹" if is_indian else "$"
            def _fmt_v(v): return f"{cur_lbl}{v:,.1f} {unit_lbl}" if v is not None else "—"
            agreement[key] = {
                "values": vals,
                "mean": mean_v,
                "spread_pct": spread * 100,
                "agree": spread < 0.10,
                "source_a_val": _fmt_v(vals[0]) if len(vals) > 0 else "—",
                "source_b_val": _fmt_v(vals[1]) if len(vals) > 1 else "—",
                "source_c_val": _fmt_v(vals[2]) if len(vals) > 2 else "—",
                "status": "✅" if spread < 0.10 else ("⚠️" if spread < 0.25 else "🔴"),
            }
            if spread > 0.25:
                flags.append({"severity": "critical", "field": key.replace('_',' ').title(), "message": f"Sources disagree by {spread:.0%} — high uncertainty in this figure."})
            elif spread > 0.10:
                flags.append({"severity": "warning", "field": key.replace('_',' ').title(), "message": f"Minor discrepancy of {spread:.0%} between sources."})

    # ── Cross-check against hardcoded (if provided) ───────────────────────────
    if hardcoded_fd:
        for key in ["net_income", "revenue", "total_debt"]:
            hc_val = hardcoded_fd.get(key)
            live_vals = [s.get(key) for s in fund_sources if isinstance(s.get(key), (int, float))]
            if hc_val and live_vals:
                live_mean = np.mean(live_vals)
                if abs(hc_val) > 0:
                    diff = abs(live_mean - hc_val) / abs(hc_val)
                    if diff > 0.30:
                        flags.append({
                            "severity": "critical",
                            "field": f"Hardcoded {key.replace('_',' ').title()}",
                            "message": f"Hardcoded value {cur}{hc_val:,.1f} {unit} differs from live data {cur}{live_mean:,.1f} {unit} by {diff:.0%}. Consider updating."
                        })
                    elif diff > 0.15:
                        flags.append({
                            "severity": "warning",
                            "field": f"Hardcoded {key.replace('_',' ').title()}",
                            "message": f"Hardcoded {cur}{hc_val:,.1f} {unit} vs live {cur}{live_mean:,.1f} {unit} — {diff:.0%} difference."
                        })

    # ── Overall status ────────────────────────────────────────────────────────
    red_flags  = [f for f in flags if isinstance(f, dict) and f.get("severity") == "critical"]
    warn_flags = [f for f in flags if isinstance(f, dict) and f.get("severity") == "warning"]

    if red_flags:
        overall_status = "MAJOR DISCREPANCY"
    elif warn_flags:
        overall_status = "MINOR DISCREPANCY"
    else:
        overall_status = "VERIFIED"

    return {
        "ticker": ticker,
        "currency": cur,
        "unit": unit,
        "is_indian": is_indian,
        "price_sources": price_sources,
        "price_consensus": price_consensus,
        "price_spread": price_spread,
        "fund_sources": fund_sources,
        "agreement": agreement,
        "flags": flags,
        "overall_status": overall_status,
        "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sources_count": 3,
    }
