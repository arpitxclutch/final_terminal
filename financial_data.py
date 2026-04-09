"""
Financial Data Fetcher
======================
Priority:
  1. Hardcoded data (reliable, from annual reports — for known tickers)
  2. Live yfinance fetch (auto-builds required dict for ANY listed company)

Monetary units:
  Indian stocks (.NS / .BO) → ₹ Crores
  US / Global stocks        → $ Millions

Covers ALL listed companies — not just the hardcoded set.
"""

import numpy as np


# ═════════════════════════════════════════════════════════════════════════════
#  HARDCODED FUNDAMENTAL DATA  (From latest annual reports)
#  Values in Crores (India) or Millions (US)
# ═════════════════════════════════════════════════════════════════════════════

FUNDAMENTAL_DATA = {
    "TATAMOTORS.NS": {
        "company": "Tata Motors", "currency": "INR", "unit": "Cr",
        "net_income": 31807, "ebit": 42500, "revenue": 437927,
        "depreciation": 28000, "capex": 38000, "delta_wc": 5000,
        "total_debt": 108000, "cash": 42000, "shares_outstanding": 366.16,
        "dividends_total": 2198, "tax_rate": 0.25,
        "debt_ratio": 0.35, "debt_ratio_changing": True,
        "cost_of_equity": 0.13, "wacc": 0.105,
        "firm_growth_rate": 0.10, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.35,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "M&M.NS": {
        "company": "Mahindra & Mahindra", "currency": "INR", "unit": "Cr",
        "net_income": 12250, "ebit": 16800, "revenue": 148800,
        "depreciation": 5200, "capex": 8500, "delta_wc": 2100,
        "total_debt": 38000, "cash": 18000, "shares_outstanding": 124.52,
        "dividends_total": 2490, "tax_rate": 0.25,
        "debt_ratio": 0.28, "debt_ratio_changing": True,
        "cost_of_equity": 0.125, "wacc": 0.10,
        "firm_growth_rate": 0.12, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.1,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "OLECTRA.NS": {
        "company": "Olectra Greentech", "currency": "INR", "unit": "Cr",
        "net_income": 120, "ebit": 170, "revenue": 2100,
        "depreciation": 80, "capex": 200, "delta_wc": 150,
        "total_debt": 600, "cash": 100, "shares_outstanding": 8.18,
        "dividends_total": 0, "tax_rate": 0.25,
        "debt_ratio": 0.30, "debt_ratio_changing": True,
        "cost_of_equity": 0.145, "wacc": 0.115,
        "firm_growth_rate": 0.25, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.5,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "ATHERENERG.NS": {
        "company": "Ather Energy", "currency": "INR", "unit": "Cr",
        "net_income": -900, "ebit": -800, "revenue": 1800,
        "depreciation": 200, "capex": 500, "delta_wc": 100,
        "total_debt": 300, "cash": 600, "shares_outstanding": 27.0,
        "dividends_total": 0, "tax_rate": 0.25,
        "debt_ratio": 0.15, "debt_ratio_changing": True,
        "cost_of_equity": 0.16, "wacc": 0.14,
        "firm_growth_rate": 0.35, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.8,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
        "startup_negative": True,
    },
    "APOLLOTYRE.NS": {
        "company": "Apollo Tyres", "currency": "INR", "unit": "Cr",
        "net_income": 2000, "ebit": 3200, "revenue": 26500,
        "depreciation": 1800, "capex": 2500, "delta_wc": 500,
        "total_debt": 5500, "cash": 1500, "shares_outstanding": 63.46,
        "dividends_total": 318, "tax_rate": 0.25,
        "debt_ratio": 0.22, "debt_ratio_changing": False,
        "cost_of_equity": 0.12, "wacc": 0.10,
        "firm_growth_rate": 0.08, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.0,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "MRF.NS": {
        "company": "MRF Ltd.", "currency": "INR", "unit": "Cr",
        "net_income": 2050, "ebit": 3500, "revenue": 24500,
        "depreciation": 1400, "capex": 2800, "delta_wc": 600,
        "total_debt": 3000, "cash": 2000, "shares_outstanding": 0.4243,
        "dividends_total": 68, "tax_rate": 0.25,
        "debt_ratio": 0.12, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.10,
        "firm_growth_rate": 0.07, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.85,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "JKTYRE.NS": {
        "company": "JK Tyre & Industries", "currency": "INR", "unit": "Cr",
        "net_income": 700, "ebit": 1300, "revenue": 14500,
        "depreciation": 600, "capex": 900, "delta_wc": 300,
        "total_debt": 4000, "cash": 500, "shares_outstanding": 24.71,
        "dividends_total": 99, "tax_rate": 0.25,
        "debt_ratio": 0.35, "debt_ratio_changing": True,
        "cost_of_equity": 0.135, "wacc": 0.105,
        "firm_growth_rate": 0.06, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.2,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "CEATLTD.NS": {
        "company": "CEAT Ltd.", "currency": "INR", "unit": "Cr",
        "net_income": 600, "ebit": 1100, "revenue": 12500,
        "depreciation": 550, "capex": 800, "delta_wc": 200,
        "total_debt": 2500, "cash": 300, "shares_outstanding": 4.04,
        "dividends_total": 56, "tax_rate": 0.25,
        "debt_ratio": 0.25, "debt_ratio_changing": False,
        "cost_of_equity": 0.125, "wacc": 0.10,
        "firm_growth_rate": 0.08, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.05,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "SBIN.NS": {
        "company": "State Bank of India", "currency": "INR", "unit": "Cr",
        "net_income": 61077, "ebit": 95000, "revenue": 340000,
        "depreciation": 5000, "capex": 6000, "delta_wc": 10000,
        "total_debt": 4200000, "cash": 200000, "shares_outstanding": 892.46,
        "dividends_total": 11600, "tax_rate": 0.25,
        "debt_ratio": 0.92, "debt_ratio_changing": False,
        "cost_of_equity": 0.13, "wacc": 0.08,
        "firm_growth_rate": 0.10, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.15,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "HDFCBANK.NS": {
        "company": "HDFC Bank", "currency": "INR", "unit": "Cr",
        "net_income": 60810, "ebit": 90000, "revenue": 395000,
        "depreciation": 4000, "capex": 5000, "delta_wc": 8000,
        "total_debt": 2400000, "cash": 150000, "shares_outstanding": 762.08,
        "dividends_total": 14600, "tax_rate": 0.25,
        "debt_ratio": 0.90, "debt_ratio_changing": False,
        "cost_of_equity": 0.12, "wacc": 0.075,
        "firm_growth_rate": 0.12, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.0,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "ICICIBANK.NS": {
        "company": "ICICI Bank", "currency": "INR", "unit": "Cr",
        "net_income": 44255, "ebit": 70000, "revenue": 250000,
        "depreciation": 3500, "capex": 4500, "delta_wc": 6000,
        "total_debt": 1200000, "cash": 100000, "shares_outstanding": 702.30,
        "dividends_total": 8500, "tax_rate": 0.25,
        "debt_ratio": 0.88, "debt_ratio_changing": False,
        "cost_of_equity": 0.12, "wacc": 0.075,
        "firm_growth_rate": 0.13, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.05,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "AXISBANK.NS": {
        "company": "Axis Bank", "currency": "INR", "unit": "Cr",
        "net_income": 26248, "ebit": 42000, "revenue": 188000,
        "depreciation": 3000, "capex": 3500, "delta_wc": 5000,
        "total_debt": 950000, "cash": 80000, "shares_outstanding": 309.44,
        "dividends_total": 3700, "tax_rate": 0.25,
        "debt_ratio": 0.87, "debt_ratio_changing": False,
        "cost_of_equity": 0.13, "wacc": 0.08,
        "firm_growth_rate": 0.12, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.2,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "LAURUSLABS.NS": {
        "company": "Laurus Labs", "currency": "INR", "unit": "Cr",
        "net_income": 250, "ebit": 450, "revenue": 5100,
        "depreciation": 350, "capex": 500, "delta_wc": 200,
        "total_debt": 2000, "cash": 400, "shares_outstanding": 53.90,
        "dividends_total": 54, "tax_rate": 0.25,
        "debt_ratio": 0.30, "debt_ratio_changing": True,
        "cost_of_equity": 0.135, "wacc": 0.11,
        "firm_growth_rate": 0.15, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.3,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "AUROPHARMA.NS": {
        "company": "Aurobindo Pharma", "currency": "INR", "unit": "Cr",
        "net_income": 2900, "ebit": 4200, "revenue": 30000,
        "depreciation": 1200, "capex": 1800, "delta_wc": 700,
        "total_debt": 5000, "cash": 2000, "shares_outstanding": 58.62,
        "dividends_total": 293, "tax_rate": 0.25,
        "debt_ratio": 0.20, "debt_ratio_changing": False,
        "cost_of_equity": 0.125, "wacc": 0.10,
        "firm_growth_rate": 0.10, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.9,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "SUNPHARMA.NS": {
        "company": "Sun Pharma", "currency": "INR", "unit": "Cr",
        "net_income": 9200, "ebit": 12000, "revenue": 48000,
        "depreciation": 1800, "capex": 2500, "delta_wc": 1000,
        "total_debt": 4000, "cash": 12000, "shares_outstanding": 239.84,
        "dividends_total": 1440, "tax_rate": 0.20,
        "debt_ratio": 0.08, "debt_ratio_changing": False,
        "cost_of_equity": 0.12, "wacc": 0.10,
        "firm_growth_rate": 0.12, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.75,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "DIVISLAB.NS": {
        "company": "Divi's Laboratories", "currency": "INR", "unit": "Cr",
        "net_income": 1750, "ebit": 2400, "revenue": 8400,
        "depreciation": 550, "capex": 700, "delta_wc": 300,
        "total_debt": 300, "cash": 1500, "shares_outstanding": 26.56,
        "dividends_total": 478, "tax_rate": 0.20,
        "debt_ratio": 0.03, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.10,
        "firm_growth_rate": 0.14, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.7,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "ITC.NS": {
        "company": "ITC Ltd.", "currency": "INR", "unit": "Cr",
        "net_income": 20200, "ebit": 26000, "revenue": 75000,
        "depreciation": 1800, "capex": 3000, "delta_wc": 500,
        "total_debt": 600, "cash": 15000, "shares_outstanding": 1252.7,
        "dividends_total": 16280, "tax_rate": 0.25,
        "debt_ratio": 0.01, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.10,
        "firm_growth_rate": 0.07, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.7,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "CHALET.NS": {
        "company": "Chalet Hotels", "currency": "INR", "unit": "Cr",
        "net_income": 350, "ebit": 700, "revenue": 1800,
        "depreciation": 250, "capex": 400, "delta_wc": 100,
        "total_debt": 2500, "cash": 200, "shares_outstanding": 20.29,
        "dividends_total": 0, "tax_rate": 0.25,
        "debt_ratio": 0.45, "debt_ratio_changing": True,
        "cost_of_equity": 0.14, "wacc": 0.105,
        "firm_growth_rate": 0.15, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.4,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "MHRIL.NS": {
        "company": "Mahindra Holidays", "currency": "INR", "unit": "Cr",
        "net_income": 200, "ebit": 350, "revenue": 1200,
        "depreciation": 120, "capex": 200, "delta_wc": 80,
        "total_debt": 600, "cash": 150, "shares_outstanding": 8.46,
        "dividends_total": 42, "tax_rate": 0.25,
        "debt_ratio": 0.30, "debt_ratio_changing": False,
        "cost_of_equity": 0.135, "wacc": 0.105,
        "firm_growth_rate": 0.10, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.1,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "INDHOTEL.NS": {
        "company": "Indian Hotels Co.", "currency": "INR", "unit": "Cr",
        "net_income": 1150, "ebit": 1700, "revenue": 6900,
        "depreciation": 500, "capex": 800, "delta_wc": 200,
        "total_debt": 2200, "cash": 1500, "shares_outstanding": 141.94,
        "dividends_total": 710, "tax_rate": 0.25,
        "debt_ratio": 0.18, "debt_ratio_changing": False,
        "cost_of_equity": 0.13, "wacc": 0.105,
        "firm_growth_rate": 0.14, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.15,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "HUL.NS": {
        "company": "Hindustan Unilever", "currency": "INR", "unit": "Cr",
        "net_income": 10000, "ebit": 13500, "revenue": 62000,
        "depreciation": 800, "capex": 1200, "delta_wc": 300,
        "total_debt": 0, "cash": 3000, "shares_outstanding": 234.81,
        "dividends_total": 8400, "tax_rate": 0.25,
        "debt_ratio": 0.00, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.105,
        "firm_growth_rate": 0.07, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.65,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "NESTLEIND.NS": {
        "company": "Nestlé India", "currency": "INR", "unit": "Cr",
        "net_income": 3180, "ebit": 4200, "revenue": 18200,
        "depreciation": 500, "capex": 700, "delta_wc": 150,
        "total_debt": 200, "cash": 1200, "shares_outstanding": 9.64,
        "dividends_total": 2891, "tax_rate": 0.25,
        "debt_ratio": 0.01, "debt_ratio_changing": False,
        "cost_of_equity": 0.11, "wacc": 0.10,
        "firm_growth_rate": 0.09, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.6,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "SHREECEM.NS": {
        "company": "Shree Cement", "currency": "INR", "unit": "Cr",
        "net_income": 2150, "ebit": 3800, "revenue": 19600,
        "depreciation": 1800, "capex": 2200, "delta_wc": 400,
        "total_debt": 3000, "cash": 1000, "shares_outstanding": 3.60,
        "dividends_total": 180, "tax_rate": 0.25,
        "debt_ratio": 0.10, "debt_ratio_changing": False,
        "cost_of_equity": 0.12, "wacc": 0.10,
        "firm_growth_rate": 0.08, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.95,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "ULTRACEMCO.NS": {
        "company": "UltraTech Cement", "currency": "INR", "unit": "Cr",
        "net_income": 7100, "ebit": 11000, "revenue": 68000,
        "depreciation": 4000, "capex": 5000, "delta_wc": 1000,
        "total_debt": 12000, "cash": 3000, "shares_outstanding": 28.90,
        "dividends_total": 578, "tax_rate": 0.25,
        "debt_ratio": 0.12, "debt_ratio_changing": True,
        "cost_of_equity": 0.12, "wacc": 0.10,
        "firm_growth_rate": 0.10, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.95,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "DALBHARAT.NS": {
        "company": "Dalmia Bharat", "currency": "INR", "unit": "Cr",
        "net_income": 1100, "ebit": 2200, "revenue": 14500,
        "depreciation": 1200, "capex": 1800, "delta_wc": 400,
        "total_debt": 5500, "cash": 1000, "shares_outstanding": 18.77,
        "dividends_total": 188, "tax_rate": 0.25,
        "debt_ratio": 0.22, "debt_ratio_changing": True,
        "cost_of_equity": 0.13, "wacc": 0.105,
        "firm_growth_rate": 0.10, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.1,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "RAMCOCEM.NS": {
        "company": "Ramco Cements", "currency": "INR", "unit": "Cr",
        "net_income": 550, "ebit": 1000, "revenue": 7200,
        "depreciation": 650, "capex": 900, "delta_wc": 200,
        "total_debt": 3500, "cash": 300, "shares_outstanding": 23.69,
        "dividends_total": 118, "tax_rate": 0.25,
        "debt_ratio": 0.28, "debt_ratio_changing": True,
        "cost_of_equity": 0.135, "wacc": 0.105,
        "firm_growth_rate": 0.08, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.1,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "ABSLAMC.NS": {
        "company": "Aditya Birla Sun Life AMC", "currency": "INR", "unit": "Cr",
        "net_income": 850, "ebit": 1100, "revenue": 1900,
        "depreciation": 60, "capex": 80, "delta_wc": 30,
        "total_debt": 0, "cash": 900, "shares_outstanding": 28.93,
        "dividends_total": 867, "tax_rate": 0.25,
        "debt_ratio": 0.00, "debt_ratio_changing": False,
        "cost_of_equity": 0.14, "wacc": 0.13,
        "firm_growth_rate": 0.15, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.2,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "HDFCAMC.NS": {
        "company": "HDFC AMC", "currency": "INR", "unit": "Cr",
        "net_income": 1900, "ebit": 2400, "revenue": 3400,
        "depreciation": 80, "capex": 100, "delta_wc": 50,
        "total_debt": 0, "cash": 3000, "shares_outstanding": 21.31,
        "dividends_total": 852, "tax_rate": 0.25,
        "debt_ratio": 0.00, "debt_ratio_changing": False,
        "cost_of_equity": 0.14, "wacc": 0.13,
        "firm_growth_rate": 0.18, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 0.95,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "NAM-INDIA.NS": {
        "company": "Nippon Life India AMC", "currency": "INR", "unit": "Cr",
        "net_income": 1050, "ebit": 1350, "revenue": 2100,
        "depreciation": 50, "capex": 70, "delta_wc": 30,
        "total_debt": 0, "cash": 1500, "shares_outstanding": 61.40,
        "dividends_total": 1474, "tax_rate": 0.25,
        "debt_ratio": 0.00, "debt_ratio_changing": False,
        "cost_of_equity": 0.135, "wacc": 0.125,
        "firm_growth_rate": 0.15, "stable_growth": 0.05,
        "has_competitive_adv": True, "beta": 1.0,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "UTIAMC.NS": {
        "company": "UTI AMC", "currency": "INR", "unit": "Cr",
        "net_income": 550, "ebit": 720, "revenue": 1200,
        "depreciation": 40, "capex": 55, "delta_wc": 20,
        "total_debt": 0, "cash": 800, "shares_outstanding": 12.72,
        "dividends_total": 318, "tax_rate": 0.25,
        "debt_ratio": 0.00, "debt_ratio_changing": False,
        "cost_of_equity": 0.14, "wacc": 0.13,
        "firm_growth_rate": 0.12, "stable_growth": 0.05,
        "has_competitive_adv": False, "beta": 1.05,
        "risk_free_rate": 0.072, "erp": 0.065,
        "inflation_rate": 0.05, "real_growth_rate": 0.06,
    },
    "NVDA": {
        "company": "NVIDIA Corp.", "currency": "USD", "unit": "M",
        "net_income": 29760, "ebit": 33000, "revenue": 60922,
        "depreciation": 1500, "capex": 1800, "delta_wc": 3000,
        "total_debt": 8500, "cash": 26000, "shares_outstanding": 24440,
        "dividends_total": 400, "tax_rate": 0.12,
        "debt_ratio": 0.06, "debt_ratio_changing": False,
        "cost_of_equity": 0.14, "wacc": 0.12,
        "firm_growth_rate": 0.35, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.75,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "MSFT": {
        "company": "Microsoft Corp.", "currency": "USD", "unit": "M",
        "net_income": 72361, "ebit": 88500, "revenue": 245100,
        "depreciation": 13500, "capex": 19600, "delta_wc": 3000,
        "total_debt": 47300, "cash": 80000, "shares_outstanding": 7441,
        "dividends_total": 22300, "tax_rate": 0.15,
        "debt_ratio": 0.14, "debt_ratio_changing": False,
        "cost_of_equity": 0.105, "wacc": 0.09,
        "firm_growth_rate": 0.16, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.92,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "GOOGL": {
        "company": "Alphabet Inc.", "currency": "USD", "unit": "M",
        "net_income": 73795, "ebit": 84300, "revenue": 307400,
        "depreciation": 14400, "capex": 24500, "delta_wc": 5000,
        "total_debt": 13200, "cash": 110900, "shares_outstanding": 12320,
        "dividends_total": 4930, "tax_rate": 0.14,
        "debt_ratio": 0.05, "debt_ratio_changing": False,
        "cost_of_equity": 0.105, "wacc": 0.09,
        "firm_growth_rate": 0.14, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.05,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "META": {
        "company": "Meta Platforms", "currency": "USD", "unit": "M",
        "net_income": 39098, "ebit": 46800, "revenue": 134900,
        "depreciation": 8000, "capex": 28100, "delta_wc": 2000,
        "total_debt": 18400, "cash": 43000, "shares_outstanding": 2540,
        "dividends_total": 1270, "tax_rate": 0.13,
        "debt_ratio": 0.08, "debt_ratio_changing": False,
        "cost_of_equity": 0.11, "wacc": 0.10,
        "firm_growth_rate": 0.17, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.25,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "IBM": {
        "company": "IBM Corp.", "currency": "USD", "unit": "M",
        "net_income": 7500, "ebit": 10200, "revenue": 62000,
        "depreciation": 3800, "capex": 2500, "delta_wc": 1000,
        "total_debt": 48000, "cash": 14000, "shares_outstanding": 904,
        "dividends_total": 6080, "tax_rate": 0.16,
        "debt_ratio": 0.42, "debt_ratio_changing": True,
        "cost_of_equity": 0.105, "wacc": 0.085,
        "firm_growth_rate": 0.04, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.88,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "ASML": {
        "company": "ASML Holding", "currency": "USD", "unit": "M",
        "net_income": 7700, "ebit": 9500, "revenue": 27600,
        "depreciation": 1300, "capex": 1800, "delta_wc": 2000,
        "total_debt": 4500, "cash": 8000, "shares_outstanding": 392,
        "dividends_total": 1570, "tax_rate": 0.17,
        "debt_ratio": 0.10, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.10,
        "firm_growth_rate": 0.15, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.2,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "INTC": {
        "company": "Intel Corp.", "currency": "USD", "unit": "M",
        "net_income": -16600, "ebit": -13000, "revenue": 53100,
        "depreciation": 8000, "capex": 25000, "delta_wc": 2000,
        "total_debt": 48700, "cash": 25000, "shares_outstanding": 4260,
        "dividends_total": 2130, "tax_rate": 0.15,
        "debt_ratio": 0.35, "debt_ratio_changing": True,
        "cost_of_equity": 0.13, "wacc": 0.105,
        "firm_growth_rate": 0.05, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.25,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
        "cyclical_negative": True,
    },
    "QCOM": {
        "company": "Qualcomm Inc.", "currency": "USD", "unit": "M",
        "net_income": 7200, "ebit": 9200, "revenue": 35800,
        "depreciation": 1500, "capex": 1800, "delta_wc": 1000,
        "total_debt": 14000, "cash": 8000, "shares_outstanding": 1100,
        "dividends_total": 3740, "tax_rate": 0.12,
        "debt_ratio": 0.20, "debt_ratio_changing": False,
        "cost_of_equity": 0.12, "wacc": 0.10,
        "firm_growth_rate": 0.10, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.30,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "CRM": {
        "company": "Salesforce Inc.", "currency": "USD", "unit": "M",
        "net_income": 4100, "ebit": 5800, "revenue": 34900,
        "depreciation": 2000, "capex": 900, "delta_wc": 1500,
        "total_debt": 8400, "cash": 9600, "shares_outstanding": 965,
        "dividends_total": 0, "tax_rate": 0.18,
        "debt_ratio": 0.12, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.10,
        "firm_growth_rate": 0.11, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.25,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "PLTR": {
        "company": "Palantir Technologies", "currency": "USD", "unit": "M",
        "net_income": 462, "ebit": 120, "revenue": 2230,
        "depreciation": 100, "capex": 50, "delta_wc": 200,
        "total_debt": 0, "cash": 3600, "shares_outstanding": 2150,
        "dividends_total": 0, "tax_rate": 0.10,
        "debt_ratio": 0.00, "debt_ratio_changing": False,
        "cost_of_equity": 0.15, "wacc": 0.14,
        "firm_growth_rate": 0.25, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 2.0,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "CRWD": {
        "company": "CrowdStrike Holdings", "currency": "USD", "unit": "M",
        "net_income": 89, "ebit": -200, "revenue": 3055,
        "depreciation": 300, "capex": 150, "delta_wc": 300,
        "total_debt": 2900, "cash": 3200, "shares_outstanding": 242,
        "dividends_total": 0, "tax_rate": 0.10,
        "debt_ratio": 0.15, "debt_ratio_changing": False,
        "cost_of_equity": 0.155, "wacc": 0.14,
        "firm_growth_rate": 0.28, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.9,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
        "startup_negative": True,
    },
    "WBD": {
        "company": "Warner Bros. Discovery", "currency": "USD", "unit": "M",
        "net_income": -3100, "ebit": 1800, "revenue": 39300,
        "depreciation": 5000, "capex": 1800, "delta_wc": 1000,
        "total_debt": 44000, "cash": 3000, "shares_outstanding": 2410,
        "dividends_total": 0, "tax_rate": 0.20,
        "debt_ratio": 0.55, "debt_ratio_changing": True,
        "cost_of_equity": 0.135, "wacc": 0.09,
        "firm_growth_rate": 0.03, "stable_growth": 0.03,
        "has_competitive_adv": False, "beta": 1.60,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
        "excess_debt_negative": True,
    },
    "NFLX": {
        "company": "Netflix Inc.", "currency": "USD", "unit": "M",
        "net_income": 7000, "ebit": 7000, "revenue": 38000,
        "depreciation": 700, "capex": 600, "delta_wc": 1000,
        "total_debt": 14500, "cash": 7000, "shares_outstanding": 430,
        "dividends_total": 0, "tax_rate": 0.15,
        "debt_ratio": 0.18, "debt_ratio_changing": False,
        "cost_of_equity": 0.115, "wacc": 0.10,
        "firm_growth_rate": 0.14, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.30,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "DIS": {
        "company": "Walt Disney Co.", "currency": "USD", "unit": "M",
        "net_income": 4900, "ebit": 9000, "revenue": 89000,
        "depreciation": 4500, "capex": 4800, "delta_wc": 1500,
        "total_debt": 44000, "cash": 5600, "shares_outstanding": 1830,
        "dividends_total": 1830, "tax_rate": 0.21,
        "debt_ratio": 0.25, "debt_ratio_changing": True,
        "cost_of_equity": 0.11, "wacc": 0.09,
        "firm_growth_rate": 0.07, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 1.05,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "PARA": {
        "company": "Paramount Global", "currency": "USD", "unit": "M",
        "net_income": -2900, "ebit": 500, "revenue": 28600,
        "depreciation": 2500, "capex": 1200, "delta_wc": 800,
        "total_debt": 14500, "cash": 2500, "shares_outstanding": 650,
        "dividends_total": 250, "tax_rate": 0.20,
        "debt_ratio": 0.50, "debt_ratio_changing": True,
        "cost_of_equity": 0.135, "wacc": 0.09,
        "firm_growth_rate": 0.03, "stable_growth": 0.03,
        "has_competitive_adv": False, "beta": 1.70,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
        "cyclical_negative": True,
    },
    "PG": {
        "company": "Procter & Gamble", "currency": "USD", "unit": "M",
        "net_income": 14800, "ebit": 18500, "revenue": 84000,
        "depreciation": 2800, "capex": 3500, "delta_wc": 1000,
        "total_debt": 28000, "cash": 10000, "shares_outstanding": 2360,
        "dividends_total": 9440, "tax_rate": 0.20,
        "debt_ratio": 0.18, "debt_ratio_changing": False,
        "cost_of_equity": 0.09, "wacc": 0.08,
        "firm_growth_rate": 0.05, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.60,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "WMT": {
        "company": "Walmart Inc.", "currency": "USD", "unit": "M",
        "net_income": 15500, "ebit": 27000, "revenue": 648100,
        "depreciation": 11000, "capex": 16000, "delta_wc": 2000,
        "total_debt": 37000, "cash": 9000, "shares_outstanding": 8050,
        "dividends_total": 6100, "tax_rate": 0.22,
        "debt_ratio": 0.15, "debt_ratio_changing": False,
        "cost_of_equity": 0.09, "wacc": 0.08,
        "firm_growth_rate": 0.05, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.55,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "LMT": {
        "company": "Lockheed Martin", "currency": "USD", "unit": "M",
        "net_income": 6900, "ebit": 9000, "revenue": 67600,
        "depreciation": 1300, "capex": 1800, "delta_wc": 500,
        "total_debt": 17000, "cash": 3000, "shares_outstanding": 240,
        "dividends_total": 3120, "tax_rate": 0.18,
        "debt_ratio": 0.40, "debt_ratio_changing": False,
        "cost_of_equity": 0.105, "wacc": 0.085,
        "firm_growth_rate": 0.06, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.80,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "GD": {
        "company": "General Dynamics", "currency": "USD", "unit": "M",
        "net_income": 3600, "ebit": 4800, "revenue": 42300,
        "depreciation": 700, "capex": 1100, "delta_wc": 400,
        "total_debt": 10000, "cash": 1500, "shares_outstanding": 270,
        "dividends_total": 1500, "tax_rate": 0.18,
        "debt_ratio": 0.30, "debt_ratio_changing": False,
        "cost_of_equity": 0.10, "wacc": 0.085,
        "firm_growth_rate": 0.06, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.85,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "NOC": {
        "company": "Northrop Grumman", "currency": "USD", "unit": "M",
        "net_income": 3900, "ebit": 5200, "revenue": 39300,
        "depreciation": 800, "capex": 1200, "delta_wc": 300,
        "total_debt": 13000, "cash": 3500, "shares_outstanding": 148,
        "dividends_total": 1110, "tax_rate": 0.18,
        "debt_ratio": 0.35, "debt_ratio_changing": False,
        "cost_of_equity": 0.105, "wacc": 0.085,
        "firm_growth_rate": 0.06, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.85,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "RTX": {
        "company": "RTX Corporation", "currency": "USD", "unit": "M",
        "net_income": 3500, "ebit": 7000, "revenue": 69000,
        "depreciation": 2500, "capex": 3000, "delta_wc": 800,
        "total_debt": 32000, "cash": 6000, "shares_outstanding": 1330,
        "dividends_total": 3190, "tax_rate": 0.20,
        "debt_ratio": 0.35, "debt_ratio_changing": True,
        "cost_of_equity": 0.11, "wacc": 0.085,
        "firm_growth_rate": 0.06, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 0.95,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "TSLA": {
        "company": "Tesla Inc.", "currency": "USD", "unit": "M",
        "net_income": 7900, "ebit": 8900, "revenue": 96800,
        "depreciation": 4700, "capex": 8900, "delta_wc": 2000,
        "total_debt": 5700, "cash": 16400, "shares_outstanding": 3210,
        "dividends_total": 0, "tax_rate": 0.15,
        "debt_ratio": 0.05, "debt_ratio_changing": False,
        "cost_of_equity": 0.14, "wacc": 0.13,
        "firm_growth_rate": 0.20, "stable_growth": 0.04,
        "has_competitive_adv": True, "beta": 2.0,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "P911.DE": {
        "company": "Porsche AG", "currency": "USD", "unit": "M",
        "net_income": 4400, "ebit": 6500, "revenue": 40000,
        "depreciation": 2500, "capex": 4000, "delta_wc": 1000,
        "total_debt": 8000, "cash": 5000, "shares_outstanding": 911,
        "dividends_total": 2000, "tax_rate": 0.25,
        "debt_ratio": 0.15, "debt_ratio_changing": False,
        "cost_of_equity": 0.11, "wacc": 0.095,
        "firm_growth_rate": 0.06, "stable_growth": 0.03,
        "has_competitive_adv": True, "beta": 1.10,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "F": {
        "company": "Ford Motor Co.", "currency": "USD", "unit": "M",
        "net_income": 4300, "ebit": 10000, "revenue": 176000,
        "depreciation": 7000, "capex": 8000, "delta_wc": 2000,
        "total_debt": 100000, "cash": 26000, "shares_outstanding": 3980,
        "dividends_total": 2400, "tax_rate": 0.20,
        "debt_ratio": 0.60, "debt_ratio_changing": True,
        "cost_of_equity": 0.13, "wacc": 0.085,
        "firm_growth_rate": 0.04, "stable_growth": 0.03,
        "has_competitive_adv": False, "beta": 1.50,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "VOW3.DE": {
        "company": "Volkswagen AG", "currency": "USD", "unit": "M",
        "net_income": 12000, "ebit": 20000, "revenue": 280000,
        "depreciation": 15000, "capex": 18000, "delta_wc": 3000,
        "total_debt": 120000, "cash": 40000, "shares_outstanding": 500,
        "dividends_total": 4500, "tax_rate": 0.25,
        "debt_ratio": 0.45, "debt_ratio_changing": True,
        "cost_of_equity": 0.12, "wacc": 0.08,
        "firm_growth_rate": 0.04, "stable_growth": 0.03,
        "has_competitive_adv": False, "beta": 1.30,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
    "HYMTF": {
        "company": "Hyundai Motor", "currency": "USD", "unit": "M",
        "net_income": 8500, "ebit": 11000, "revenue": 115000,
        "depreciation": 5000, "capex": 7000, "delta_wc": 2000,
        "total_debt": 20000, "cash": 12000, "shares_outstanding": 224,
        "dividends_total": 1800, "tax_rate": 0.22,
        "debt_ratio": 0.18, "debt_ratio_changing": False,
        "cost_of_equity": 0.11, "wacc": 0.095,
        "firm_growth_rate": 0.06, "stable_growth": 0.03,
        "has_competitive_adv": True, "beta": 1.10,
        "risk_free_rate": 0.043, "erp": 0.05,
        "inflation_rate": 0.024, "real_growth_rate": 0.02,
    },
}


# ═════════════════════════════════════════════════════════════════════════════
#  LIVE FETCH — works for ANY listed ticker via yfinance
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# Ensure every hardcoded entry has all keys valuation_engine needs
# (older entries may be missing optional boolean flags)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "cyclical_negative":    False,
    "temporary_negative":   False,
    "excess_debt_negative": False,
    "bankruptcy_likely":    False,
    "startup_negative":     False,
    "stable_growth":        None,   # computed below if missing
    "inflation_rate":       0.03,
    "real_growth_rate":     0.02,
}

for _ticker, _fd in FUNDAMENTAL_DATA.items():
    for _k, _v in _DEFAULTS.items():
        if _k not in _fd:
            if _k == "stable_growth" and _v is None:
                _fd["stable_growth"] = round(
                    _fd.get("inflation_rate", 0.03) + _fd.get("real_growth_rate", 0.02) * 0.5, 4
                )
            else:
                _fd[_k] = _v
    # Infer startup/excess_debt from data if not set
    if _fd.get("net_income", 0) < 0:
        if _fd.get("debt_ratio", 0) > 0.50:
            _fd["excess_debt_negative"] = True
        rev = _fd.get("revenue", 9999)
        if rev < (1000 if _fd.get("currency") == "INR" else 500):
            _fd["startup_negative"] = True


def _fetch_live_fundamentals(ticker: str) -> dict:
    """
    Auto-fetches fundamentals from yfinance for any listed company.
    Indian stocks (.NS / .BO) → ₹ Crores | US stocks → $ Millions
    """
    import yfinance as yf

    t = yf.Ticker(ticker)
    info = t.info

    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    currency  = "INR" if is_indian else "USD"
    unit      = "Cr"  if is_indian else "M"
    scale     = 1e-7  if is_indian else 1e-6

    def safe(keys, fallback=0):
        for k in keys:
            v = info.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
        return float(fallback)

    net_income = safe(["netIncomeToCommon"]) * scale
    revenue    = safe(["totalRevenue"]) * scale
    ebit       = safe(["operatingIncome", "ebit"]) * scale
    total_debt = safe(["totalDebt"]) * scale
    cash       = safe(["totalCash"]) * scale
    shares_raw = safe(["sharesOutstanding"])
    shares     = shares_raw * scale
    beta       = safe(["beta"], 1.0)

    # Cash flow items — try statements first, else estimate
    depreciation = revenue * 0.03
    capex        = revenue * 0.04
    delta_wc     = revenue * 0.01
    try:
        cf = t.cashflow
        if cf is not None and not cf.empty:
            col = cf.columns[0]
            for k in ["Depreciation & Amortization", "Depreciation Amortization Depletion"]:
                if k in cf.index:
                    depreciation = abs(float(cf.loc[k, col])) * scale
                    break
            for k in ["Capital Expenditure", "Purchase Of PPE"]:
                if k in cf.index:
                    capex = abs(float(cf.loc[k, col])) * scale
                    break
    except Exception:
        pass

    div_per_share  = safe(["dividendsPerShare", "lastDividendValue"])
    dividends_total = div_per_share * shares_raw * scale

    if is_indian:
        risk_free_rate, erp, inflation_rate, real_growth_rate = 0.072, 0.065, 0.05, 0.06
        tax_rate = 0.25
    else:
        risk_free_rate, erp, inflation_rate, real_growth_rate = 0.043, 0.05, 0.024, 0.02
        tax_rate = safe(["effectiveTaxRate"], 0.21)
        if not (0 < tax_rate < 0.60):
            tax_rate = 0.21

    cost_of_equity = risk_free_rate + max(beta, 0.3) * erp

    market_cap  = safe(["marketCap"]) * scale
    firm_value  = market_cap + total_debt - cash
    debt_ratio  = min(max(total_debt / firm_value if firm_value > 0 else 0.20, 0), 0.95)
    kd          = (risk_free_rate + 0.02) * (1 - tax_rate)
    wacc        = cost_of_equity * (1 - debt_ratio) + kd * debt_ratio

    firm_growth_rate = safe(["earningsGrowth", "revenueGrowth"], 0.08)
    if not (-0.30 < firm_growth_rate < 1.0):
        firm_growth_rate = 0.08
    stable_growth = inflation_rate + real_growth_rate * 0.5

    profit_margin    = (net_income / revenue) if revenue > 0 else 0
    has_competitive_adv = profit_margin > 0.15
    debt_ratio_changing = debt_ratio > 0.30 or abs(firm_growth_rate) > 0.20
    startup_negative    = net_income < 0 and revenue < (1000 if is_indian else 500)
    excess_debt_negative = net_income < 0 and debt_ratio > 0.50

    company = info.get("longName") or info.get("shortName") or ticker

    return {
        "company": company, "currency": currency, "unit": unit,
        "net_income":  round(net_income, 2),
        "ebit":        round(ebit, 2),
        "revenue":     round(revenue, 2),
        "depreciation":round(depreciation, 2),
        "capex":       round(capex, 2),
        "delta_wc":    round(delta_wc, 2),
        "total_debt":  round(total_debt, 2),
        "cash":        round(cash, 2),
        "shares_outstanding": round(shares, 4),
        "dividends_total":    round(dividends_total, 2),
        "tax_rate":    round(tax_rate, 4),
        "debt_ratio":  round(debt_ratio, 4),
        "debt_ratio_changing": bool(debt_ratio_changing),
        "cost_of_equity": round(cost_of_equity, 4),
        "wacc":        round(wacc, 4),
        "firm_growth_rate": round(firm_growth_rate, 4),
        "stable_growth":    round(stable_growth, 4),
        "has_competitive_adv": bool(has_competitive_adv),
        "beta":        round(beta, 3),
        "risk_free_rate": risk_free_rate,
        "erp":         erp,
        "inflation_rate":    inflation_rate,
        "real_growth_rate":  real_growth_rate,
        "startup_negative":      bool(startup_negative),
        "cyclical_negative":     False,
        "excess_debt_negative":  bool(excess_debt_negative),
        "bankruptcy_likely":     False,
        "temporary_negative":    False,
        "_live_fetched": True,
    }


def get_fundamental_data(ticker: str) -> dict:
    """
    Returns fundamental data dict for a given ticker.
    Uses hardcoded data if available; falls back to live yfinance for any other ticker.
    """
    if ticker in FUNDAMENTAL_DATA:
        return FUNDAMENTAL_DATA[ticker]
    try:
        return _fetch_live_fundamentals(ticker)
    except Exception as e:
        raise ValueError(
            f"Could not fetch fundamental data for '{ticker}'. "
            f"Live fetch error: {e}\n"
            f"Add manual data to FUNDAMENTAL_DATA in financial_data.py if live fetch fails."
        )
