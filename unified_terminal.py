"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  UNIFIED EQUITY RESEARCH TERMINAL  v4.0                                      ║
║  Research · Valuation · Monte Carlo · Risk · Capital Structure · News        ║
║  US (NYSE/NASDAQ · $B) + India (NSE/BSE · ₹Cr)  ·  Damodaran Framework      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  RUN:  streamlit run unified_terminal.py                                     ║
║  DEPS: pip install streamlit yfinance plotly pandas numpy feedparser         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import re
import sys
import traceback
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime

# ── Import helper modules ──────────────────────────────────────────────────────
try:
    from data_fetch       import get_stock_data
    from monte_carlo      import run_simulation
    from risk_metrics     import calculate_metrics
    from valuation_engine import run_valuation
    from financial_data   import FUNDAMENTAL_DATA
    _HAS_ADVANCED = True
except ImportError:
    _HAS_ADVANCED = False

try:
    from data_audit   import run_data_audit
    from cross_verify import cross_verify_and_correct
    _HAS_AUDIT = True
except ImportError:
    _HAS_AUDIT = False


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & PALETTE
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Equity Research Terminal",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sandstone & Clay (Organic Premium) — matching dashboard.py ───────────────
C = {
    # ── Surfaces ──────────────────────────────────────────────
    "bg":        "#F4F1EE",   # warm parchment — app background
    "surface":   "#EBE7E2",   # soft stone — sidebar, tabs bg
    "card":      "#EBE7E2",   # stone card background
    "chart_bg":  "#EBE7E2",   # chart paper background
    "border":    "#D6CFC7",   # warm stone border
    "border2":   "#C8BFB5",   # stronger border
    # ── Text ──────────────────────────────────────────────────
    "text":      "#2D2926",   # warm near-black — primary text
    "muted":     "#6B6661",   # warm gray — labels & secondary
    "subtle":    "#8E8982",   # medium warm gray — hints & timestamps
    # ── Brand (Bronze) ─────────────────────────────────────────
    "primary":   "#8C7851",   # bronze — main interactive colour
    "accent":    "#8C7851",   # alias
    "accent2":   "#7A6840",   # darker bronze for hover / fills
    "accent_bg": "#EBE7E2",   # stone tint — narrative bg
    "gold":      "#8C7851",   # bronze (premium accent)
    "gold_dk":   "#6A5A35",   # darker bronze for text
    "gold_bg":   "#EBE7E2",   # stone bg
    "secondary": "#7A656D",   # plum
    # ── Sidebar aliases ───────────────────────────────────────
    "sidebar":   "#EBE7E2",
    "sb_text":   "#2D2926",
    "sb_head":   "#2D2926",
    # ── Semantic green (Sage) ─────────────────────────────────
    "green":     "#5F7161",   # sage green
    "green_bg":  "#D2D6D0",   # sage tint
    "green_bd":  "#5F7161",   # sage border
    "green_t":   "#2B3A30",   # dark sage — text on sage bg
    # ── Semantic red (Terra) ──────────────────────────────────
    "red":       "#9D5C58",   # terra red
    "red_bg":    "#E4D4D3",   # terracotta tint
    "red_bd":    "#9D5C58",   # terra border
    "red_t":     "#5C3A38",   # dark terra — text on terra bg
    # ── Semantic amber (Clay) ─────────────────────────────────
    "amber":     "#B58A54",   # clay amber
    "amber_bg":  "#E9DFCE",   # warm clay tint
    "amber_bd":  "#B58A54",   # clay border
    "amber_t":   "#543C16",   # dark clay — text on clay bg
    # ── Plum ──────────────────────────────────────────────────
    "purple":    "#7A656D",   # dusty plum
    "purple_bg": "#E8E0E4",   # plum tint
    "purple_t":  "#3D2F35",   # darkest plum
    # ── Terra (alias teal → sage) ─────────────────────────────
    "teal":      "#5F7161",   # sage (reused)
    "teal_bg":   "#D2D6D0",   # sage tint
    "teal_t":    "#2B3A30",   # dark sage
}

# ── Global CSS — Soft Luxury Neutrals ────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ─────────────── RESET ─────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body,
[data-testid="stApp"],
[data-testid="stMain"],
.main {{
  background-color: {C['bg']} !important;
  color: {C['text']};
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}}
.block-container {{
  padding: 1.2rem 2.4rem 3rem !important;
  max-width: 1560px !important;
}}

/* ─────────────── SIDEBAR ─────────────── */
[data-testid="stSidebar"] {{
  background: {C['surface']} !important;
  border-right: 2px solid {C['border2']} !important;
}}
[data-testid="stSidebar"] * {{
  color: {C['text']} !important;
  font-family: 'Inter', sans-serif !important;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stRadio > label {{
  font-size: 0.60rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 2px !important;
  color: {C['muted']} !important;
}}
[data-testid="stSidebar"] .stRadio label span {{
  font-size: 0.86rem !important;
  font-weight: 500 !important;
  color: {C['text']} !important;
}}
[data-testid="stSidebar"] .stTextInput input {{
  background: {C['card']} !important;
  border: 1.5px solid {C['border2']} !important;
  border-radius: 6px !important;
  color: {C['text']} !important;
  font-size: 0.84rem !important;
}}
[data-testid="stSidebar"] hr {{ border-color: {C['border2']} !important; }}

/* ─────────────── TYPOGRAPHY ─────────────── */
h1, h2 {{
  font-family: 'Inter', sans-serif !important;
  color: {C['text']} !important;
  font-weight: 800 !important;
  letter-spacing: -0.3px;
}}
h3, h4 {{
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  color: {C['text']} !important;
}}
code, pre {{
  font-family: 'JetBrains Mono', monospace !important;
  background: {C['surface']} !important;
  border: 1px solid {C['border2']} !important;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 0.82rem !important;
  color: {C['text']} !important;
}}

/* ─────────────── SECTION HEADING ─────────────── */
.sec-head {{
  font-size: 0.60rem;
  font-weight: 700;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: {C['muted']};
  border-bottom: 2px solid {C['border2']};
  padding-bottom: 8px;
  margin: 1.8rem 0 1.1rem;
  font-family: 'Inter', sans-serif;
}}

/* ─────────────── CARDS ─────────────── */
.card {{
  background: {C['card']};
  border: 1px solid {C['border']};
  border-radius: 12px;
  padding: 1.3rem 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 5px rgba(0,0,0,.07);
  color: {C['text']};
}}
.card-l {{
  background: {C['card']};
  border: 1px solid {C['border']};
  border-left: 3px solid {C['primary']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['text']};
}}
.card-gold {{
  background: {C['gold_bg']};
  border: 1px solid {C['amber_bd']};
  border-left: 3px solid {C['gold']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['amber_t']};
}}
.card-g {{
  background: {C['green_bg']};
  border: 1px solid {C['green_bd']};
  border-left: 3px solid {C['green']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['green_t']};
}}
.card-r {{
  background: {C['red_bg']};
  border: 1px solid {C['red_bd']};
  border-left: 3px solid {C['red']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['red_t']};
}}
.card-a {{
  background: {C['amber_bg']};
  border: 1px solid {C['amber_bd']};
  border-left: 3px solid {C['amber']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['amber_t']};
}}
.card-p {{
  background: {C['purple_bg']};
  border: 1px solid #A89EE8;
  border-left: 3px solid {C['purple']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['purple_t']};
}}
.card-t {{
  background: {C['teal_bg']};
  border: 1px solid #7CBECE;
  border-left: 3px solid {C['teal']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  color: {C['teal_t']};
}}

/* ─────────────── KPI TILES ─────────────── */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin: 1rem 0;
}}
.kpi {{
  background: {C['card']};
  border: 1px solid {C['border']};
  border-radius: 10px;
  padding: 1rem 1.1rem;
  text-align: center;
  transition: border-color .18s, box-shadow .18s, transform .12s;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}}
.kpi:hover {{
  border-color: {C['primary']};
  box-shadow: 0 4px 16px rgba(140,120,81,.18);
  transform: translateY(-1px);
}}
.kpi-label {{
  font-size: 0.58rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: {C['muted']};
  margin-bottom: 7px;
}}
.kpi-value {{
  font-size: 1.45rem;
  font-weight: 800;
  color: {C['text']};
  font-family: 'Inter', sans-serif;
  line-height: 1.05;
}}
.kpi-sub {{
  font-size: 0.63rem;
  color: {C['subtle']};
  margin-top: 5px;
}}

/* ─────────────── PRICE HERO ─────────────── */
.price-hero {{
  background: {C['card']};
  border: 1px solid {C['border']};
  border-top: 4px solid {C['primary']};
  border-radius: 0 0 16px 16px;
  padding: 2rem 2.2rem;
  margin-bottom: 1.6rem;
  box-shadow: 0 2px 12px rgba(0,0,0,.06);
}}
.price-main {{
  font-family: 'Inter', sans-serif;
  font-size: 3rem;
  font-weight: 800;
  color: {C['text']};
  line-height: 1.05;
  letter-spacing: -1px;
}}
.price-change-up {{ color: {C['green']}; font-size: 1rem; font-weight: 700; }}
.price-change-dn {{ color: {C['red']};   font-size: 1rem; font-weight: 700; }}
.company-name {{
  font-family: 'Inter', sans-serif;
  font-size: 1.6rem;
  font-weight: 800;
  color: {C['text']};
  letter-spacing: -0.2px;
}}
.company-meta {{ font-size: 0.76rem; color: {C['muted']}; margin-top: 5px; letter-spacing: 0.2px; font-weight: 500; }}

/* ─────────────── CHIPS ─────────────── */
.chip {{
  display: inline-block;
  padding: 3px 11px;
  border-radius: 999px;
  font-size: 0.67rem;
  font-weight: 700;
  letter-spacing: 0.4px;
  border: 1px solid transparent;
}}
.chip-g {{ background: {C['green_bg']}; color: {C['green_t']}; border-color: {C['green_bd']}; }}
.chip-r {{ background: {C['red_bg']};   color: {C['red_t']};   border-color: {C['red_bd']};   }}
.chip-a {{ background: {C['amber_bg']}; color: {C['amber_t']}; border-color: {C['amber_bd']}; }}
.chip-b {{ background: {C['border']};   color: {C['text']};     border-color: {C['border2']};  }}
.chip-p {{ background: {C['purple_bg']}; color: {C['purple_t']}; border-color: {C['secondary']}; }}
.chip-t {{ background: {C['teal_bg']};  color: {C['teal_t']};  border-color: {C['teal']};     }}
.chip-gold {{ background: {C['gold_bg']}; color: {C['gold_dk']}; border-color: {C['gold']};    }}

/* ─────────────── NEWS ─────────────── */
.news-pos {{
  background: {C['green_bg']};
  border-left: 3px solid {C['green']};
  padding: 0.85rem 1rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 0.55rem;
}}
.news-neg {{
  background: {C['red_bg']};
  border-left: 3px solid {C['red']};
  padding: 0.85rem 1rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 0.55rem;
}}
.news-neu {{
  background: {C['surface']};
  border-left: 3px solid {C['border2']};
  padding: 0.85rem 1rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 0.55rem;
}}
.news-title {{ font-size: 0.87rem; font-weight: 600; color: {C['text']}; line-height: 1.5; }}
.news-meta  {{ font-size: 0.67rem; color: {C['muted']}; margin-top: 4px; font-weight: 500; }}

/* ─────────────── TABLES ─────────────── */
.stDataFrame td, .stDataFrame th {{
  font-size: 0.82rem !important;
  font-family: 'Inter', sans-serif !important;
  color: {C['text']} !important;
  border-color: {C['border']} !important;
}}
.stDataFrame th {{
  background: {C['border']} !important;
  color: {C['text']} !important;
  font-weight: 700 !important;
  font-size: 0.62rem !important;
  text-transform: uppercase !important;
  letter-spacing: 1.3px !important;
  border-bottom: 2px solid {C['primary']} !important;
}}
.stDataFrame tr:nth-child(even) td {{ background: {C['surface']} !important; }}
.stDataFrame tr:hover td {{ background: {C['border']} !important; }}

/* ─────────────── METRICS ─────────────── */
div[data-testid="stMetric"] {{
  background: {C['card']} !important;
  border: 1px solid {C['border']} !important;
  border-radius: 10px !important;
  padding: 14px 18px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.06) !important;
}}
div[data-testid="stMetric"] label {{
  color: {C['muted']} !important;
  font-size: 0.64rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  font-family: 'Inter', sans-serif !important;
}}
div[data-testid="stMetricValue"] {{
  color: {C['text']} !important;
  font-weight: 800 !important;
  font-family: 'Inter', sans-serif !important;
}}

/* ─────────────── TABS ─────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background: {C['surface']} !important;
  border-bottom: 2px solid {C['border2']};
  padding: 0 4px;
  border-radius: 8px 8px 0 0;
}}
.stTabs [data-baseweb="tab"] {{
  color: {C['muted']} !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  background: transparent !important;
  padding: 10px 18px;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: {C['primary']} !important; }}
.stTabs [aria-selected="true"] {{
  color: {C['primary']} !important;
  border-bottom-color: {C['primary']} !important;
  font-weight: 700 !important;
  background: transparent !important;
}}

/* ─────────────── EXPANDER ─────────────── */
.streamlit-expanderHeader {{
  background: {C['surface']} !important;
  border: 1px solid {C['border2']} !important;
  border-radius: 8px !important;
  color: {C['primary']} !important;
  font-weight: 600 !important;
  font-size: 0.87rem !important;
}}
.streamlit-expanderContent {{
  background: {C['card']} !important;
  border: 1px solid {C['border']} !important;
  border-top: none !important;
  border-radius: 0 0 8px 8px !important;
}}

/* ─────────────── NARRATIVE BLOCK ─────────────── */
.narrative {{
  background: linear-gradient(135deg, {C['accent_bg']} 0%, {C['surface']} 100%);
  border-left: 3px solid {C['primary']};
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.4rem;
  font-size: 0.88rem;
  line-height: 1.9;
  color: {C['text']};
  margin-bottom: 1.2rem;
  font-style: italic;
  box-shadow: 0 1px 4px rgba(140,120,81,.12);
}}

/* ─────────────── ROW LIST ─────────────── */
.row-item {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid {C['border']};
  font-size: 0.84rem;
  color: {C['text']};
}}
.row-item:last-child {{ border-bottom: none; }}
.row-label {{ color: {C['muted']}; font-size: 0.82rem; font-weight: 500; }}
.row-val   {{ font-weight: 700; color: {C['text']}; }}

/* ─────────────── AUDIT FLAGS ─────────────── */
.af-r {{ background:{C['red_bg']};   border-left:3px solid {C['red']};   padding:9px 14px; border-radius:0 7px 7px 0; margin:4px 0; font-size:.85rem; color:{C['red_t']};   font-weight:600; }}
.af-y {{ background:{C['amber_bg']}; border-left:3px solid {C['amber']}; padding:9px 14px; border-radius:0 7px 7px 0; margin:4px 0; font-size:.85rem; color:{C['amber_t']}; font-weight:600; }}
.af-g {{ background:{C['green_bg']}; border-left:3px solid {C['green']}; padding:9px 14px; border-radius:0 7px 7px 0; margin:4px 0; font-size:.85rem; color:{C['green_t']}; font-weight:600; }}

/* ─────────────── MISC ─────────────── */
hr {{ border:none; border-top:1px solid {C['border2']} !important; margin:1.3rem 0 !important; }}
.stSpinner > div {{ border-top-color: {C['primary']} !important; }}
.stDeployButton, #MainMenu, footer {{ display: none !important; }}
/* Slim scrollbar */
::-webkit-scrollbar {{ width:6px; height:6px; }}
::-webkit-scrollbar-track {{ background:{C['surface']}; }}
::-webkit-scrollbar-thumb {{ background:{C['border2']}; border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background:{C['muted']}; }}
/* Slider accent */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{ background:{C['primary']} !important; border-color:{C['primary']} !important; }}
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stTickBarMax"] {{ color:{C['muted']}; }}
/* Select boxes */
[data-testid="stSelectbox"] [data-baseweb="select"] div {{
  background:{C['card']} !important;
  border-color:{C['border2']} !important;
  color:{C['text']} !important;
  font-family:'Inter',sans-serif !important;
}}
/* Info / warning / error boxes */
div[data-testid="stAlert"] {{
  border-radius: 8px !important;
  font-size: 0.85rem !important;
  font-family: 'Inter', sans-serif !important;
}}
/* Plotly chart container */
.js-plotly-plot, .plotly, .plot-container {{
  background: {C['chart_bg']} !important;
  border-radius: 10px;
}}

/* ─────────────── ANIMATIONS ─────────────── */
@keyframes fadeInUp {{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes slideInLeft {{from{{opacity:0;transform:translateX(-20px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes pulseRing {{0%,100%{{box-shadow:0 0 0 0 rgba(140,120,81,.2)}}60%{{box-shadow:0 0 0 12px rgba(140,120,81,0)}}}}

/* ─────────────── STEP BADGES ─────────────── */
.sb {{
  display: inline-flex; align-items: center; padding: 5px 15px;
  border-radius: 20px; font-weight: 700; font-size: .8rem;
  letter-spacing: .5px; animation: slideInLeft .35s ease both;
  font-family: 'Inter', sans-serif;
}}
.sb-bronze {{ background: {C['primary']};   color: #F4F1EE; }}
.sb-terra  {{ background: #A76D60;           color: #F4F1EE; }}
.sb-plum   {{ background: {C['secondary']}; color: #F4F1EE; }}
.sb-sage   {{ background: {C['green']};      color: #F4F1EE; }}

/* ─────────────── DCF COMPONENTS ─────────────── */
.iv-hero {{
  border: 2px solid {C['primary']}; border-radius: 16px; padding: 28px;
  text-align: center; background: {C['card']};
  animation: pulseRing 3s ease infinite;
}}
.rat {{
  background: {C['card']}; border-left: 3px solid {C['primary']};
  border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 8px 0;
  font-size: .89rem; color: {C['text']}; line-height: 1.65;
}}
.rej {{
  background: {C['red_bg']}; border-left: 3px solid {C['red']};
  border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 5px 0;
  font-size: .87rem; color: {C['red_t']};
}}
.arow {{
  display: flex; justify-content: space-between; padding: 7px 12px;
  border-radius: 7px; margin: 3px 0; font-size: .87rem;
  background: {C['card']}; border: 1px solid {C['border']}; color: {C['text']};
}}
.arow:hover {{ background: {C['border']}; }}

/* Sensitivity heat cells */
.sens-hot  {{ background: {C['red_bg']};   color: {C['red_t']};   font-weight: 700; border-radius: 4px; padding: 4px 8px; }}
.sens-mid  {{ background: {C['amber_bg']}; color: {C['amber_t']}; font-weight: 600; border-radius: 4px; padding: 4px 8px; }}
.sens-cold {{ background: {C['green_bg']}; color: {C['green_t']}; font-weight: 700; border-radius: 4px; padding: 4px 8px; }}

/* ─────────────── BRAND / FOOTER ─────────────── */
.brand {{ font-family:'Inter', sans-serif; font-size:1.05rem; color:{C['text']}; letter-spacing:-0.3px; font-weight:700; }}
.brand-dot {{ color: {C['gold']}; }}
.footer {{
  font-size: 0.67rem; color: {C['subtle']}; text-align: center;
  margin-top: 3rem; border-top: 1px solid {C['border2']};
  padding-top: 1.2rem; line-height: 2.3;
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY DATABASE
# ══════════════════════════════════════════════════════════════════════════════
INDIA_COMPANIES = {
    "Reliance Industries":"RELIANCE.NS","Tata Consultancy Services":"TCS.NS",
    "HDFC Bank":"HDFCBANK.NS","Infosys":"INFY.NS","ICICI Bank":"ICICIBANK.NS",
    "Hindustan Unilever":"HINDUNILVR.NS","ITC":"ITC.NS","State Bank of India":"SBIN.NS",
    "Bharti Airtel":"BHARTIARTL.NS","Kotak Mahindra Bank":"KOTAKBANK.NS",
    "Axis Bank":"AXISBANK.NS","Wipro":"WIPRO.NS","HCL Technologies":"HCLTECH.NS",
    "Asian Paints":"ASIANPAINT.NS","Maruti Suzuki":"MARUTI.NS",
    "Bajaj Finance":"BAJFINANCE.NS","Titan Company":"TITAN.NS",
    "Sun Pharmaceutical":"SUNPHARMA.NS","Divi's Laboratories":"DIVISLAB.NS",
    "Tech Mahindra":"TECHM.NS","UltraTech Cement":"ULTRACEMCO.NS",
    "NTPC":"NTPC.NS","Tata Motors":"TATAMOTORS.NS","Tata Steel":"TATASTEEL.NS",
    "JSW Steel":"JSWSTEEL.NS","Hindalco Industries":"HINDALCO.NS",
    "Bajaj Auto":"BAJAJ-AUTO.NS","Hero MotoCorp":"HEROMOTOCO.NS",
    "Mahindra & Mahindra":"M&M.NS","Eicher Motors":"EICHERMOT.NS",
    "Adani Ports":"ADANIPORTS.NS","Coal India":"COALINDIA.NS","ONGC":"ONGC.NS",
    "Indian Oil Corporation":"IOC.NS","BPCL":"BPCL.NS","GAIL India":"GAIL.NS",
    "Cipla":"CIPLA.NS","Dr. Reddy's Labs":"DRREDDY.NS","Lupin":"LUPIN.NS",
    "Apollo Hospitals":"APOLLOHOSP.NS","Dabur India":"DABUR.NS",
    "Britannia Industries":"BRITANNIA.NS","Zomato":"ZOMATO.NS",
    "LTIMindtree":"LTIM.NS","Persistent Systems":"PERSISTENT.NS",
    "Larsen & Toubro":"LT.NS","Siemens India":"SIEMENS.NS",
    "IndusInd Bank":"INDUSINDBK.NS","IndiGo":"INDIGO.NS",
}

US_COMPANIES = {
    "Apple":"AAPL","Microsoft":"MSFT","Alphabet (Google)":"GOOGL","Amazon":"AMZN",
    "NVIDIA":"NVDA","Meta Platforms":"META","Tesla":"TSLA","Broadcom":"AVGO",
    "Oracle":"ORCL","Salesforce":"CRM","Adobe":"ADBE","AMD":"AMD","Intel":"INTC",
    "Qualcomm":"QCOM","Texas Instruments":"TXN","Applied Materials":"AMAT",
    "ServiceNow":"NOW","Snowflake":"SNOW","Palantir":"PLTR","CrowdStrike":"CRWD",
    "Palo Alto Networks":"PANW","Cloudflare":"NET","Datadog":"DDOG",
    "Netflix":"NFLX","Uber":"UBER","Airbnb":"ABNB","PayPal":"PYPL","Shopify":"SHOP",
    "JPMorgan Chase":"JPM","Berkshire Hathaway":"BRK-B","Visa":"V","Mastercard":"MA",
    "Bank of America":"BAC","Goldman Sachs":"GS","Morgan Stanley":"MS",
    "UnitedHealth Group":"UNH","Johnson & Johnson":"JNJ","Eli Lilly":"LLY",
    "AbbVie":"ABBV","Merck":"MRK","Pfizer":"PFE","Amgen":"AMGN",
    "Walmart":"WMT","Procter & Gamble":"PG","Home Depot":"HD","Coca-Cola":"KO",
    "PepsiCo":"PEP","Costco":"COST","McDonald's":"MCD","Nike":"NKE",
    "ExxonMobil":"XOM","Chevron":"CVX","Caterpillar":"CAT","Boeing":"BA",
    "Lockheed Martin":"LMT","NextEra Energy":"NEE","American Tower":"AMT",
    "Lowe's":"LOW","Target":"TGT","Starbucks":"SBUX","FedEx":"FDX","UPS":"UPS",
}

SECTOR_PEERS = {
    "US_SEMI":    ["NVDA","AMD","INTC","QCOM","AVGO","TXN","AMAT"],
    "US_TECH":    ["AAPL","MSFT","GOOGL","META","NVDA","AMZN","ORCL","ADBE","CRM"],
    "US_CLOUD":   ["MSFT","AMZN","GOOGL","SNOW","DDOG","NOW","CRM","WDAY"],
    "US_CYBER":   ["PANW","CRWD","NET","PLTR"],
    "US_FIN":     ["JPM","BAC","WFC","GS","MS","V","MA","AXP"],
    "US_HEALTH":  ["UNH","JNJ","LLY","ABBV","MRK","PFE","AMGN"],
    "US_CONSUMER":["WMT","COST","HD","MCD","NKE","SBUX","TGT"],
    "US_STAPLES": ["PG","KO","PEP"],
    "US_ENERGY":  ["XOM","CVX","COP","EOG"],
    "US_INDUST":  ["CAT","DE","HON","GE","BA","LMT","UNP","FDX"],
    "IN_IT":      ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS","PERSISTENT.NS"],
    "IN_BANK":    ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS","SBIN.NS","INDUSINDBK.NS"],
    "IN_PHARMA":  ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","LUPIN.NS"],
    "IN_AUTO":    ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","EICHERMOT.NS"],
    "IN_ENERGY":  ["RELIANCE.NS","ONGC.NS","IOC.NS","BPCL.NS","GAIL.NS"],
}
INDUSTRY_KEY = {
    "semiconductors":"US_SEMI","semiconductor equipment":"US_SEMI",
    "technology":"US_TECH","internet":"US_TECH","software":"US_TECH",
    "cloud computing":"US_CLOUD","information technology":"US_TECH",
    "cybersecurity":"US_CYBER","information technology":"IN_IT","it consulting":"IN_IT",
    "banks":"IN_BANK","banking":"IN_BANK","investment banking":"US_FIN",
    "pharmaceuticals":"IN_PHARMA","drug manufacturers":"US_HEALTH","biotechnology":"US_HEALTH",
    "auto":"IN_AUTO","automobile":"IN_AUTO",
    "oil":"IN_ENERGY","energy":"US_ENERGY","oil and gas":"US_ENERGY",
    "industrials":"US_INDUST","aerospace & defense":"US_INDUST",
    "consumer":"US_CONSUMER","beverages":"US_STAPLES","household products":"US_STAPLES",
}


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def _extract_row(df, *keys):
    if df is None or df.empty: return pd.Series(dtype=float)
    norm_to_orig = {_norm(k): k for k in df.index}
    for key in keys:
        if key in df.index: return df.loc[key]
        nk = _norm(key)
        if nk in norm_to_orig: return df.loc[norm_to_orig[nk]]
    return pd.Series(dtype=float)

def safe_f(x, default=0.0):
    try:
        v = float(x)
        return default if (np.isnan(v) or np.isinf(v)) else v
    except: return default

def is_india(ticker):
    return ticker.upper().endswith(".NS") or ticker.upper().endswith(".BO")

def _sym(c): return "₹" if c=="INR" else "$"
def _lbl(c): return "Cr" if c=="INR" else "B"
def _div(c): return 1e7  if c=="INR" else 1e9

def fmt_price(p, c): return f"{'₹' if c=='INR' else '$'}{p:,.2f}"
def fmt_mcap(m, c):
    if m==0: return "—"
    return f"{'₹' if c=='INR' else '$'}{m/1e7:,.0f} Cr" if c=="INR" else f"${ m/1e9:.2f}B"
def fmt_val(v, c, dec=0):
    if v==0: return "—"
    return f"{_sym(c)}{v/_div(c):,.{dec}f} {_lbl(c)}"
def fmt_pct(v): return f"{v:.1f}%" if v!=0 else "—"
def _is_indian(ticker): return is_india(ticker)


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def get_live_price(ticker):
    default_currency = "INR" if is_india(ticker) else "USD"
    out = {"price":0.0,"prev_close":0.0,"change":0.0,"change_pct":0.0,
           "volume":"—","market_cap":"—","mcap_raw":0.0,"52w_high":0.0,
           "52w_low":0.0,"pe":0.0,"fwd_pe":0.0,"pb":0.0,"div_yield":0.0,
           "beta":1.0,"shares":0.0,"sector":"—","industry":"—",
           "long_name":ticker,"country":"—","currency":default_currency,
           "website":"","summary":"","employees":0}
    try:
        t = yf.Ticker(ticker)
        try:
            fi = t.fast_info
            out["price"]     = safe_f(fi.last_price)
            out["prev_close"]= safe_f(fi.previous_close or fi.regular_market_previous_close)
            out["mcap_raw"]  = safe_f(fi.market_cap)
            out["52w_high"]  = safe_f(fi.fifty_two_week_high)
            out["52w_low"]   = safe_f(fi.fifty_two_week_low)
            out["shares"]    = safe_f(fi.shares)
            cur = str(getattr(fi,"currency",default_currency) or default_currency).upper()
            out["currency"]  = cur
        except: pass
        try:
            info = t.info or {}
            if out["price"]==0.0:
                out["price"] = safe_f(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("ask"))
            if out["prev_close"]==0.0:
                out["prev_close"] = safe_f(info.get("previousClose") or info.get("regularMarketPreviousClose"), out["price"])
            if out["mcap_raw"]==0.0:  out["mcap_raw"]= safe_f(info.get("marketCap"))
            if out["52w_high"]==0.0:  out["52w_high"]= safe_f(info.get("fiftyTwoWeekHigh"), out["price"])
            if out["52w_low"]==0.0:   out["52w_low"] = safe_f(info.get("fiftyTwoWeekLow"),  out["price"])
            if out["shares"]==0.0:    out["shares"]  = safe_f(info.get("sharesOutstanding"))
            out["pe"]       = safe_f(info.get("trailingPE"))
            out["fwd_pe"]   = safe_f(info.get("forwardPE"))
            out["pb"]       = safe_f(info.get("priceToBook"))
            out["div_yield"]= safe_f(info.get("dividendYield",0))*100
            out["beta"]     = safe_f(info.get("beta"),1.0)
            out["sector"]   = info.get("sector","—") or "—"
            out["industry"] = info.get("industry","—") or "—"
            out["long_name"]= info.get("longName",ticker) or ticker
            out["country"]  = info.get("country","—") or "—"
            out["website"]  = info.get("website","") or ""
            out["summary"]  = info.get("longBusinessSummary","") or ""
            out["employees"]= int(info.get("fullTimeEmployees",0) or 0)
            if out["currency"]==default_currency:
                out["currency"] = str(info.get("currency",default_currency) or default_currency).upper()
        except: pass
        if out["price"]==0.0:
            try:
                h = t.history(period="5d")
                if not h.empty:
                    out["price"]     = float(h["Close"].iloc[-1])
                    out["prev_close"]= float(h["Close"].iloc[-2]) if len(h)>1 else out["price"]
            except: pass
        if out["price"] and out["prev_close"]:
            out["change"]     = round(out["price"]-out["prev_close"],4)
            out["change_pct"] = round(out["change"]/out["prev_close"]*100,2) if out["prev_close"] else 0.0
        out["market_cap"] = fmt_mcap(out["mcap_raw"], out["currency"])
        try:
            vol = safe_f(t.fast_info.three_month_average_volume or t.fast_info.last_volume)
            out["volume"] = f"{vol/1e5:.1f}L" if out["currency"]=="INR" and vol else (f"{vol/1e6:.2f}M" if vol else "—")
        except: pass
    except Exception as e:
        out["summary"] = f"[Error: {str(e)[:80]}]"
    return out


def _get_stmt(t, stmt_type):
    attrs = {"income":["income_stmt","financials"],"cashflow":["cashflow","cash_flow"],"balance":["balance_sheet","quarterly_balance_sheet"]}
    for attr in attrs.get(stmt_type,[]):
        try:
            df = getattr(t,attr,None)
            if df is not None and not df.empty: return df.sort_index(axis=1,ascending=False)
        except: continue
    return None


@st.cache_data(ttl=600, show_spinner=False)
def get_financials(ticker, currency):
    div = _div(currency)
    try:
        t = yf.Ticker(ticker)
        fin = _get_stmt(t,"income")
        cf  = _get_stmt(t,"cashflow")
        bs  = _get_stmt(t,"balance")
        if fin is None or fin.empty:
            return {"has_data":False,"error":"No income statement data.","hist":pd.DataFrame(),"base":{}}
        cols  = fin.columns.tolist()
        years = []
        for c in cols:
            try: years.append(c.strftime("FY%y") if hasattr(c,"strftime") else str(c)[:4])
            except: years.append(str(c)[:6])
        rev   = _extract_row(fin,"Total Revenue","TotalRevenue","Operating Revenue","Revenue")
        gp    = _extract_row(fin,"Gross Profit","GrossProfit")
        ebit  = _extract_row(fin,"Operating Income","OperatingIncome","EBIT","Operating Income Or Loss")
        ebitda= _extract_row(fin,"EBITDA","Normalized EBITDA","NormalizedEBITDA")
        ni    = _extract_row(fin,"Net Income","NetIncome","Net Income Common Stockholders","NetIncomeCommonStockholders")
        eps_d = _extract_row(fin,"Diluted EPS","DilutedEPS","Basic EPS","BasicEPS")
        da    = _extract_row(fin if cf is None else cf,"Reconciled Depreciation","ReconciledDepreciation","Depreciation And Amortization","DepreciationAndAmortization")
        if da.empty and cf is not None:
            da = _extract_row(cf,"Depreciation And Amortization","DepreciationAndAmortization","Depreciation")
        cfo   = _extract_row(cf,"Operating Cash Flow","OperatingCashFlow","Total Cash From Operating Activities") if cf is not None else pd.Series(dtype=float)
        capex = _extract_row(cf,"Capital Expenditure","CapitalExpenditures","CapEx","Purchases Of Property Plant And Equipment") if cf is not None else pd.Series(dtype=float)
        equity= _extract_row(bs,"Stockholders Equity","StockholdersEquity","Common Stock Equity","CommonStockEquity") if bs is not None else pd.Series(dtype=float)
        debt  = _extract_row(bs,"Total Debt","TotalDebt","Long Term Debt And Capital Lease Obligation") if bs is not None else pd.Series(dtype=float)
        cash  = _extract_row(bs,"Cash And Cash Equivalents","CashAndCashEquivalents","Cash Cash Equivalents And Short Term Investments") if bs is not None else pd.Series(dtype=float)
        def sv(s,i,d=1.0):
            try:
                if s is None or s.empty or i>=len(s): return 0.0
                v = float(s.iloc[i]); return 0.0 if (np.isnan(v) or np.isinf(v)) else round(v/d,4)
            except: return 0.0
        rows = []
        for i in range(min(len(cols),5)):
            r=sv(rev,i,div); e=sv(ebit,i,div); g=sv(gp,i,div); nd=sv(ni,i,div)
            da_v=sv(da,i,div); eb=sv(ebitda,i,div) or e+da_v
            cfo_v=sv(cfo,i,div); cap_v=abs(sv(capex,i,div)); eq_v=sv(equity,i,div)
            dbt_v=sv(debt,i,div); csh_v=sv(cash,i,div); eps_v=sv(eps_d,i,1.0)
            rows.append({
                "Year":years[i],"Revenue":round(r,2),"GrossProfit":round(g,2),
                "EBITDA":round(eb,2),"EBIT":round(e,2),"NI":round(nd,2),"EPS":round(eps_v,2),
                "OPM":round(e/r*100,2) if r else 0.0,"EBITDA_M":round(eb/r*100,2) if r else 0.0,
                "NPM":round(nd/r*100,2) if r else 0.0,"ROE":round(nd/eq_v*100,2) if eq_v else 0.0,
                "DA":round(da_v,2),"CFO":round(cfo_v,2),"Capex":round(cap_v,2),
                "FCFF":round(cfo_v-cap_v,2),"Equity":round(eq_v,2),
                "Debt":round(dbt_v,2),"Cash":round(csh_v,2),"NetDebt":round(dbt_v-csh_v,2),
            })
        hist_df = pd.DataFrame(rows)
        return {"has_data":True,"hist":hist_df,"base":rows[0] if rows else {},"n":len(rows)}
    except Exception as e:
        return {"has_data":False,"error":str(e),"hist":pd.DataFrame(),"base":{}}


@st.cache_data(ttl=300, show_spinner=False)
def get_price_history(ticker, period="1y"):
    try: return yf.Ticker(ticker).history(period=period)
    except: return pd.DataFrame()


@st.cache_data(ttl=700, show_spinner=False)
def get_peer_data(peer_tickers, currency):
    rows = []
    for tk in peer_tickers[:7]:
        try:
            info = yf.Ticker(tk).info or {}
            rows.append({
                "Company":    info.get("shortName",tk)[:26],
                "Ticker":     tk,
                "Mkt Cap":    fmt_mcap(safe_f(info.get("marketCap")), currency),
                "P/E":        round(safe_f(info.get("trailingPE")),1),
                "Fwd P/E":    round(safe_f(info.get("forwardPE")),1),
                "P/B":        round(safe_f(info.get("priceToBook")),2),
                "OPM%":       round(safe_f(info.get("operatingMargins"))*100,1),
                "ROE%":       round(safe_f(info.get("returnOnEquity"))*100,1),
                "Rev Growth%":round(safe_f(info.get("revenueGrowth"))*100,1),
                "Div Yield%": round(safe_f(info.get("dividendYield"))*100,2),
                "Beta":       round(safe_f(info.get("beta"),1.0),2),
            })
        except: pass
    return pd.DataFrame(rows)


@st.cache_data(ttl=600, show_spinner=False)
def get_news(name, ticker, n=20):
    queries = [name[:30], ticker.replace(".NS","").replace(".BO","")]
    articles = []
    seen = set()
    POS = ["growth","profit","revenue","beat","strong","upgrade","buy","gains","record","expands","positive","raises","outperforms","dividend","wins","launches"]
    NEG = ["loss","decline","fall","miss","downgrade","sell","weak","cuts","concerns","risks","drops","below","warns","penalty","fraud","probe","layoffs"]
    for q in queries:
        try:
            feed = feedparser.parse(f"https://news.google.com/rss/search?q={q.replace(' ','+')}+stock&hl=en&gl=US&ceid=US:en")
            for e in feed.entries[:n]:
                if e.title in seen: continue
                seen.add(e.title)
                title_l = e.title.lower()
                sent = "positive" if any(w in title_l for w in POS) else ("negative" if any(w in title_l for w in NEG) else "neutral")
                articles.append({"title":e.title,"link":getattr(e,"link","#"),"date":getattr(e,"published","")[:16],"sentiment":sent})
        except: pass
    return articles[:n]


def run_dcf(wacc, g_term, rev_cagr, ebit_margin, live_price, base, currency, shares_raw):
    if not base: return None
    rev0   = base.get("Revenue",0)
    if rev0==0: return None
    tax    = 0.25
    stc    = 2.0 if currency=="INR" else 2.5
    div    = _div(currency)
    shares_scaled = shares_raw/div if shares_raw else 1.0
    net_cash = base.get("Cash",0.0) - base.get("Debt",0.0)
    pv_total = 0.0; rev_prev=rev0; rows=[]; sym=_sym(currency); lbl=_lbl(currency)
    for i in range(1,6):
        rev_i   = rev_prev*(1+rev_cagr/100)
        ebit_i  = rev_i*ebit_margin/100
        nopat_i = ebit_i*(1-tax)
        reinv_i = (rev_i-rev_prev)/stc
        fcff_i  = nopat_i-reinv_i
        df_     = (1+wacc/100)**i
        pv_i    = fcff_i/df_
        pv_total+= pv_i
        rev_prev = rev_i
        rows.append({"Year":f"Y{i}E",f"Rev({lbl})":round(rev_i,1),f"EBIT({lbl})":round(ebit_i,1),
                     "EBIT%":f"{ebit_margin:.1f}%",f"FCFF({lbl})":round(fcff_i,1),
                     "DF":round(1/df_,4),f"PV({lbl})":round(pv_i,1)})
    tv_fcff = rows[-1][f"FCFF({lbl})"]; tv=tv_fcff*(1+g_term/100)/((wacc-g_term)/100)
    pv_tv = tv/(1+wacc/100)**5; ev=pv_total+pv_tv; eq_val=ev+net_cash
    ivps_native = (eq_val*div/shares_raw) if shares_raw else 0.0
    upside = round(((ivps_native/live_price)-1)*100,1) if live_price>0 else 0.0
    return {"rows":rows,"pv_explicit":round(pv_total,1),"pv_tv":round(pv_tv,1),
            "ev":round(ev,1),"eq_val":round(eq_val,1),"ivps":round(ivps_native,2),
            "upside":upside,"tv_pct":round(pv_tv/ev*100,1) if ev else 0.0,"sym":sym,"lbl":lbl}


def sensitivity_table(rev_cagr, ebit_margin, live_price, base, currency, shares_raw):
    if currency=="INR": wacc_v=[10.,10.5,11.,11.5,12.,12.5,13.]; g_v=[4.,4.5,5.,5.5,6.]
    else:               wacc_v=[7.,7.5,8.,8.5,9.,9.5,10.];       g_v=[1.5,2.,2.5,3.,3.5]
    data = {}
    for w in wacc_v:
        row=[]
        for g in g_v:
            r=run_dcf(w,g,rev_cagr,ebit_margin,live_price,base,currency,shares_raw)
            row.append(round(r["ivps"],1) if r else "—")
        data[f"WACC {w}%"]=row
    return pd.DataFrame(data, index=[f"g={g}%" for g in g_v])


# ══════════════════════════════════════════════════════════════════════════════
#  CHART HELPERS
# ══════════════════════════════════════════════════════════════════════════════
_LAYOUT = dict(
    plot_bgcolor=C['chart_bg'], paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C['text'], family="Inter, sans-serif", size=12),
    margin=dict(l=20, r=20, t=36, b=20),
    legend=dict(orientation="h", y=1.14, font=dict(size=11, color=C['text'])),
)

def _fig(**kw):
    fig = go.Figure(); fig.update_layout(**{**_LAYOUT, **kw}); return fig

def chart_candlestick(df, ticker, name, currency):
    sym = _sym(currency)
    _GRID = C['border']
    if df is None or df.empty:
        fig = _fig(height=420)
        fig.add_annotation(text="No price data available",xref="paper",yref="paper",x=.5,y=.5,showarrow=False,font=dict(color=C['muted'],size=14))
        return fig
    fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.03,row_heights=[.75,.25])
    fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],
        name=name,increasing_line_color=C['green'],decreasing_line_color=C['red']),row=1,col=1)
    for w,col,dash,lbl in [(20,C['amber'],"dot","20D MA"),(50,C['accent'],"dash","50D MA")]:
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"].rolling(w).mean(),name=lbl,
            line=dict(color=col,width=1.8,dash=dash)),row=1,col=1)
    fig.add_trace(go.Bar(x=df.index,y=df["Volume"],name="Volume",marker_color=C['accent'],opacity=.3),row=2,col=1)
    fig.update_layout(height=440,**_LAYOUT,xaxis_rangeslider_visible=False,
        yaxis=dict(tickprefix=sym,gridcolor=_GRID,tickfont=dict(size=11,color=C['muted']),linecolor=C['border2']),
        yaxis2=dict(gridcolor=_GRID,tickfont=dict(size=10,color=C['muted']),linecolor=C['border2']))
    return fig


def chart_revenue(hist_df, currency):
    if hist_df.empty: return go.Figure()
    sym=_sym(currency); lbl=_lbl(currency)
    _GRID = C['border']
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=hist_df["Year"],y=hist_df["Revenue"],name=f"Revenue ({lbl})",
        marker_color=C['accent'],opacity=.78),secondary_y=False)
    fig.add_trace(go.Scatter(x=hist_df["Year"],y=hist_df["EBIT"],name=f"EBIT ({lbl})",
        line=dict(color=C['amber'],width=2.5),mode="lines+markers",marker=dict(size=7,color=C['amber'])),secondary_y=True)
    fig.add_trace(go.Scatter(x=hist_df["Year"],y=hist_df["CFO"],name=f"CFO ({lbl})",
        line=dict(color=C['green'],width=2,dash="dot"),mode="lines+markers",marker=dict(size=6,color=C['green'])),secondary_y=True)
    fig.update_layout(height=320,**_LAYOUT,
        yaxis=dict(tickprefix=sym,gridcolor=_GRID,tickfont=dict(color=C['muted'])),
        yaxis2=dict(tickprefix=sym,gridcolor=_GRID,tickfont=dict(color=C['muted'])))
    return fig


def chart_margins(hist_df):
    if hist_df.empty: return go.Figure()
    _GRID = C['border']
    fig = go.Figure()
    for col,name,color in [("OPM","EBIT Margin",C['accent']),("EBITDA_M","EBITDA Margin",C['green']),("NPM","Net Margin",C['amber'])]:
        fig.add_trace(go.Scatter(x=hist_df["Year"],y=hist_df[col],name=name,
            line=dict(color=color,width=2.3),mode="lines+markers",marker=dict(size=7,color=color)))
    fig.update_layout(height=280,**_LAYOUT,
        yaxis=dict(ticksuffix="%",gridcolor=_GRID,tickfont=dict(color=C['muted'])))
    return fig


def chart_waterfall(result):
    sym=result["sym"]; lbl=result["lbl"]
    _GRID = C['border']
    labels=["PV FCFFs","PV Terminal","Enterprise Value","± Net Cash/Debt","Equity Value"]
    values=[result["pv_explicit"],result["pv_tv"],0,result["eq_val"]-result["ev"],0]
    measures=["relative","relative","total","relative","total"]
    fig=go.Figure(go.Waterfall(orientation="v",measure=measures,x=labels,y=values,
        connector=dict(line=dict(color=C['border2'],width=1.5)),
        increasing=dict(marker=dict(color=C['green'])),
        decreasing=dict(marker=dict(color=C['red'])),
        totals=dict(marker=dict(color=C['accent'])),
        textfont=dict(color=C['text'],size=11)))
    fig.update_layout(height=320,**_LAYOUT,
        yaxis=dict(tickprefix=sym,ticksuffix=f" {lbl}",gridcolor=_GRID,tickfont=dict(color=C['muted'])))
    return fig


def chart_monte_carlo(path_matrix, low_band, high_band, s0, T, currency):
    sym = _sym(currency)
    _GRID = C['border']
    t_axis = np.linspace(0, T, path_matrix.shape[0])
    fig = go.Figure()
    # Sample paths (draw up to 80)
    sample = min(80, path_matrix.shape[1])
    idx = np.random.choice(path_matrix.shape[1], sample, replace=False)
    # Decode accent2 hex to rgba
    r2,g2,b2 = int(C['accent2'][1:3],16), int(C['accent2'][3:5],16), int(C['accent2'][5:],16)
    for i in idx:
        fig.add_trace(go.Scatter(x=t_axis, y=path_matrix[:, i], mode="lines",
            line=dict(color=f"rgba({r2},{g2},{b2},0.06)", width=1),
            showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=t_axis, y=high_band, name="95th percentile",
        line=dict(color=C['green'], width=2.5, dash="dash"), fill=None))
    fig.add_trace(go.Scatter(x=t_axis, y=low_band, name="5th percentile",
        line=dict(color=C['red'], width=2.5, dash="dash"),
        fill="tonexty", fillcolor=f"rgba({r2},{g2},{b2},0.05)"))
    fig.add_hline(y=s0, line_color=C['amber'], line_width=2, line_dash="dot",
                  annotation_text="Current Price",
                  annotation_font_color=C['amber'],
                  annotation_position="bottom right")
    fig.update_layout(height=380, **_LAYOUT,
        yaxis=dict(tickprefix=sym, gridcolor=_GRID, tickfont=dict(color=C['muted'])),
        xaxis=dict(title=dict(text="Years", font=dict(color=C['muted'])), gridcolor=_GRID, tickfont=dict(color=C['muted'])))
    return fig


def chart_histogram(final_prices, s0, currency):
    sym = _sym(currency)
    _GRID = C['border']
    returns_pct = (final_prices - s0) / s0 * 100
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=returns_pct, nbinsx=80,
        marker_color=C['accent'], opacity=.72, name="Return distribution",
        marker_line=dict(color=C['accent2'], width=0.3)))
    fig.add_vline(x=0, line_color=C['red'], line_width=2, line_dash="dash",
                  annotation_text="Break-even",
                  annotation_font_color=C['red'],
                  annotation_position="top left")
    p95 = np.percentile(returns_pct, 5)
    fig.add_vline(x=p95, line_color=C['amber'], line_width=2, line_dash="dot",
                  annotation_text=f"VaR 95%: {p95:.1f}%",
                  annotation_font_color=C['amber_t'],
                  annotation_bgcolor=C['amber_bg'],
                  annotation_position="top right")
    fig.update_layout(height=300, **_LAYOUT,
        xaxis=dict(title=dict(text="Return (%)", font=dict(color=C['muted'])),
                   gridcolor=_GRID, tickfont=dict(color=C['muted'])),
        yaxis=dict(title=dict(text="Frequency", font=dict(color=C['muted'])),
                   gridcolor=_GRID, tickfont=dict(color=C['muted'])))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="padding:1.2rem 0 1rem;">
      <div class="brand" style="font-size:1.08rem;color:{C['text']};">
        🏛️ Equity Research<span class="brand-dot" style="color:{C['accent']};">.</span>
      </div>
      <div style="font-size:0.6rem;color:{C['muted']};letter-spacing:2px;margin-top:4px;font-weight:600;">UNIFIED TERMINAL  v4.0</div>
      <div style="width:32px;height:2px;background:{C['accent']};border-radius:1px;margin-top:8px;"></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    market      = st.radio("Market", ["🇺🇸  United States", "🇮🇳  India (NSE/BSE)"])
    india_mode  = market.startswith("🇮🇳")
    all_cos     = INDIA_COMPANIES if india_mode else US_COMPANIES
    sorted_names = sorted(all_cos.keys())

    # Default: Qualcomm for US, Divi's for India
    if india_mode:
        default_idx = sorted_names.index("Divi's Laboratories") if "Divi's Laboratories" in sorted_names else 0
    else:
        default_idx = sorted_names.index("Qualcomm") if "Qualcomm" in sorted_names else 0

    sel_name   = st.selectbox("Company", sorted_names, index=default_idx)
    sel_ticker = all_cos[sel_name]

    custom = st.text_input("Custom ticker", placeholder="QCOM / RELIANCE.NS",value="").strip().upper()
    if custom:
        if india_mode and "." not in custom: custom += ".NS"
        TICKER = custom; COMPANY_NAME = custom
    else:
        TICKER = sel_ticker; COMPANY_NAME = sel_name

    st.markdown(f"""<div style="font-size:.65rem;color:{C['muted']};margin-top:-4px;margin-bottom:.5rem;">
    Ticker: <b style="color:{C['text']};">{TICKER}</b></div>""", unsafe_allow_html=True)

    st.divider()

    PAGE = st.radio("Navigation", [
        "🏠  Overview",
        "📊  Financial History",
        "🔮  DCF Valuation",
        "🎲  Monte Carlo Sim",
        "⚠️  Risk Metrics",
        "🏗️  Capital Structure",
        "🔍  Peer Analysis",
        "♟️  Strategy",
        "📰  Live News",
        "🔬  Data Audit",
    ], label_visibility="collapsed")

    st.divider()
    st.markdown(f"""<div style="font-size:.62rem;color:{C['muted']};line-height:1.9;">
    <b style="color:{C['text']};">Data Sources</b><br>
    · Yahoo Finance (yfinance)<br>
    · Google News RSS<br>
    · Damodaran Framework (NYU)<br>
    {'· Hardcoded Fundamentals' if _HAS_ADVANCED else ''}<br><br>
    <b style="color:{C['text']};">Scale</b><br>
    {'₹ INR → Crores' if india_mode else '$ USD → Billions'}<br><br>
    <span style="color:{C['subtle']};">{datetime.now().strftime('%d %b %Y  %H:%M')}</span>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner(f"Loading {COMPANY_NAME} ({TICKER}) …"):
    live = get_live_price(TICKER)

CURRENCY     = live["currency"]
SYM          = _sym(CURRENCY)
LBL          = _lbl(CURRENCY)
DIV          = _div(CURRENCY)
DISPLAY_NAME = live.get("long_name") or COMPANY_NAME

with st.spinner("Fetching financials …"):
    fin_data = get_financials(TICKER, CURRENCY)

hist_df = fin_data.get("hist", pd.DataFrame())
base    = fin_data.get("base", {})


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Compact KPI card
# ══════════════════════════════════════════════════════════════════════════════
def kpi_card(label, value, sub="", color=None):
    color_style = f"color:{color};" if color else ""
    return f"""<div class="kpi">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value" style="{color_style}">{value}</div>
      {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
    </div>"""


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if PAGE == "🏠  Overview":
    flag = "🇮🇳" if CURRENCY=="INR" else "🇺🇸"
    chg_col = C['green'] if live["change"]>=0 else C['red']
    chg_arr = "▲" if live["change"]>=0 else "▼"

    # ── Header & Price Hero ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class="price-hero">
      <div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:1rem;">
        <div>
          <div style="font-size:0.75rem; color:{C['muted']}; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px;">
            {flag} {live['sector']} · {TICKER}
          </div>
          <div class="company-name">{DISPLAY_NAME}</div>
          <div class="company-meta">{live['industry']} &nbsp;·&nbsp; {live['country']} &nbsp;·&nbsp; {CURRENCY}</div>
        </div>
        <div style="text-align:right;">
          <div class="price-main">{fmt_price(live['price'], CURRENCY)}</div>
          <div class="{'price-change-up' if live['change']>=0 else 'price-change-dn'}">
            {chg_arr} {SYM}{abs(live['change']):.2f} &nbsp; ({abs(live['change_pct']):.2f}%)
          </div>
          <div style="font-size:0.7rem; color:{C['muted']}; margin-top:4px;">vs prev close {SYM}{live['prev_close']:,.2f}</div>
        </div>
      </div>

      <div class="kpi-grid" style="margin-top:1.4rem;">
        {kpi_card("Market Cap", live['market_cap'])}
        {kpi_card("52W High",   f"{SYM}{live['52w_high']:,.2f}")}
        {kpi_card("52W Low",    f"{SYM}{live['52w_low']:,.2f}")}
        {kpi_card("Volume",     live['volume'])}
        {kpi_card("Trailing P/E", f"{live['pe']:.1f}x" if live['pe'] else "—", "earnings multiple")}
        {kpi_card("Forward P/E",  f"{live['fwd_pe']:.1f}x" if live['fwd_pe'] else "—", "consensus")}
        {kpi_card("Price/Book",   f"{live['pb']:.1f}x"  if live['pb'] else "—")}
        {kpi_card("Div Yield",    f"{live['div_yield']:.2f}%" if live['div_yield'] else "—")}
        {kpi_card("Beta",         f"{live['beta']:.2f}", "systematic risk")}
        {kpi_card("Employees",    f"{live['employees']:,}" if live['employees'] else "—")}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Chart + Snapshot ─────────────────────────────────────────────────────
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="sec-head">Price Chart — Technical Analysis</div>', unsafe_allow_html=True)
        period_sel = st.select_slider("Period", ["1mo","3mo","6mo","1y","2y","5y"], value="1y", label_visibility="collapsed")
        with st.spinner("Loading …"):
            ph = get_price_history(TICKER, period_sel)
        st.plotly_chart(chart_candlestick(ph, TICKER, DISPLAY_NAME, CURRENCY), use_container_width=True)

    with c2:
        st.markdown('<div class="sec-head">Latest Annual</div>', unsafe_allow_html=True)
        if base:
            r=base.get("Revenue",0); e=base.get("EBIT",0); n=base.get("NI",0)
            nd=base.get("NetDebt",0)
            nd_l = "Net Cash" if nd<0 else "Net Debt"
            items = [
                ("Revenue",  f"{SYM}{r:,.1f} {LBL}"),
                ("EBIT",     f"{SYM}{e:,.1f} {LBL}"),
                ("Net Income",f"{SYM}{n:,.1f} {LBL}"),
                ("EBIT Margin",f"{base.get('OPM',0):.1f}%"),
                ("EBITDA Margin",f"{base.get('EBITDA_M',0):.1f}%"),
                ("ROE",      f"{base.get('ROE',0):.1f}%"),
                ("CFO",      f"{SYM}{base.get('CFO',0):,.1f} {LBL}"),
                (nd_l,       f"{SYM}{abs(nd):,.1f} {LBL}"),
            ]
            rows_html = "".join(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {C["border"]};font-size:.82rem;"><span style="color:{C["muted"]}">{k}</span><b>{v}</b></div>' for k,v in items)
            st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)
        else:
            st.info("Financials loading…")

        if live.get("summary"):
            with st.expander("About the company"):
                st.write(live["summary"][:600]+"…" if len(live["summary"])>600 else live["summary"])

    # ── Damodaran Profile ─────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Damodaran Investment Profile</div>', unsafe_allow_html=True)
    pe=live.get("pe",0); pb=live.get("pb",0)
    opm=base.get("OPM",0) if base else 0; roe_v=base.get("ROE",0) if base else 0; nd_v=base.get("NetDebt",0) if base else 0

    t1,t2,t3 = st.columns(3)
    with t1:
        gtype = "High Growth" if pe>35 else ("Moderate Growth" if pe>18 else "Value / Mature")
        gclass= "chip-r" if pe>35 else ("chip-a" if pe>18 else "chip-g")
        g_desc= ("Premium valuation — market expects sustained above-average earnings growth." if pe>35
                 else "Moderate multiple — balanced growth expectations." if pe>18
                 else "Value-oriented — market prices in stable / slow growth.")
        st.markdown(f"""<div class="card card-l">
          <div style="font-size:.62rem;color:{C['muted']};text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;font-weight:700;">GROWTH CLASSIFICATION</div>
          <span class="chip {gclass}">{gtype}</span>
          <div style="font-size:.84rem;color:{C['sb_text']};margin-top:10px;line-height:1.75;">
            Trailing P/E <b style="color:{C['text']}">{pe:.1f}x</b> &nbsp;·&nbsp; Fwd P/E <b style="color:{C['text']}">{live.get('fwd_pe',0):.1f}x</b><br>
            <span style="color:{C['muted']};font-size:.8rem;">{g_desc}</span>
          </div></div>""", unsafe_allow_html=True)

    with t2:
        qtype = "Quality Compounder" if (opm>20 and roe_v>18) else ("Cyclical / Commodity" if opm<10 else "Average Quality")
        qclass= "chip-g" if (opm>20 and roe_v>18) else ("chip-r" if opm<10 else "chip-a")
        q_desc= ("High-margin compounding business with durable returns on equity." if (opm>20 and roe_v>18)
                 else "Thin margins — business subject to cyclical demand fluctuations." if opm<10
                 else "Decent margins — operating in a competitive market.")
        st.markdown(f"""<div class="card card-l">
          <div style="font-size:.62rem;color:{C['muted']};text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;font-weight:700;">QUALITY PROFILE</div>
          <span class="chip {qclass}">{qtype}</span>
          <div style="font-size:.84rem;color:{C['sb_text']};margin-top:10px;line-height:1.75;">
            EBIT margin <b style="color:{C['text']}">{opm:.1f}%</b> &nbsp;·&nbsp; ROE <b style="color:{C['text']}">{roe_v:.1f}%</b><br>
            <span style="color:{C['muted']};font-size:.8rem;">{q_desc}</span>
          </div></div>""", unsafe_allow_html=True)

    with t3:
        lev_l = "Net Cash" if nd_v<0 else ("Moderate Leverage" if base and nd_v < base.get("Revenue",1)*.5 else "High Leverage") if base else "—"
        lclass= "chip-g" if nd_v<0 else ("chip-a" if base and nd_v < base.get("Revenue",1)*.5 else "chip-r")
        l_desc= ("Strong balance sheet — net cash position provides strategic flexibility." if nd_v<0
                 else "Manageable leverage relative to earnings power." if base and nd_v<base.get("EBIT",1)*3
                 else "Elevated debt level — monitor interest coverage ratios.")
        st.markdown(f"""<div class="card card-l">
          <div style="font-size:.62rem;color:{C['muted']};text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;font-weight:700;">BALANCE SHEET</div>
          <span class="chip {lclass}">{lev_l}</span>
          <div style="font-size:.84rem;color:{C['sb_text']};margin-top:10px;line-height:1.75;">
            P/B <b style="color:{C['text']}">{pb:.1f}x</b> &nbsp;·&nbsp; Net {'Cash' if nd_v<0 else 'Debt'} <b style="color:{C['text']}">{SYM}{abs(nd_v):,.1f} {LBL}</b><br>
            <span style="color:{C['muted']};font-size:.8rem;">{l_desc}</span>
          </div></div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — FINANCIAL HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "📊  Financial History":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Financial History ({LBL})</div>', unsafe_allow_html=True)

    if not fin_data.get("has_data"):
        st.error(f"Financials unavailable: {fin_data.get('error','Unknown error')}")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📈 P&L Trend", "📐 Margins", "💰 Cash Flow", "🏦 Balance Sheet"])

        with tab1:
            st.markdown('<div class="sec-head">Revenue, EBIT & Cash Flow</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_revenue(hist_df, CURRENCY), use_container_width=True)
            disp = hist_df[["Year","Revenue","EBITDA","EBIT","NI","EPS"]].copy()
            disp.columns = ["Year",f"Revenue ({LBL})",f"EBITDA ({LBL})",f"EBIT ({LBL})",f"Net Income ({LBL})","EPS"]
            st.dataframe(disp, use_container_width=True, hide_index=True)

        with tab2:
            st.markdown('<div class="sec-head">Profitability Margins (%)</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_margins(hist_df), use_container_width=True)
            m_df = hist_df[["Year","OPM","EBITDA_M","NPM","ROE"]].copy()
            m_df.columns = ["Year","EBIT Margin%","EBITDA Margin%","Net Margin%","ROE%"]
            st.dataframe(m_df, use_container_width=True, hide_index=True)

        with tab3:
            st.markdown('<div class="sec-head">Cash Flow Statement</div>', unsafe_allow_html=True)
            cf_df = hist_df[["Year","CFO","Capex","FCFF","DA"]].copy()
            cf_df.columns = ["Year",f"Oper. CF ({LBL})",f"CapEx ({LBL})",f"FCFF ({LBL})",f"D&A ({LBL})"]
            fig_cf = go.Figure()
            for col, color in [(f"Oper. CF ({LBL})",C['green']),(f"FCFF ({LBL})",C['accent']),(f"CapEx ({LBL})",C['red'])]:
                fig_cf.add_trace(go.Bar(x=cf_df["Year"],y=cf_df[col],name=col,marker_color=color,opacity=.8))
            fig_cf.update_layout(barmode="group",height=300,**_LAYOUT,yaxis=dict(tickprefix=SYM,gridcolor=C['border']))
            st.plotly_chart(fig_cf, use_container_width=True)
            st.dataframe(cf_df, use_container_width=True, hide_index=True)

        with tab4:
            st.markdown('<div class="sec-head">Balance Sheet</div>', unsafe_allow_html=True)
            bs_df = hist_df[["Year","Equity","Debt","Cash","NetDebt"]].copy()
            bs_df.columns = ["Year",f"Equity ({LBL})",f"Total Debt ({LBL})",f"Cash ({LBL})",f"Net Debt ({LBL})"]
            fig_bs = go.Figure()
            for col, color in [(f"Equity ({LBL})",C['accent']),(f"Total Debt ({LBL})",C['red']),(f"Cash ({LBL})",C['green'])]:
                fig_bs.add_trace(go.Bar(x=bs_df["Year"],y=bs_df[col],name=col,marker_color=color,opacity=.8))
            fig_bs.update_layout(barmode="group",height=300,**_LAYOUT,yaxis=dict(tickprefix=SYM,gridcolor=C['border']))
            st.plotly_chart(fig_bs, use_container_width=True)
            st.dataframe(bs_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — DCF VALUATION  (full Damodaran framework)
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "🔮  DCF Valuation":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Damodaran Intrinsic Value Framework</div>', unsafe_allow_html=True)

    skip_cols = ("Year","Phase","Growth","Growth Rate","Expected Growth","Cost of Equity","WACC")

    # ══════════════════════════════════════════════════════════════════
    #  DAMODARAN MODEL ENGINE  (advanced path)
    # ══════════════════════════════════════════════════════════════════
    if _HAS_ADVANCED:
        dcf_val  = None
        dcf_err  = None
        lp       = live["price"]
        with st.spinner("Running Damodaran model selector + DCF engine …"):
            try:
                dcf_val = run_valuation(TICKER)
            except Exception as ex:
                dcf_err = str(ex)

        if dcf_err:
            st.warning(f"⚠️ Damodaran engine unavailable for {TICKER}: {dcf_err}")
        else:
            mc_sel   = dcf_val.get("model_selection", {})
            vd       = dcf_val.get("valuation_detail", {})
            fd_dcf   = dcf_val.get("fundamentals", {})
            comp_dcf = dcf_val.get("computed", {})
            intrinsic_adv = dcf_val.get("intrinsic_value_per_share", 0)
            cur_adv  = "₹" if CURRENCY == "INR" else "$"
            unit_adv = fd_dcf.get("unit","Cr")

            # ── SIGNAL BANNER ────────────────────────────────────────
            if lp and intrinsic_adv > 0:
                mos = (intrinsic_adv - lp) / lp
                if mos > .20:   sb,sbd,stc,svt = C['green_bg'],C['green'],C['green_t'],"🟢 UNDERVALUED — BUY"
                elif mos > -.10: sb,sbd,stc,svt = C['amber_bg'],C['amber'],C['amber_t'],"🟡 FAIRLY VALUED — HOLD"
                else:            sb,sbd,stc,svt = C['red_bg'],  C['red'],  C['red_t'],  "🔴 OVERVALUED — AVOID"
                sub_dcf = f"Market {cur_adv}{lp:,.2f} · DCF {cur_adv}{intrinsic_adv:,.2f} · Margin of Safety {mos:+.1%}"
            else:
                sb,sbd,stc,svt = C['amber_bg'],C['amber'],C['amber_t'],"⚠️ DCF RESULT"
                sub_dcf = "Market price or intrinsic value unavailable"
            st.markdown(f"""<div style="background:{sb};border:1.5px solid {sbd};border-radius:14px;padding:22px 20px;
              text-align:center;margin:.5rem 0 1.2rem;box-shadow:0 2px 8px rgba(0,0,0,.05);">
              <div style="font-size:1.8rem;font-weight:800;color:{stc};letter-spacing:.5px;">{svt}</div>
              <div style="font-size:.85rem;color:{stc};opacity:.85;margin-top:6px;font-weight:500;">{sub_dcf}</div>
            </div>""", unsafe_allow_html=True)

            # ── STEP 1: MODEL SELECTION Q&A ──────────────────────────
            st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:20px 0 8px;">'
                        f'<span class="sb sb-bronze">STEP 1</span>'
                        f'<span style="font-size:1.15rem;font-weight:700;color:{C["text"]};">Choosing the Right Model</span></div>',
                        unsafe_allow_html=True)
            st.caption("Replicates Damodaran's model1.xls decision tree — answered with live company data")

            with st.expander("📝 Q&A Model Inputs", expanded=True):
                cs = ""
                for item in mc_sel.get("qa_inputs", []):
                    s = item.get("section", "")
                    if s and s != cs:
                        st.markdown(f"<p style='color:{C['primary']};font-weight:700;margin:14px 0 5px;'>━━ {s} ━━</p>", unsafe_allow_html=True)
                        cs = s
                    if "formula" in item:
                        st.markdown(f"**{item['question']}**")
                        st.code(item["formula"], language="text")
                        st.markdown(f"<p style='color:{C['primary']};font-weight:600;'>= {item['answer']}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"<p style='margin:3px 0;'><span style='color:{C['muted']};'>{item['question']}</span>"
                            f" → <code style='color:{C['text']};background:{C['border']};padding:2px 6px;border-radius:4px;'>{item['answer']}</code></p>",
                            unsafe_allow_html=True)
                    if "note" in item:
                        st.caption(f"ℹ️ {item['note']}")

            with st.expander("🧠 Decision Trail", expanded=True):
                for i, step in enumerate(mc_sel.get("decision_trail", []), 1):
                    st.markdown(f"<p style='margin:5px 0;'><span style='color:{C['primary']};font-weight:700;'>{i}.</span> "
                                f"<span style='color:{C['text']};'>{step}</span></p>", unsafe_allow_html=True)

            if mc_sel.get("detailed_rationale"):
                with st.expander("📚 Detailed Academic Rationale", expanded=True):
                    for p in mc_sel["detailed_rationale"]:
                        st.markdown(f'<div class="rat">{p}</div>', unsafe_allow_html=True)

            if mc_sel.get("rejected_alternatives"):
                with st.expander("🚫 Why Other Models Were Rejected"):
                    for r in mc_sel["rejected_alternatives"]:
                        st.markdown(f'<div class="rej">❌ {r}</div>', unsafe_allow_html=True)

            if mc_sel.get("key_assumptions"):
                with st.expander("📐 Key Assumptions"):
                    ka = mc_sel["key_assumptions"]
                    if isinstance(ka, dict):
                        cols_ka = st.columns(2)
                        for i, (k, v) in enumerate(ka.items()):
                            with cols_ka[i % 2]:
                                st.markdown(f'<div class="arow"><span style="color:{C["muted"]};font-weight:500;">{k}</span>'
                                            f'<span style="color:{C["text"]};font-weight:700;">{v}</span></div>', unsafe_allow_html=True)
                    else:
                        for item in ka:
                            st.markdown(f'<div class="rat">📌 {item}</div>', unsafe_allow_html=True)

            # Model summary card
            st.markdown(f"""<div class="card" style="border-color:{C['primary']};margin-top:10px;">
              <p style="color:{C['primary']};font-weight:700;font-size:.88rem;margin:0 0 10px;letter-spacing:1px;">📐 MODEL SELECTOR OUTPUT</p>
              <table style="width:100%;font-size:.93rem;border:none;">
                <tr><td style="color:{C['muted']};padding:6px 0;width:40%;">Type</td><td style="font-weight:600;color:{C['text']};">{mc_sel.get('model_type','—')}</td></tr>
                <tr><td style="color:{C['muted']};padding:6px 0;">Earnings</td><td style="font-weight:600;color:{C['text']};">{mc_sel.get('earnings_level','—')}</td></tr>
                <tr><td style="color:{C['muted']};padding:6px 0;">Cashflows</td><td style="font-weight:600;color:{C['text']};">{mc_sel.get('cashflow_type','—')}</td></tr>
                <tr><td style="color:{C['muted']};padding:6px 0;">Growth</td><td style="font-weight:600;color:{C['text']};">{mc_sel.get('growth_pattern','—')}</td></tr>
                <tr style="background:{C['border']};">
                  <td style="color:{C['text']};font-weight:700;padding:8px 6px;">✅ Selected</td>
                  <td style="color:{C['primary']};font-weight:800;font-size:1rem;padding:8px 6px;">
                    {mc_sel.get('model_description','—')}
                    <code style="font-size:.75rem;background:{C['surface']};padding:2px 6px;border-radius:4px;margin-left:6px;color:{C['text']};">{mc_sel.get('model_code','—')}.xls</code>
                  </td>
                </tr>
              </table>
            </div>""", unsafe_allow_html=True)
            st.markdown("---")

            # ── STEP 2: ANNUAL REPORT DATA ────────────────────────────
            st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px;">'
                        f'<span class="sb sb-bronze">STEP 2</span>'
                        f'<span style="font-size:1.15rem;font-weight:700;color:{C["text"]};">Annual Report Data</span></div>',
                        unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="card" style="border-left:4px solid {C["primary"]};">'
                            f'<p style="color:{C["primary"]};font-weight:700;font-size:.85rem;margin-bottom:8px;">📄 INCOME STATEMENT</p>', unsafe_allow_html=True)
                for lbl_s, k in [("Revenue","revenue"),("EBIT","ebit"),("Net Income","net_income")]:
                    st.write(f"{lbl_s}: **{cur_adv}{fd_dcf.get(k,0):,.0f} {unit_adv}**")
                st.write(f"EPS: **{cur_adv}{comp_dcf.get('EPS',0):,.2f}**")
                st.write(f"Tax Rate: **{fd_dcf.get('tax_rate',0):.0%}**")
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="card" style="border-left:4px solid {C["secondary"]};">'
                            f'<p style="color:{C["secondary"]};font-weight:700;font-size:.85rem;margin-bottom:8px;">💰 CASH FLOW</p>', unsafe_allow_html=True)
                for lbl_s, k in [("Depreciation","depreciation"),("CapEx","capex"),("ΔWC","delta_wc"),("Dividends","dividends_total")]:
                    st.write(f"{lbl_s}: **{cur_adv}{fd_dcf.get(k,0):,.0f} {unit_adv}**")
                st.markdown(f"<p style='color:{C['secondary']};font-weight:700;font-size:.85rem;'>"
                            f"FCFE: {cur_adv}{comp_dcf.get('FCFE_total',0):,.0f} {unit_adv}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:{C['secondary']};font-weight:700;font-size:.85rem;'>"
                            f"FCFF: {cur_adv}{comp_dcf.get('FCFF_total',0):,.0f} {unit_adv}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="card" style="border-left:4px solid {C["green"]};">'
                            f'<p style="color:{C["green"]};font-weight:700;font-size:.85rem;margin-bottom:8px;">🏗️ BALANCE SHEET & RATES</p>', unsafe_allow_html=True)
                st.write(f"Total Debt: **{cur_adv}{fd_dcf.get('total_debt',0):,.0f}** | Cash: **{cur_adv}{fd_dcf.get('cash',0):,.0f} {unit_adv}**")
                st.write(f"D/E: **{fd_dcf.get('debt_ratio',0):.1%}** | Beta: **{fd_dcf.get('beta',1):.2f}**")
                st.write(f"Ke: **{fd_dcf.get('cost_of_equity',0):.1%}** | WACC: **{fd_dcf.get('wacc',0):.1%}**")
                st.write(f"Rf: **{fd_dcf.get('risk_free_rate',0):.1%}** | ERP: **{fd_dcf.get('erp',0):.1%}**")
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

            # ── STEP 3: YEAR-BY-YEAR DCF TABLE ───────────────────────
            st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px;">'
                        f'<span class="sb sb-bronze">STEP 3</span>'
                        f'<span style="font-size:1.15rem;font-weight:700;color:{C["text"]};">'
                        f'{vd.get("model","DCF")} — Year-by-Year Cash Flows</span></div>', unsafe_allow_html=True)
            if vd.get("year_by_year"):
                df_yby = pd.DataFrame(vd["year_by_year"])
                for col_yby in df_yby.columns:
                    if col_yby in skip_cols: continue
                    if df_yby[col_yby].dtype in [np.float64, np.int64, float, int]:
                        df_yby[col_yby] = df_yby[col_yby].apply(
                            lambda x: f"{cur_adv}{x:,.2f}" if abs(x) >= 1 else f"{x:.6f}")
                st.dataframe(df_yby, use_container_width=True, hide_index=True)
            if vd.get("formula"):
                st.code(vd["formula"], language="text")
            if vd.get("summary"):
                with st.expander("📊 Valuation Summary"):
                    rows_sum = [{"Item":k,"Value":f"{v:.2%}" if isinstance(v,float) and abs(v)<1 and v!=0
                                 else f"{cur_adv}{v:,.2f}" if isinstance(v,float) else str(v)}
                                for k, v in vd["summary"].items()]
                    st.table(pd.DataFrame(rows_sum))

            # Intrinsic Value Hero
            if intrinsic_adv > 0:
                mos2 = (intrinsic_adv - lp) / lp if lp else 0
                iv_clr = C['green'] if mos2 > 0 else C['red']
                st.markdown(f"""<div class="iv-hero">
                  <p style="color:{C['muted']};font-size:.85rem;margin:0;font-weight:500;letter-spacing:1px;">INTRINSIC VALUE PER SHARE</p>
                  <h1 style="margin:8px 0;font-size:2.6rem;font-weight:900;color:{C['text']};">{cur_adv}{intrinsic_adv:,.2f}</h1>
                  <p style="color:{C['muted']};margin:0;font-size:.83rem;">Model: {mc_sel.get("model_description","—")} ·
                    <code style="background:{C['border']};color:{C['text']};padding:1px 5px;border-radius:3px;">{mc_sel.get("model_code","—")}.xls</code>
                  </p>
                  <p style="color:{iv_clr};font-weight:700;font-size:1rem;margin:6px 0 0;">
                    Margin of Safety: {mos2:+.1%} vs market {cur_adv}{lp:,.2f}
                  </p>
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("⚠️ Intrinsic value ≤ 0 — check input assumptions.")
            st.markdown("---")

            # ── STEP 4: SENSITIVITY HEATMAP ──────────────────────────
            st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px;">'
                        f'<span class="sb sb-terra">STEP 4</span>'
                        f'<span style="font-size:1.15rem;font-weight:700;color:{C["text"]};">DCF Sensitivity — WACC × Terminal Growth</span></div>',
                        unsafe_allow_html=True)
            st.caption("How intrinsic value changes as WACC and terminal growth rate vary. Your base case is highlighted.")
            try:
                from valuation_models import (
                    fcff_stable, fcff_two_stage, fcff_three_stage,
                    fcfe_stable, fcfe_two_stage, fcfe_three_stage,
                    ddm_stable,  ddm_two_stage,  ddm_three_stage,
                    compute_fcfe, compute_fcff,
                )
                code_s   = mc_sel.get("model_code","fcff2st")
                base_wacc = fd_dcf.get("wacc", 0.10)
                base_sg   = fd_dcf.get("stable_growth", 0.03)
                wacc_range = [round(base_wacc + d, 3) for d in [-0.04,-0.03,-0.02,-0.01,0,0.01,0.02,0.03,0.04]]
                sg_range   = [round(base_sg   + d, 3) for d in [-0.02,-0.01,0,0.01,0.02]]

                def _sens_val(w, g):
                    try:
                        sh   = fd_dcf["shares_outstanding"]
                        hg   = fd_dcf["firm_growth_rate"]
                        fcff_t = compute_fcff(fd_dcf["ebit"], fd_dcf["tax_rate"], fd_dcf["depreciation"], fd_dcf["capex"], fd_dcf["delta_wc"])
                        fcfe_t = compute_fcfe(fd_dcf["net_income"], fd_dcf["depreciation"], fd_dcf["capex"], fd_dcf["delta_wc"], fd_dcf["debt_ratio"])
                        fcfe_ps = fcfe_t / sh if sh > 0 else 0
                        dps_s  = fd_dcf.get("dividends_total", 0) / sh if sh > 0 else 0
                        ke_s   = fd_dcf.get("cost_of_equity", 0.12)
                        if code_s == "fcffst":  r = fcff_stable(fcff_t, w, g, fd_dcf["total_debt"], fd_dcf["cash"], sh)
                        elif code_s == "fcff2st": r = fcff_two_stage(fcff_t, w, w*.95, hg, g, 7, fd_dcf["total_debt"], fd_dcf["cash"], sh)
                        elif code_s == "fcff3st": r = fcff_three_stage(fcff_t, w, w*.95, hg, g, 5, 5, fd_dcf["total_debt"], fd_dcf["cash"], sh)
                        elif code_s == "fcfest":  r = fcfe_stable(fcfe_ps, ke_s, g)
                        elif code_s == "fcfe2st": r = fcfe_two_stage(fcfe_ps, ke_s, hg, g, 7)
                        elif code_s == "fcfe3st": r = fcfe_three_stage(fcfe_ps, ke_s, hg, g, 5, 5)
                        elif code_s == "ddmst":   r = ddm_stable(dps_s, ke_s, g)
                        elif code_s == "ddm2st":  r = ddm_two_stage(dps_s, ke_s, hg, g, 7)
                        elif code_s == "ddm3st":  r = ddm_three_stage(dps_s, ke_s, hg, g, 5, 5)
                        else: r = fcff_two_stage(fcff_t, w, w*.95, hg, g, 7, fd_dcf["total_debt"], fd_dcf["cash"], sh)
                        iv_s = r.get("intrinsic_value_per_share", r.get("intrinsic_value", 0))
                        return max(0, iv_s)
                    except: return 0

                sens_data = {}
                for w in wacc_range:
                    row_s = {}
                    for g in sg_range:
                        row_s[f"g={g:.1%}"] = _sens_val(w, g)
                    sens_data[f"WACC={w:.1%}"] = row_s
                df_sens = pd.DataFrame(sens_data).T

                fig_sens = go.Figure(data=go.Heatmap(
                    z=df_sens.values,
                    x=df_sens.columns.tolist(),
                    y=df_sens.index.tolist(),
                    colorscale=[[0, C['red_bg']], [0.3, C['amber_bg']], [0.5, C['green_bg']], [0.7, C['border']], [1, C['primary']]],
                    text=[[f"{cur_adv}{v:,.0f}" for v in row_r] for row_r in df_sens.values],
                    texttemplate="%{text}",
                    textfont={"size": 11, "color": C['text']},
                    hovertemplate="WACC: %{y}<br>Terminal g: %{x}<br>Value: %{text}<extra></extra>",
                    showscale=True,
                    colorbar=dict(title="Value", tickformat=",.0f", thickness=15),
                ))
                base_wi = [i for i, r in enumerate(df_sens.index) if abs(float(r.split("=")[1].rstrip("%"))/100 - base_wacc) < 0.0015]
                base_gi = [i for i, col_ in enumerate(df_sens.columns) if abs(float(col_.split("=")[1].rstrip("%"))/100 - base_sg) < 0.0015]
                if base_wi and base_gi:
                    fig_sens.add_shape(type="rect", xref="x", yref="y",
                        x0=base_gi[0]-.5, x1=base_gi[0]+.5,
                        y0=base_wi[0]-.5, y1=base_wi[0]+.5,
                        line=dict(color=C['text'], width=3))
                    fig_sens.add_annotation(xref="x", yref="y", x=base_gi[0], y=base_wi[0],
                        text="BASE", font=dict(color=C['text'], size=9), showarrow=False, yshift=16)
                fig_sens.update_layout(
                    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor=C['chart_bg'], font=dict(family="Inter,sans-serif", color=C['text']),
                    margin=dict(l=40,r=40,t=50,b=40),
                    title=f"Intrinsic Value Sensitivity — {DISPLAY_NAME}",
                    height=380, xaxis_title="Terminal Growth Rate", yaxis_title="WACC"
                )
                st.plotly_chart(fig_sens, use_container_width=True)

                # ── STEP 5: TORNADO CHART ─────────────────────────────
                st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:10px 0 14px;">'
                            f'<span class="sb sb-plum">STEP 5</span>'
                            f'<span style="font-size:1.15rem;font-weight:700;color:{C["text"]};">Key Value Drivers — Tornado Chart</span></div>',
                            unsafe_allow_html=True)
                base_iv = intrinsic_adv if intrinsic_adv > 0 else 1
                params_t = {
                    "WACC −2pp":   (base_wacc-.02, base_sg),
                    "WACC +2pp":   (base_wacc+.02, base_sg),
                    "Growth −1pp": (base_wacc, base_sg-.01),
                    "Growth +1pp": (base_wacc, base_sg+.01),
                    "Growth −2pp": (base_wacc, base_sg-.02),
                    "Growth +2pp": (base_wacc, base_sg+.02),
                }
                drivers = []
                for dname, (w, g) in params_t.items():
                    iv_d = _sens_val(w, g)
                    drivers.append({
                        "Driver": dname,
                        "Impact": iv_d - base_iv,
                        "Impact%": (iv_d - base_iv) / base_iv if base_iv else 0,
                        "New Value": iv_d
                    })
                df_torn = pd.DataFrame(drivers).sort_values("Impact")
                fig_torn = go.Figure()
                fig_torn.add_trace(go.Bar(
                    y=df_torn["Driver"], x=df_torn["Impact%"], orientation="h",
                    marker_color=[C['red'] if v < 0 else C['green'] for v in df_torn["Impact%"]],
                    text=[f"{v:+.1%}" for v in df_torn["Impact%"]],
                    textposition="outside",
                    hovertemplate="%{y}: %{text}<extra></extra>",
                ))
                fig_torn.add_vline(x=0, line_color=C['border2'], line_width=1.5)
                fig_torn.update_layout(
                    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor=C['chart_bg'], font=dict(family="Inter,sans-serif", color=C['text']),
                    margin=dict(l=40,r=40,t=40,b=40),
                    title="Impact on Intrinsic Value (% change from base)",
                    xaxis_title="Change from Base", height=320, showlegend=False
                )
                st.plotly_chart(fig_torn, use_container_width=True)
            except Exception as e:
                st.warning(f"Sensitivity analysis error: {e}")

            st.markdown("---")

    # ══════════════════════════════════════════════════════════════════
    #  MANUAL DCF BUILDER  (always shown as supplementary tool)
    # ══════════════════════════════════════════════════════════════════
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:8px 0 14px;">'
                f'<span class="sb sb-sage">MANUAL</span>'
                f'<span style="font-size:1.15rem;font-weight:700;color:{C["text"]};">Manual DCF Builder — Custom Assumptions</span></div>',
                unsafe_allow_html=True)
    if not base:
        st.info("Waiting for financials…")
    else:
        rev0 = base.get("Revenue", 0)
        opm0 = base.get("OPM", 0)
        lp   = live["price"]
        shares_raw = live.get("shares", 0) or 1

        col1, col2 = st.columns(2)
        with col1:
            if CURRENCY == "INR": (wacc_def,wacc_r),(g_def,g_r) = (11.0,(8.,14.)),(5.0,(3.,7.))
            else:                 (wacc_def,wacc_r),(g_def,g_r) = (8.5,(6.,12.)),(2.5,(1.,5.))
            wacc   = st.slider("WACC (%)",            wacc_r[0], wacc_r[1], wacc_def, .5, key="wacc_s")
            g_term = st.slider("Terminal growth (%)", g_r[0],    g_r[1],    g_def,    .5, key="gterm_s")
        with col2:
            cagr_default = round(
                ((base.get("Revenue",rev0) / hist_df["Revenue"].iloc[-1])**(1/(max(len(hist_df)-1,1)))-1)*100, 1
            ) if len(hist_df)>1 and hist_df["Revenue"].iloc[-1]!=0 else 8.0
            rev_cagr    = st.slider("Revenue CAGR (%)", 0.0, 35.0, float(max(0,min(30,cagr_default))), .5)
            ebit_margin = st.slider("EBIT Margin (%)",  0.0, 50.0, float(max(0,min(45,opm0))), .5)

        result = run_dcf(wacc, g_term, rev_cagr, ebit_margin, lp, base, CURRENCY, shares_raw)
        if result:
            upside = result["upside"]
            up_col = C['green'] if upside >= 0 else C['red']
            c1, c2, c3, c4 = st.columns(4)
            for col_m, label, val_m in [
                (c1,"Intrinsic Value",  f"{SYM}{result['ivps']:,.2f}"),
                (c2,"Margin of Safety", f"{upside:+.1f}%"),
                (c3,"Enterprise Value", f"{SYM}{result['ev']:,.1f} {LBL}"),
                (c4,"Terminal Val %",   f"{result['tv_pct']:.1f}%"),
            ]:
                col_m.markdown(f"""<div class="kpi"><div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{up_col if label=='Margin of Safety' else C['text']};">{val_m}</div></div>""",
                unsafe_allow_html=True)
            st.markdown("")

            t1, t2, t3 = st.tabs(["📋 Projection Table", "🌊 Waterfall", "🎯 Sensitivity"])
            with t1:
                st.dataframe(pd.DataFrame(result["rows"]), use_container_width=True, hide_index=True)
            with t2:
                st.plotly_chart(chart_waterfall(result), use_container_width=True)
            with t3:
                st.markdown('<div class="sec-head">WACC × Terminal Growth — Intrinsic Value per Share</div>', unsafe_allow_html=True)
                stab = sensitivity_table(rev_cagr, ebit_margin, lp, base, CURRENCY, shares_raw)
                flat = [v for row in stab.values for v in row if isinstance(v, (int, float))]
                if flat:
                    lo, hi = min(flat), max(flat)
                    def style_cell(v):
                        if not isinstance(v,(int,float)): return ""
                        if v < lo+(hi-lo)*.33: return f"color:{C['red']};font-weight:700"
                        if v > lo+(hi-lo)*.67: return f"color:{C['green']};font-weight:700"
                        return f"color:{C['amber']}"
                    st.dataframe(stab.style.applymap(lambda v: style_cell(v)), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — MONTE CARLO SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "🎲  Monte Carlo Sim":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Geometric Brownian Motion Price Simulation</div>', unsafe_allow_html=True)

    # ── Parameters ────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1: T       = st.slider("Horizon (years)", 0.5, 5.0, 1.0, 0.5)
    with c2: n_sims  = st.select_slider("Simulations", [1000,2500,5000,10000,25000], value=10000)
    with c3: rf_rate = st.slider("Risk-free rate (%)", 0.0, 8.0, 4.5, 0.25) / 100

    # ── Fetch price data ──────────────────────────────────────────────────────
    if _HAS_ADVANCED:
        try:
            with st.spinner("Fetching historical price data …"):
                s0, mu, sigma, src_name = get_stock_data(TICKER)
            st.caption(f"Price data source: **{src_name}**")
        except Exception as e:
            st.warning(f"Could not fetch price data: {e}. Using live price + estimated params.")
            s0 = live["price"] or 100
            mu, sigma, src_name = 0.12, 0.30, "Estimated"
    else:
        s0 = live["price"] or 100
        ph_hist = get_price_history(TICKER, "3y")
        if not ph_hist.empty:
            lr = np.log(ph_hist["Close"].pct_change()+1).dropna()
            mu    = float(lr.mean()*252)
            sigma = float(lr.std()*np.sqrt(252))
            src_name = "yfinance (computed)"
        else:
            mu, sigma, src_name = 0.12, 0.30, "Estimated"

    # ── Run simulation ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Simulation Parameters</div>', unsafe_allow_html=True)
    p1,p2,p3,p4 = st.columns(4)
    p1.metric("Current Price",    fmt_price(s0, CURRENCY))
    p2.metric("Annual Drift (μ)", f"{mu*100:.1f}%")
    p3.metric("Volatility (σ)",   f"{sigma*100:.1f}%")
    p4.metric("Sharpe (est.)",    f"{(mu-rf_rate)/sigma:.2f}" if sigma else "—")

    with st.spinner(f"Running {n_sims:,} simulations …"):
        if _HAS_ADVANCED:
            from monte_carlo import run_simulation as _sim
            path_matrix, low_band, high_band = _sim(s0, mu, sigma, T, n_sims)
        else:
            n_steps = int(T*252)
            shocks = np.random.normal(0,1,(n_steps,n_sims))
            drift  = (mu-0.5*sigma**2)*(1/252)
            daily  = np.exp(drift+sigma*np.sqrt(1/252)*shocks)
            path_matrix = np.zeros((n_steps+1,n_sims)); path_matrix[0]=s0
            path_matrix[1:] = s0*np.cumprod(daily,axis=0)
            low_band  = np.percentile(path_matrix,5,axis=1)
            high_band = np.percentile(path_matrix,95,axis=1)

    final_prices = path_matrix[-1]

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Simulation Paths</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_monte_carlo(path_matrix, low_band, high_band, s0, T, CURRENCY), use_container_width=True)

    ca, cb = st.columns([1,1])
    with ca:
        st.markdown('<div class="sec-head">Return Distribution</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_histogram(final_prices, s0, CURRENCY), use_container_width=True)
    with cb:
        st.markdown('<div class="sec-head">Price Percentiles</div>', unsafe_allow_html=True)
        pct_df = pd.DataFrame({
            "Percentile": ["1st","5th","10th","25th","50th (Median)","75th","90th","95th","99th"],
            "Price": [fmt_price(np.percentile(final_prices,p),CURRENCY) for p in [1,5,10,25,50,75,90,95,99]],
            "Return": [f"{(np.percentile(final_prices,p)-s0)/s0*100:+.1f}%" for p in [1,5,10,25,50,75,90,95,99]],
        })
        st.dataframe(pct_df, use_container_width=True, hide_index=True)

    # ── Risk Metrics ───────────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Risk & Return Metrics</div>', unsafe_allow_html=True)
    if _HAS_ADVANCED:
        from risk_metrics import calculate_metrics as _cm
        metrics = _cm(final_prices, s0, mu, sigma, rf_rate)
    else:
        returns = (final_prices-s0)/s0
        avg_p = np.mean(final_prices); prob = np.mean(final_prices>s0)
        exp_ret = (avg_p-s0)/s0
        metrics = {
            "Expected Price":      avg_p,  "Median Price":    np.median(final_prices),
            "Expected Return":     exp_ret*100,"Volatility (Annual)":sigma*100,
            "Prob. of Profit":     prob*100, "VaR 95% (Rel)":  np.percentile(returns,5),
            "CVaR 95%":            np.mean(returns[returns<=np.percentile(returns,5)]),
            "Sharpe Ratio":        (mu-rf_rate)/sigma if sigma else 0,
            "Max Upside":          (np.max(final_prices)-s0)/s0*100,
            "Max Drawdown":        (np.min(final_prices)-s0)/s0*100,
            "Signal":              "🟢 STRONG BUY" if (exp_ret>0.15 and prob>0.65) else ("🟡 ACCUMULATE" if (exp_ret>0.05 and prob>0.55) else "🔴 AVOID"),
        }

    # Signal banner
    sig = metrics.get("Signal","—")
    _is_buy  = "🟢" in sig
    _is_hold = "🟡" in sig
    sig_bg  = C['green_bg']  if _is_buy  else (C['amber_bg'] if _is_hold else C['red_bg'])
    sig_bd  = C['green']     if _is_buy  else (C['amber']    if _is_hold else C['red'])
    sig_tc  = C['green_t']   if _is_buy  else (C['amber_t']  if _is_hold else C['red_t'])
    st.markdown(f"""<div style="background:{sig_bg};border:1.5px solid {sig_bd};border-radius:12px;padding:1.2rem 1.6rem;text-align:center;margin:.8rem 0;box-shadow:0 2px 8px rgba(0,0,0,.05);">
      <div style="font-size:1.65rem;font-weight:800;color:{sig_tc};letter-spacing:.5px;">{sig}</div>
      <div style="font-size:.82rem;color:{sig_tc};opacity:.85;margin-top:5px;font-weight:500;">
        Expected Return: <b>{metrics.get('Expected Return',0):.1f}%</b> &nbsp;·&nbsp; Prob. of Profit: <b>{metrics.get('Prob. of Profit',0):.1f}%</b>
      </div></div>""", unsafe_allow_html=True)

    # Metrics grid
    metric_items = [
        ("Expected Price",   fmt_price(metrics.get("Expected Price",0),CURRENCY)),
        ("Median Price",     fmt_price(metrics.get("Median Price",0),CURRENCY)),
        ("Expected Return",  f"{metrics.get('Expected Return',0):.1f}%"),
        ("Volatility",       f"{metrics.get('Volatility (Annual)',0):.1f}%"),
        ("Prob. of Profit",  f"{metrics.get('Prob. of Profit',0):.1f}%"),
        ("Sharpe Ratio",     f"{metrics.get('Sharpe Ratio',0):.2f}"),
        ("VaR 95%",          f"{metrics.get('VaR 95% (Rel)',0)*100:.1f}%"),
        ("CVaR 95%",         f"{metrics.get('CVaR 95%',0)*100:.1f}%"),
        ("Max Upside",       f"{metrics.get('Max Upside',0):.1f}%"),
        ("Max Drawdown",     f"{metrics.get('Max Drawdown',0):.1f}%"),
    ]
    html = '<div class="kpi-grid">'+"".join(f'<div class="kpi"><div class="kpi-label">{k}</div><div class="kpi-value" style="font-size:1.05rem;">{v}</div></div>' for k,v in metric_items)+'</div>'
    st.markdown(html, unsafe_allow_html=True)

    if _HAS_ADVANCED and hasattr(metrics,'get') and "Prob. of >10% Gain" in metrics:
        prob_items = [
            ("P(>10% gain)",  f"{metrics.get('Prob. of >10% Gain',0):.1f}%"),
            ("P(>25% gain)",  f"{metrics.get('Prob. of >25% Gain',0):.1f}%"),
            ("P(>10% loss)",  f"{metrics.get('Prob. of >10% Loss',0):.1f}%"),
            ("Sortino Ratio", f"{metrics.get('Sortino Ratio',0):.2f}"),
            ("Risk-Reward",   f"{metrics.get('Risk-Reward Ratio',0):.2f}"),
        ]
        st.markdown('<div class="kpi-grid" style="grid-template-columns:repeat(5,1fr);">' +
            "".join(f'<div class="kpi"><div class="kpi-label">{k}</div><div class="kpi-value" style="font-size:1rem;">{v}</div></div>' for k,v in prob_items) +
            '</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — RISK METRICS
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "⚠️  Risk Metrics":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Risk Analysis & Value-at-Risk</div>', unsafe_allow_html=True)

    ph = get_price_history(TICKER, "3y")
    if ph.empty:
        st.error("Price history unavailable for risk computation.")
    else:
        close_prices = ph["Close"].dropna().values
        log_returns  = np.log(close_prices[1:]/close_prices[:-1])
        mu    = float(np.mean(log_returns)*252)
        sigma = float(np.std(log_returns)*np.sqrt(252))
        s0    = float(close_prices[-1])
        rf    = 0.045 if CURRENCY=="USD" else 0.072

        # Quick sim for VaR
        n_steps = 252; n_sims = 10000
        shocks = np.random.normal(0,1,(n_steps,n_sims))
        daily  = np.exp((mu-0.5*sigma**2)/252 + sigma/np.sqrt(252)*shocks)
        pm = np.zeros((n_steps+1,n_sims)); pm[0]=s0; pm[1:]=s0*np.cumprod(daily,axis=0)
        fp = pm[-1]; returns=(fp-s0)/s0

        col1, col2 = st.columns([1,1])
        with col1:
            st.markdown('<div class="sec-head">Key Risk Indicators</div>', unsafe_allow_html=True)
            sharpe = (mu-rf)/sigma if sigma else 0
            sortino_dn = np.std(log_returns[log_returns<0])*np.sqrt(252)
            sortino = (mu-rf)/sortino_dn if sortino_dn else 0
            var_95  = np.percentile(returns,5)
            cvar_95 = float(np.mean(returns[returns<=var_95]))
            var_99  = np.percentile(returns,1)
            max_up  = (np.max(fp)-s0)/s0

            risk_data = [
                ("Annual Return (μ)",   f"{mu*100:.1f}%",       "Historical drift"),
                ("Annual Volatility",   f"{sigma*100:.1f}%",    "σ annualised"),
                ("Sharpe Ratio",        f"{sharpe:.2f}",         "Risk-adj return"),
                ("Sortino Ratio",       f"{sortino:.2f}",        "Downside-adj return"),
                ("VaR 95%",             f"{var_95*100:.1f}%",    "Max loss 95% confidence"),
                ("CVaR 95% (ES)",       f"{cvar_95*100:.1f}%",   "Expected shortfall"),
                ("VaR 99%",             f"{var_99*100:.1f}%",    "Max loss 99% confidence"),
                ("Beta",                f"{live['beta']:.2f}",   "vs Market"),
                ("Max Upside",          f"{max_up*100:.1f}%",    "Best case 1Y"),
                ("Prob. Profit",        f"{np.mean(fp>s0)*100:.1f}%", "1Y horizon"),
            ]
            for k,v,sub in risk_data:
                st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                  padding:8px 0;border-bottom:1px solid {C['border']};font-size:.85rem;">
                  <span style="color:{C['sb_text']}">{k}<br><span style="font-size:.68rem;color:{C['muted']}">{sub}</span></span>
                  <b>{v}</b></div>""", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="sec-head">Risk Register</div>', unsafe_allow_html=True)
            pe   = live.get("pe",0); nd_v=base.get("NetDebt",0) if base else 0
            ind  = live.get("industry","—"); sec = live.get("sector","—")
            if CURRENCY=="INR":
                risks = [
                    ("Regulatory (SEBI/RBI)", "Medium","High","Monitor SEBI filings, governance"),
                    ("FX / Currency",         "Medium","Medium","Track INR/USD exposure"),
                    ("Valuation Re-rating",   "Medium","High", f"P/E {pe:.1f}x — watch earnings miss risk"),
                    ("Leverage",              "Low" if nd_v<0 else "Medium","High",f"{'Net cash' if nd_v<0 else f'Net debt {SYM}{nd_v:,.1f} {LBL}'} — monitor coverage"),
                    ("Competitive Disruption","Medium","High", f"Track market share in {ind}"),
                    ("Global Macro",          "Medium","Medium","Revenue diversification"),
                ]
            else:
                risks = [
                    ("Regulatory (FTC/DOJ)",  "Low-Med","High","Monitor antitrust filings"),
                    ("Interest Rate Risk",    "Medium", "Medium",f"Beta {live.get('beta',1):.2f}"),
                    ("Valuation Premium",     "Medium", "High", f"P/E {pe:.1f}x — multiple compression risk"),
                    ("Balance Sheet",         "Low" if nd_v<0 else "Medium","High",f"{'Net cash' if nd_v<0 else f'Net debt'}"),
                    ("Geopolitical / Trade",  "Medium", "Medium","Supply chain, tariff exposure"),
                    ("AI Disruption",         "Medium", "High", f"AI displacement risk in {sec}"),
                    ("Management",            "Low",    "High", "Track capex, M&A, succession"),
                ]
            risk_df = pd.DataFrame(risks, columns=["Risk","Probability","Impact","Mitigation"])
            st.dataframe(risk_df, use_container_width=True, hide_index=True)

        st.markdown('<div class="sec-head">Distribution of 1-Year Returns</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_histogram(fp, s0, CURRENCY), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 6 — CAPITAL STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "🏗️  Capital Structure":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Optimal Capital Structure (Modigliani-Miller / Trade-Off Theory)</div>', unsafe_allow_html=True)

    if not base:
        st.info("Financials loading…")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if CURRENCY=="INR":
                rf_cs = st.slider("Risk-free rate (%)", 5.0, 9.0, 7.2, .1, key="cs_rf") / 100
                erp_cs= st.slider("ERP (%)",            4.0, 9.0, 6.5, .5, key="cs_erp") / 100
                kd_cs = st.slider("Pre-tax cost of debt (%)", 6.0, 14.0, 9.0, .5, key="cs_kd") / 100
                tax_cs= st.slider("Tax rate (%)", 15.0, 35.0, 25.0, 1.0, key="cs_tax") / 100
            else:
                rf_cs = st.slider("Risk-free rate (%)", 2.0, 7.0, 4.5, .1, key="cs_rf") / 100
                erp_cs= st.slider("ERP (%)",            4.0, 8.0, 5.5, .5, key="cs_erp") / 100
                kd_cs = st.slider("Pre-tax cost of debt (%)", 3.0, 10.0, 5.5, .5, key="cs_kd") / 100
                tax_cs= st.slider("Tax rate (%)", 10.0, 35.0, 21.0, 1.0, key="cs_tax") / 100
        with col2:
            beta_v = live.get("beta", 1.0)
            unlevered_beta = beta_v / (1 + (1-tax_cs)*((base.get("Debt",1))/(max(base.get("Equity",1),0.001))))
            cur_dr = base.get("Debt",0) / (base.get("Debt",0)+base.get("Equity",1)) if (base.get("Debt",0)+base.get("Equity",0)) else 0.3
            cs_dr  = st.slider("Debt Ratio to analyse (%)", 0.0, 80.0, round(cur_dr*100,0), 5.0, key="cs_dr") / 100
            st.metric("Current Debt Ratio", f"{cur_dr*100:.1f}%")
            st.metric("Unlevered Beta",      f"{unlevered_beta:.3f}")

        # ── WACC curve ─────────────────────────────────────────────────────────
        dr_range = np.linspace(0.0, 0.80, 81)
        waccs = []
        for dr in dr_range:
            de  = dr/(1-dr) if dr<1 else 9
            lb  = unlevered_beta*(1+(1-tax_cs)*de)
            ke  = rf_cs+lb*erp_cs
            dist= max(0,(dr-.6)*.15)
            kd  = kd_cs+dist
            waccs.append((1-dr)*ke+dr*kd*(1-tax_cs))
        opt_dr = dr_range[np.argmin(waccs)]
        opt_wacc = min(waccs)

        fig_wacc = go.Figure()
        fig_wacc.add_trace(go.Scatter(x=dr_range*100, y=[w*100 for w in waccs],
            name="WACC (%)", line=dict(color=C['accent'],width=2.5)))
        fig_wacc.add_vline(x=opt_dr*100, line_color=C['green'], line_dash="dash",
            annotation_text=f"Opt D/V={opt_dr:.0%}", annotation_position="top right")
        fig_wacc.add_vline(x=cur_dr*100, line_color=C['amber'], line_dash="dot",
            annotation_text=f"Current={cur_dr:.0%}", annotation_position="bottom right")
        fig_wacc.add_vline(x=cs_dr*100, line_color=C['purple'], line_dash="dot",
            annotation_text=f"Custom={cs_dr:.0%}", annotation_position="top left")
        fig_wacc.update_layout(height=320, **_LAYOUT,
            xaxis=dict(title="Debt Ratio (%)", gridcolor=C['border']),
            yaxis=dict(title="WACC (%)", ticksuffix="%", gridcolor=C['border']))
        st.markdown('<div class="sec-head">WACC Curve (Trade-Off Theory)</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_wacc, use_container_width=True)

        # Insight
        if abs(cs_dr-opt_dr) < 0.05:
            insight = f"✅ Near-optimal capital structure at {cs_dr:.0%} D/V. Minimal WACC improvement available."
            i_bg, i_bd, i_tc = C['green_bg'], C['green'], C['green_t']
        elif cs_dr < opt_dr-.10:
            insight = f"📉 Under-leveraged vs optimum (~{opt_dr:.0%}). Additional debt could lower WACC and boost firm value — subject to financial flexibility constraints."
            i_bg, i_bd, i_tc = C['amber_bg'], C['amber'], C['amber_t']
        else:
            insight = f"📈 Over-leveraged vs optimum (~{opt_dr:.0%}). Excess debt increases financial distress risk and raises WACC above minimum."
            i_bg, i_bd, i_tc = C['red_bg'], C['red'], C['red_t']
        st.markdown(f'<div style="background:{i_bg};border:1px solid {i_bd}40;border-left:3px solid {i_bd};border-radius:0 10px 10px 0;padding:14px 18px;color:{i_tc};font-size:.88rem;font-weight:500;margin:.8rem 0;">{insight}</div>', unsafe_allow_html=True)

        # Scenario table
        st.markdown('<div class="sec-head">Scenario Comparison</div>', unsafe_allow_html=True)
        scenarios = [("All Equity (0%)",0.),("Conservative (20%)",.20),("Current",cur_dr),
                     (f"Custom ({cs_dr:.0%})",cs_dr),(f"Optimal ({opt_dr:.0%})",opt_dr),("Aggressive (70%)",.70)]
        rows = []
        for sname, sdr in scenarios:
            de = sdr/(1-sdr) if sdr < 1 else 9
            lb = unlevered_beta*(1+(1-tax_cs)*de)
            ke = rf_cs+lb*erp_cs
            kd = kd_cs+max(0,(sdr-.6)*.15)
            w  = (1-sdr)*ke+sdr*kd*(1-tax_cs)
            # Compute intrinsic value at this WACC if advanced modules available
            iv_scen = "—"
            if _HAS_ADVANCED:
                try:
                    from valuation_models import fcff_two_stage as _fts2, compute_fcff as _cff
                    _val_s = run_valuation(TICKER)
                    _fd_s  = _val_s.get("fundamentals", {})
                    _mc_s  = _val_s.get("model_selection", {})
                    _sh    = _fd_s.get("shares_outstanding", 1)
                    _hg    = _fd_s.get("firm_growth_rate", 0.08)
                    _sg    = _fd_s.get("stable_growth", 0.03)
                    _fcff  = _cff(_fd_s.get("ebit",0), _fd_s.get("tax_rate",0.25), _fd_s.get("depreciation",0), _fd_s.get("capex",0), _fd_s.get("delta_wc",0))
                    _r     = _fts2(_fcff, max(.01,w), max(.01,w*.95), _hg, _sg, 7, _fd_s.get("total_debt",0), _fd_s.get("cash",0), _sh)
                    iv_s   = max(0, _r.get("intrinsic_value_per_share", _r.get("intrinsic_value", 0)))
                    iv_scen = f"{SYM}{iv_s:,.2f}" if iv_s > 0 else "—"
                except: pass
            rows.append({"Scenario":sname,"D/V":f"{sdr:.0%}","Levered β":f"{lb:.2f}",
                         "Ke":f"{ke:.1%}","Kd":f"{kd:.1%}","WACC":f"{w:.1%}","Intrinsic Value":iv_scen})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with st.expander("📚 Theory Reference (MM + Hamada)"):
            st.markdown("""
**MM Prop I (with taxes):** V_L = V_U + τ·D  
**MM Prop II:** K_e = K_u + (K_u − K_d)(1−τ)(D/E)  
**Hamada:** β_L = β_U × [1 + (1−τ) × D/E]  
**Trade-Off Theory:** Optimal D/V balances tax shield vs. financial distress costs  
**WACC:** (E/V)·Ke + (D/V)·Kd·(1−τ) — minimising WACC maximises firm value
            """)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 7 — PEER ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "🔍  Peer Analysis":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Comparable Company Analysis</div>', unsafe_allow_html=True)

    ind_low = live.get("industry","").lower()
    group_key = next((v for k,v in INDUSTRY_KEY.items() if k in ind_low), None)
    default_peers = SECTOR_PEERS.get(group_key, [])
    if TICKER not in default_peers: default_peers = [TICKER]+default_peers[:6]

    peer_input = st.text_input("Peer tickers (comma-separated)", ", ".join(default_peers[:7]))
    peers = [p.strip().upper() for p in peer_input.split(",") if p.strip()]

    if peers:
        with st.spinner("Fetching peer data …"):
            peer_df = get_peer_data(peers, CURRENCY)
        if not peer_df.empty:
            st.markdown('<div class="sec-head">Valuation & Profitability Comparison</div>', unsafe_allow_html=True)
            st.dataframe(peer_df, use_container_width=True, hide_index=True)

            # ── Scatter: P/E vs OPM ────────────────────────────────────────────
            st.markdown('<div class="sec-head">P/E Ratio vs Operating Margin</div>', unsafe_allow_html=True)
            valid = peer_df[(peer_df["P/E"]>0) & (peer_df["P/E"]<100) & (peer_df["OPM%"].abs()<100)]
            if not valid.empty:
                fig_sc = go.Figure()
                colors = [C['red'] if r["Ticker"]==TICKER else C['accent'] for _,r in valid.iterrows()]
                fig_sc.add_trace(go.Scatter(x=valid["OPM%"],y=valid["P/E"],mode="markers+text",
                    text=valid["Company"],textposition="top center",
                    marker=dict(size=12,color=colors,opacity=.85,line=dict(width=1,color="white"))))
                fig_sc.update_layout(height=360,**_LAYOUT,
                    xaxis=dict(title="Operating Margin (%)",gridcolor=C['border']),
                    yaxis=dict(title="P/E Ratio",gridcolor=C['border']))
                st.plotly_chart(fig_sc, use_container_width=True)

            # ── Bar: Revenue Growth ────────────────────────────────────────────
            st.markdown('<div class="sec-head">Revenue Growth Comparison</div>', unsafe_allow_html=True)
            rg_df = peer_df[["Company","Rev Growth%"]].dropna()
            rg_df = rg_df[rg_df["Rev Growth%"].abs() < 100]
            if not rg_df.empty:
                colors_rg = [C['green'] if v>=0 else C['red'] for v in rg_df["Rev Growth%"]]
                fig_rg = go.Figure(go.Bar(x=rg_df["Company"],y=rg_df["Rev Growth%"],
                    marker_color=colors_rg,opacity=.8))
                fig_rg.update_layout(height=280,**_LAYOUT,
                    yaxis=dict(ticksuffix="%",gridcolor=C['border']),
                    xaxis=dict(tickangle=-30))
                st.plotly_chart(fig_rg, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 8 — STRATEGY
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "♟️  Strategy":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Strategic Analysis (Damodaran Framework)</div>', unsafe_allow_html=True)

    pe=live.get("pe",0); pb=live.get("pb",0)
    opm=base.get("OPM",0) if base else 0; roe_v=base.get("ROE",0) if base else 0
    rev=base.get("Revenue",0) if base else 0; ni=base.get("NI",0) if base else 0
    nd_v=base.get("NetDebt",0) if base else 0
    beta_v=live.get("beta",1.0); div_y=live.get("div_yield",0)
    sec=live.get("sector","—"); ind=live.get("industry","—")
    npm=base.get("NPM",0) if base else 0

    # SWOT-style tiles
    tab1,tab2,tab3,tab4 = st.tabs(["🏛️ Investment Thesis","📐 Value Drivers","⚠️ Risk Register","🧭 Positioning"])

    with tab1:
        narrative = f"""
{DISPLAY_NAME} ({TICKER}) operates in <b>{ind}</b>, a segment of the broader <b>{sec}</b> sector.
At {SYM}{live['price']:,.2f} per share, the stock trades at {pe:.1f}x trailing earnings and {pb:.1f}x book value.
{"The company's strong <b>net cash position</b> ({SYM}{abs(nd_v):,.1f} {LBL}) provides strategic flexibility for M&A and buybacks." if nd_v<0 else f"With <b>net debt of {SYM}{nd_v:,.1f} {LBL}</b>, financial leverage remains a key watch item."}
Operating margins of <b>{opm:.1f}%</b> and ROE of <b>{roe_v:.1f}%</b>
{"signal a high-quality business with durable competitive advantages." if (opm>20 and roe_v>18) else "reflect a competitive but not distinctly advantaged market position."}
"""
        st.markdown(f'<div class="narrative">{narrative}</div>', unsafe_allow_html=True)

        g1,g2 = st.columns(2)
        with g1:
            st.markdown(f"""<div class="card" style="border:1px solid {C['green_bd']};background:{C['green_bg']};">
              <b style="color:{C['green_t']};">✓ Bull Case</b>
              <ul style="font-size:.84rem;margin-top:.5rem;color:{C['sb_text']};line-height:1.9;padding-left:1.2rem;">
                <li>{"Strong cash generation and M&A firepower" if nd_v<0 else "Improving leverage ratio with strong cash flows"}</li>
                <li>{"High-margin compounding with ROE " + str(round(roe_v,0)) + "%" if roe_v>15 else "Margin expansion potential from operating leverage"}</li>
                <li>{"International expansion across growing markets" if CURRENCY=="INR" else "Shareholder returns via buybacks and dividends"}</li>
                <li>{"Favourable regulatory environment" if CURRENCY=="INR" else "AI / automation tailwind for productivity"}</li>
              </ul>
            </div>""", unsafe_allow_html=True)
        with g2:
            st.markdown(f"""<div class="card" style="border:1px solid {C['red_bd']};background:{C['red_bg']};">
              <b style="color:{C['red_t']};">✗ Bear Case</b>
              <ul style="font-size:.84rem;margin-top:.5rem;color:{C['sb_text']};line-height:1.9;padding-left:1.2rem;">
                <li>{"Valuation premium at " + str(round(pe,1)) + "x P/E — earnings miss compresses multiple" if pe>25 else "Revenue growth deceleration risk"}</li>
                <li>{"Rising input cost / margin pressure" if CURRENCY=="INR" else "Interest rate sensitivity (Beta: " + str(round(beta_v,2)) + ")"}</li>
                <li>{"FX volatility impacting exports / imports" if CURRENCY=="INR" else "Regulatory / antitrust overhang in " + sec}</li>
                <li>{"Promoter pledging or governance risk" if CURRENCY=="INR" else "Management succession / capital allocation risk"}</li>
              </ul>
            </div>""", unsafe_allow_html=True)

    with tab2:
        if len(hist_df)>1:
            cagr_r = round((hist_df["Revenue"].iloc[0]/hist_df["Revenue"].iloc[-1])**(1/(len(hist_df)-1))-1,3)*100
        else: cagr_r=0
        drivers = pd.DataFrame([
            {"Driver":"Revenue CAGR (hist.)",    "Current":f"{cagr_r:.1f}%",   "Value Impact":"High"},
            {"Driver":"EBIT Margin",              "Current":f"{opm:.1f}%",      "Value Impact":"High"},
            {"Driver":"Return on Equity",         "Current":f"{roe_v:.1f}%",    "Value Impact":"High"},
            {"Driver":"Net Debt / Cash",          "Current":f"{SYM}{nd_v:,.1f} {LBL}","Value Impact":"Medium"},
            {"Driver":"Beta",                     "Current":f"{beta_v:.2f}",    "Value Impact":"Medium"},
            {"Driver":"Dividend Yield",           "Current":f"{div_y:.2f}%",   "Value Impact":"Low"},
            {"Driver":"Trailing P/E",             "Current":f"{pe:.1f}x",       "Value Impact":"Signal"},
        ])
        st.dataframe(drivers, use_container_width=True, hide_index=True)

    with tab3:
        if CURRENCY=="INR":
            risks_s = [
                ("Regulatory (SEBI/RBI/Sector)","Medium","High","Monitor SEBI/sector filings, governance"),
                ("FX / Currency","Medium","Medium","Track INR/USD; hedge export/import exposure"),
                ("Valuation Re-rating","Medium","High",f"P/E {pe:.1f}x — monitor vs sector median"),
                ("Leverage / Liquidity","Low" if nd_v<0 else "Medium","High",f"{'Net cash' if nd_v<0 else f'Net debt {SYM}{nd_v:,.1f} {LBL}'}"),
                ("Promoter / Governance","Low-Medium","High","Check pledging, RPTs in annual report"),
                ("Global Macro","Medium","Medium","Revenue diversification; commodity/demand cycle"),
                ("Competitive Disruption","Medium","High",f"Track market share in {ind}"),
            ]
        else:
            risks_s = [
                ("Regulatory / Antitrust","Low-Medium","High","Monitor regulatory filings"),
                ("Interest Rate","Medium","Medium",f"Beta {beta_v:.2f} — {'low' if beta_v<.8 else 'moderate/high'} sensitivity"),
                ("Valuation Premium","Medium","High",f"P/E {pe:.1f}x — earnings miss compresses multiple"),
                ("Balance Sheet","Low" if nd_v<0 else "Medium","High",f"{'Net cash' if nd_v<0 else f'Net debt {SYM}{abs(nd_v):,.1f} {LBL}'}"),
                ("Geopolitical / Trade","Medium","Medium","Supply chain diversification; tariff exposure"),
                ("Technology Disruption","Medium","High",f"AI/automation risk in {sec}"),
                ("Mgmt / Capital Allocation","Low","High","Track capex, M&A, CEO succession"),
            ]
        st.dataframe(pd.DataFrame(risks_s,columns=["Risk","Probability","Impact","Mitigation"]),use_container_width=True,hide_index=True)

    with tab4:
        moat = "Wide Moat" if (opm>25 and roe_v>20) else ("Narrow Moat" if (opm>15 or roe_v>15) else "No Moat / Commodity")
        stage= "Early Growth" if pe>45 else ("Growth" if pe>28 else ("Mature" if pe>12 else "Decline / Deep Value"))
        cls_m = "chip-g" if "Wide" in moat else ("chip-a" if "Narrow" in moat else "chip-r")
        cls_s = "chip-b" if "Growth" in stage else "chip-a"
        st.markdown(f"""<div class="card">
          <div style="display:flex;gap:.8rem;flex-wrap:wrap;margin-bottom:1rem;">
            <span class="chip {cls_m}">Moat: {moat}</span>
            <span class="chip {cls_s}">Stage: {stage}</span>
            <span class="chip chip-p">Sector: {sec}</span>
          </div>
          <div style="font-size:.84rem;color:{C['sb_text']};line-height:1.9;">
            <b>Competitive positioning:</b><br>
            {"High margins and ROE suggest durable pricing power and competitive barriers to entry." if (opm>20 and roe_v>18)
             else "Average competitive position — business faces moderate competitive intensity." if opm>12
             else "Commoditised market — differentiation and volume are key value drivers."}<br><br>
            <b>Capital allocation profile:</b><br>
            {"Capital-light with high returns — ideal for compounding at reinvestment rates." if (opm>20 and roe_v>18)
             else "Capital allocation discipline is critical given moderate return profile." if roe_v>10
             else "Low returns on equity — buybacks or dividends may create more value than reinvestment."}
          </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 9 — LIVE NEWS
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "📰  Live News":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Live News Feed (Google News RSS)</div>', unsafe_allow_html=True)

    with st.spinner("Fetching news …"):
        news = get_news(DISPLAY_NAME, TICKER)

    pos_n=sum(1 for n in news if n["sentiment"]=="positive")
    neg_n=sum(1 for n in news if n["sentiment"]=="negative")
    neu_n=sum(1 for n in news if n["sentiment"]=="neutral")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Headlines", len(news))
    c2.metric("Positive 🟢", pos_n)
    c3.metric("Neutral ⬜",  neu_n)
    c4.metric("Negative 🔴", neg_n)

    sf = st.selectbox("Filter by sentiment", ["All","positive","neutral","negative"])
    filtered = news if sf=="All" else [n for n in news if n["sentiment"]==sf]

    col_a, col_b = st.columns([3,1])
    with col_a:
        if not filtered:
            st.info("No news found. Google RSS may be temporarily unavailable.")
        for item in filtered:
            cls = {"positive":"news-pos","negative":"news-neg","neutral":"news-neu"}.get(item["sentiment"],"news-neu")
            sent_chip = {"positive":f'<span class="chip chip-g">positive</span>',
                         "negative":f'<span class="chip chip-r">negative</span>',
                         "neutral":f'<span class="chip chip-b">neutral</span>'}.get(item["sentiment"],"")
            link_html = f'<a href="{item["link"]}" target="_blank" style="font-size:.72rem;color:{C["accent2"]};font-weight:700;">Read →</a>' if item["link"]!="#" else ""
            st.markdown(f"""<div class="{cls}">
              <div class="news-title">{item['title']}</div>
              <div class="news-meta">{sent_chip} &nbsp; {item['date']} &nbsp; {link_html}</div>
            </div>""", unsafe_allow_html=True)

    with col_b:
        if pos_n+neg_n+neu_n>0:
            fig_pie = go.Figure(go.Pie(
                labels=["Positive","Neutral","Negative"],
                values=[max(pos_n,1),max(neu_n,1),max(neg_n,1)],
                hole=.55,
                marker_colors=[C['green'],C['accent'],C['red']],
                textinfo="label+percent",textfont=dict(size=11)))
            fig_pie.update_layout(height=240,**_LAYOUT,margin=dict(l=10,r=10,t=10,b=10),showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        sig_note = ("SEBI filings, dividend declarations, order wins, PAT surprises"
                    if CURRENCY=="INR" else
                    "SEC 8-K filings, earnings beats, buybacks, M&A, FDA clearances")
        st.markdown(f"""<div class="card card-l" style="font-size:.82rem;margin-top:.5rem;">
          <b>Signal (high weight)</b><br><span style="color:{C['muted']}">{sig_note}</span><br><br>
          <b>Noise (low weight)</b><br><span style="color:{C['muted']}">Analyst PT changes, ETF flow data, index rebalancing</span>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 10 — DATA AUDIT
# ══════════════════════════════════════════════════════════════════════════════
elif PAGE == "🔬  Data Audit":
    st.markdown(f'<h1 style="font-size:1.65rem;margin-bottom:.2rem;">{DISPLAY_NAME}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="company-meta">{TICKER} · Automated Multi-Source Data Audit</div>', unsafe_allow_html=True)

    if _HAS_AUDIT:
        hcfd = None
        if _HAS_ADVANCED and TICKER in FUNDAMENTAL_DATA:
            hcfd = FUNDAMENTAL_DATA[TICKER]
        with st.spinner("Running cross-source audit …"):
            try:
                audit = run_data_audit(TICKER, hardcoded_fd=hcfd)
                status = audit.get("overall_status","COMPLETE")
                status_cfg = {
                    "VERIFIED":          (C['green_bg'],  C['green'],  C['green_t'],  "✅ All sources verified"),
                    "MINOR DISCREPANCY": (C['amber_bg'],  C['amber'],  C['amber_t'],  "⚠️ Minor discrepancy"),
                    "MAJOR DISCREPANCY": (C['red_bg'],    C['red'],    C['red_t'],    "🚨 Major discrepancy"),
                }
                sb,sc,stc,slbl = status_cfg.get(status,(C['purple_bg'],C['purple'],C['purple_t'],"ℹ️ Complete"))
                st.markdown(f"""<div style="background:{sb};border:1.5px solid {sc};border-radius:12px;padding:14px 20px;margin-bottom:16px;">
                  <span style="color:{stc};font-weight:800;font-size:1rem;">{slbl}</span>
                  <span style="color:{stc};font-size:.78rem;margin-left:12px;opacity:.75;">{len(audit.get('flags',[]))} flag(s) · {audit.get('timestamp','')}</span>
                </div>""", unsafe_allow_html=True)

                flags = audit.get("flags",[])
                if flags:
                    with st.expander(f"🚩 {len(flags)} Flag(s)", expanded=True):
                        for f in flags:
                            if isinstance(f,dict):
                                sev=f.get("severity","info"); msg=f.get("message",str(f)); field=f.get("field","")
                            else:
                                sev="warning" if "⚠️" in str(f) else "critical" if "🔴" in str(f) else "info"
                                msg=str(f).lstrip("⚠️🔴✅ "); field=""
                            cls="af-r" if sev=="critical" else "af-y" if sev=="warning" else "af-g"
                            ic ="🔴" if sev=="critical" else "🟡" if sev=="warning" else "🟢"
                            lbl=f"<b>{field}</b>: " if field else ""
                            st.markdown(f'<div class="{cls}">{ic} {lbl}{msg}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="af-g">🟢 All sources in agreement — no flags raised.</div>', unsafe_allow_html=True)

                ps = audit.get("price_sources",[])
                if ps:
                    st.markdown('<div class="sec-head">Price Sources</div>', unsafe_allow_html=True)
                    pr=[]
                    for d in (ps if isinstance(ps,list) else list(ps.values())):
                        if not isinstance(d,dict): continue
                        if "error" in d: pr.append({"Source":d.get("source","—"),"Price":"⚠️ Error","Status":"FAIL","Note":str(d.get("error",""))[:60]})
                        else: pr.append({"Source":d.get("source","—"),"Price":f"{SYM}{d.get('price',0):,.2f}","Status":d.get("status","OK"),"Note":d.get("label","")[:50]})
                    if pr: st.dataframe(pd.DataFrame(pr),use_container_width=True,hide_index=True)

                ag = audit.get("agreement",{})
                if ag:
                    st.markdown('<div class="sec-head">Fundamentals Agreement</div>', unsafe_allow_html=True)
                    ar=[{"Metric":m,"Src A":v.get("source_a_val","—"),"Src B":v.get("source_b_val","—"),
                         "Src C":v.get("source_c_val","—"),"Spread":f"{v.get('spread_pct',0):.1f}%",
                         "✓":"✅" if v.get("agree") else "⚠️"} for m,v in ag.items() if isinstance(v,dict)]
                    if ar: st.dataframe(pd.DataFrame(ar),use_container_width=True,hide_index=True)

                hvl = audit.get("hardcoded_vs_live",{})
                if hvl and isinstance(hvl,dict) and any(isinstance(v,dict) for v in hvl.values()):
                    st.markdown('<div class="sec-head">Hardcoded vs Live</div>', unsafe_allow_html=True)
                    hr=[{"Field":f,"Hardcoded":v.get("hardcoded","—"),"Live":v.get("live","—"),
                         "Δ":v.get("delta","—"),"⚑":"🚨" if v.get("flag")=="critical" else "⚠️" if v.get("flag")=="warning" else "✅"}
                        for f,v in hvl.items() if isinstance(v,dict)]
                    if hr: st.dataframe(pd.DataFrame(hr),use_container_width=True,hide_index=True)

            except Exception as e:
                st.error(f"Audit error: {e}")
    else:
        # Lightweight audit without advanced modules
        st.markdown('<div class="sec-head">Price Verification</div>', unsafe_allow_html=True)
        p1 = live["price"]
        try:
            ph_check = get_price_history(TICKER,"5d")
            p2 = float(ph_check["Close"].iloc[-1]) if not ph_check.empty else 0
        except: p2=0
        delta = abs(p1-p2)/p1*100 if p1 else 0
        _ok = delta < 2
        st.markdown(f"""<div style="background:{C['green_bg'] if _ok else C['amber_bg']};
          border:1px solid {C['green_bd'] if _ok else C['amber_bd']};
          border-radius:10px;padding:14px 20px;margin-bottom:1rem;
          color:{C['green_t'] if _ok else C['amber_t']};font-weight:600;">
          {'✅ VERIFIED' if _ok else '⚠️ MINOR DISCREPANCY'} — Price delta between sources: {delta:.2f}%
        </div>""", unsafe_allow_html=True)
        st.metric("fast_info price", fmt_price(p1, CURRENCY))
        st.metric("history price",   fmt_price(p2, CURRENCY))
        st.info("Install cross_verify.py and data_audit.py for full multi-source audit.")

    st.markdown(f'<div style="font-size:.72rem;color:{C["subtle"]};margin-top:1rem;">'
                f'{"🇮🇳 NSE/BSE" if is_india(TICKER) else "🇺🇸 NYSE/NASDAQ"} · {CURRENCY} · '
                f'Audit modules: {"✅ Available" if _HAS_AUDIT else "⚠️ Not loaded"}</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="footer">
  ◈ Unified Equity Research Terminal v4.0 &nbsp;·&nbsp;
  Data: Yahoo Finance / Google News RSS &nbsp;·&nbsp;
  {"🇮🇳 NSE/BSE · ₹ Crores" if is_india(TICKER) else "🇺🇸 NYSE/NASDAQ · $ Billions"} &nbsp;·&nbsp;
  Framework: Damodaran (NYU Stern) &nbsp;·&nbsp;
  {datetime.now().strftime("%d %B %Y  %H:%M")}<br>
  <b style="color:{C['accent']};">Academic / research use only — not investment advice</b>
</div>
""", unsafe_allow_html=True)
