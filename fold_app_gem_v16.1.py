import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any

# --- CONFIGURATION & CONSTANTS ---
PAGE_TITLE = "XGA Valuation Engine"
BLOCKS_PER_YEAR = 2_628_000  # 7,200 slots/day * 365
FOLD_TOTAL_SUPPLY = 2_000_000

# XGA Constants
XGA_TOTAL_SUPPLY = 270_000_000
AIRDROP_RATIO = 5.0 # Fixed: 5 XGA per 1 FOLD

SCENARIO_PRESETS: Dict[str, Dict[str, float]] = {
    "Conservative": {
        "market_share_pct": 10,
        "adjustment_rate_pct": 25,
        "success_rate_pct": 30,
        "avg_bid_eth": 0.05,
    },
    "Realistic": {
        "market_share_pct": 25,
        "adjustment_rate_pct": 40,
        "success_rate_pct": 50,
        "avg_bid_eth": 0.10,
    },
    "Optimistic": {
        "market_share_pct": 40,
        "adjustment_rate_pct": 60,
        "success_rate_pct": 70,
        "avg_bid_eth": 0.15,
    },
}

# --- PAGE SETUP ---
st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon="⚡")

# --- XGA BRANDED CSS (DEEP CONTRAST) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* CORE BACKGROUNDS - PURE BLACK */
    .stApp { 
        background-color: #000000 !important; 
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }
    
    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a; 
        border-right: 1px solid #222; 
    }
    
    /* UNIFIED CARD STYLING (Glassmorphism) */
    .metric-card {
        background-color: rgba(20, 20, 20, 0.9);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 24px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
        margin-bottom: 16px;
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        border-color: #BB86FC; /* XGA Purple Glow */
        transform: translateY(-2px);
    }
    
    /* HIGH CONTRAST TEXT HIERARCHY */
    h1, h2, h3, h4, h5 { 
        color: #FFFFFF !important; 
        letter-spacing: -0.5px; 
        font-weight: 800; 
    }
    p, span, li, label, div { 
        color: #E0E0E0 !important; 
    }
    
    /* STREAMLIT NATIVE METRIC OVERRIDES */
    .stMetricLabel { 
        color: #888888 !important; 
        font-size: 0.9rem !important; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
    }
    .stMetricValue { 
        color: #FFFFFF !important; 
        font-family: 'Inter', sans-serif; 
        font-weight: 700; 
    }
    small { color: #888888 !important; }
    
    /* BRAND COLORS (TEXT CLASSES) */
    .money-green { 
        color: #00E676 !important; 
        font-weight: 800; 
        font-size: 2rem; 
        text-shadow: 0 0 15px rgba(0, 230, 118, 0.25);
    }
    .valuation-purple { 
        color: #BB86FC !important; /* XGA Neon Purple */
        font-weight: 800; 
        font-size: 2rem; 
        text-shadow: 0 0 15px rgba(187, 134, 252, 0.35);
    }
    .card-label { 
        color: #FFFFFF !important; 
        font-size: 0.85rem; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        margin-bottom: 8px;
        display: block;
    }
    .card-sub { 
        color: #888888 !important; 
        font-size: 0.85rem; 
        margin-top: 4px;
        display: block;
    }
    
    /* STREAMLIT WIDGET OVERRIDES */
    .stButton>button {
        background-color: #1a1a1a;
        color: #BB86FC !important;
        border: 1px solid #BB86FC;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #BB86FC;
        color: #000 !important;
        box-shadow: 0 0 15px rgba(187, 134, 252, 0.5);
    }
    
    /* DISCLAIMER */
    .disclaimer-box {
        background-color: rgba(255, 152, 0, 0.05);
        border: 1px solid #FF9800;
        border-radius: 8px;
        padding: 16px;
        font-size: 0.75rem;
        color: #FF9800 !important;
        margin-top: 24px;
        line-height: 1.4;
    }
    .disclaimer-box b { color: #FF9800 !important; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator != 0 else 0.0

def calculate_vault_revenue_eth(
    market_share: float,
    adjustment_rate: float,
    success_rate: float,
    avg_bid: float,
    kickback_rate: float,
    fold_share: float
) -> float:
    total_slots = BLOCKS_PER_YEAR * market_share
    adjustable = total_slots * adjustment_rate
    successful = adjustable * success_rate
    captured_value = successful * avg_bid
    net_revenue = captured_value * (1.0 - kickback_rate)
    return net_revenue * fold_share

def update_from_preset():
    selected = st.session_state["preset_selector"]
    if selected in SCENARIO_PRESETS:
        for key, value in SCENARIO_PRESETS[selected].items():
            st.session_state[key] = value

# --- INITIALIZATION ---
if "initialized" not in st.session_state:
    defaults = SCENARIO_PRESETS["Realistic"]
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state["eth_price"] = 3200.0
    st.session_state["pe_ratio"] = 20
    st.session_state["current_price"] = 0.75
    st.session_state["staked_pct"] = 50
    st.session_state["kickback_pct"] = 30
    st.session_state["fold_share_pct"] = 90
    st.session_state["staked_lock"] = False
    st.session_state["user_fold"] = 5000.0
    st.session_state["currency_mode"] = "USD ($)"
    st.session_state["initialized"] = True

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## ⚡ **XGA** | CONTROLS")
    
    # 1. Currency
    st.session_state["currency_mode"] = st.radio(
        "Base Currency", ["USD ($)", "ETH (Ξ)"], horizontal=True, label_visibility="collapsed"
    )
    is_usd = st.session_state["currency_mode"] == "USD ($)"
    sym = "$" if is_usd else "Ξ"

    # 2. Preset
    st.markdown("### SCENARIOS")
    st.selectbox(
        "Load Preset",
        options=list(SCENARIO_PRESETS.keys()) + ["Custom"],
        index=1,
        key="preset_selector",
        on_change=update_from_preset,
        label_visibility="collapsed"
    )
    
    st.markdown("---")

    # 3. Market Data
    st.markdown("### MARKET DATA")
    st.number_input("ETH Price ($)", min_value=0.0, step=50.0, key="eth_price")
    
    st.checkbox("Enforce 400k Launch Cap", key="staked_lock")
    if st.session_state["staked_lock"]:
        st.session_state["staked_pct"] = 20
        st.caption("🔒 Staking Capped at 20% (400k FOLD)")
    else:
        st.slider("Total % FOLD Staked", 0, 100, key="staked_pct")

    # GLOBAL USER INPUT
    st.markdown("---")
    st.markdown("### MY POSITION")
    st.number_input("FOLD Holdings", min_value=0.0, step=100.0, key="user_fold")

    st.markdown("---")

    # 4. Assumptions
    st.markdown("### PROTOCOL ASSUMPTIONS")
    st.slider("Market Share %", 0, 50, key="market_share_pct")
    st.slider("Adjustment Rate %", 0, 100, key="adjustment_rate_pct")
    st.slider("Success Rate %", 0, 100, key="success_rate_pct")
    st.number_input("Avg. Bid Delta (ETH)", min_value=0.0, format="%.3f", key="avg_bid_eth")

    st.markdown("---")

    # 5. Valuation
    st.markdown("### VALUATION")
    st.slider("Target P/E Ratio", 5, 60, key="pe_ratio")
    st.number_input("Ref. FOLD Price ($)", min_value=0.0, step=0.05, key="current_price")

    st.markdown("""
    <div class="disclaimer-box">
        <b>⚠️ DISCLAIMER</b><br>
        This tool is for educational purposes only. Not financial advice. Calculations based on unverified internal projections.
    </div>
    """, unsafe_allow_html=True)

# --- MAIN LOGIC ---

# 1. Normalize Inputs
ms = st.session_state["market_share_pct"] / 100.0
ar = st.session_state["adjustment_rate_pct"] / 100.0
sr = st.session_state["success_rate_pct"] / 100.0
eff_fill = ar * sr

kr = st.session_state["kickback_pct"] / 100.0 if "kickback_pct" in st.session_state else 0.30
fs = st.session_state["fold_share_pct"] / 100.0 if "fold_share_pct" in st.session_state else 0.90

staked_amt = FOLD_TOTAL_SUPPLY * (st.session_state["staked_pct"] / 100.0)

# 2. Calculate Revenue (ETH)
vault_rev_eth = calculate_vault_revenue_eth(
    ms, ar, sr, st.session_state["avg_bid_eth"], kr, fs
)

# 3. Currency Conversion Logic
eth_p = st.session_state["eth_price"]

if is_usd:
    vault_rev_display = vault_rev_eth * eth_p
    yield_per_token = safe_divide(vault_rev_display, staked_amt)
    implied_mcap = vault_rev_display * st.session_state["pe_ratio"]
    implied_price = safe_divide(implied_mcap, FOLD_TOTAL_SUPPLY)
    current_val_ref = st.session_state["current_price"]
else:
    vault_rev_display = vault_rev_eth
    yield_per_token = safe_divide(vault_rev_eth, staked_amt)
    implied_mcap = vault_rev_eth * st.session_state["pe_ratio"]
    implied_price = safe_divide(implied_mcap, FOLD_TOTAL_SUPPLY)
    current_val_ref = safe_divide(st.session_state["current_price"], eth_p)

# Yield Calc
div_yield = safe_divide(yield_per_token, current_val_ref)
upside = safe_divide(implied_price - current_val_ref, current_val_ref) * 100

# User Specifics
user_fold = st.session_state["user_fold"]
my_income_annual = user_fold * yield_per_token
my_portfolio_val = user_fold * implied_price


# --- UI LAYOUT: TABS ---
st.title(f"{PAGE_TITLE}")

tab_dash, tab_prof, tab_xga, tab_faq = st.tabs([
    "📊 DASHBOARD", 
    "👤 MY PORTFOLIO", 
    "🎁 XGA REWARDS", 
    "📚 RESOURCES"
])

# ==========================================
# TAB 1: DASHBOARD
# ==========================================
with tab_dash:
    st.markdown("#### PROTOCOL HEALTH")
    
    m1, m2, m3, m4 = st.columns(4)
    
    # Formatting Logic
    fmt = ",.2f" if is_usd else ",.4f"
    label_rev = f"{sym}{vault_rev_display/1_000_000:.1f}M" if is_usd else f"{sym}{vault_rev_display:,.0f}"
    
    # Using Custom Card HTML for consistency
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Vault Revenue (Annual)</span><br>
            <span class="money-green">{label_rev}</span><br>
            <span class="card-sub">Net to Insurance Vault</span>
        </div>
        """, unsafe_allow_html=True)
        
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Dividend / Token</span><br>
            <span class="money-green">{sym}{yield_per_token:{fmt}}</span><br>
            <span class="card-sub">Cash flow per Staked FOLD</span>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Implied Price</span><br>
            <span class="valuation-purple">{sym}{implied_price:{fmt}}</span><br>
            <span class="card-sub">Based on {st.session_state['pe_ratio']}x P/E</span>
        </div>
        """, unsafe_allow_html=True)
        
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Yield APY</span><br>
            <span class="valuation-purple">{div_yield:.1%}</span><br>
            <span class="card-sub">Upside: {upside:,.0f}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Sensitivity
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### SENSITIVITY: MARKET SHARE")
        st.caption("How price reacts to adoption")
        ms_range = range(5, 55, 5)
        prices = []
        for x in ms_range:
            r_eth = calculate_vault_revenue_eth(x/100, ar, sr, st.session_state["avg_bid_eth"], kr, fs)
            r_val = r_eth * eth_p if is_usd else r_eth
            mcap = r_val * st.session_state["pe_ratio"]
            prices.append(safe_divide(mcap, FOLD_TOTAL_SUPPLY))
        st.line_chart(pd.DataFrame({"Share %": ms_range, "Price": prices}).set_index("Share %"))

    with c2:
        st.markdown("#### 36-MONTH RAMP")
        st.caption("Projected revenue growth")
        ramp_data = []
        for m in [1, 12, 24, 36]:
            factor = np.interp(m, [1, 36], [0.1, 1.0])
            ramp_rev = vault_rev_display * factor
            ramp_data.append({"Month": m, "Revenue": ramp_rev})
        st.bar_chart(pd.DataFrame(ramp_data).set_index("Month"))

# ==========================================
# TAB 2: MY PORTFOLIO (RENAMED)
# ==========================================
with tab_prof:
    st.markdown(f"#### INCOME PROJECTOR ({user_fold:,.0f} FOLD)")
    
    st.markdown("""
    <div style="background-color: rgba(0, 230, 118, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #00E676; margin-bottom: 20px;">
        <span style="color: #00E676; font-weight: bold;">💸 SOURCE OF YIELD: CAPTIVE INSURANCE</span><br>
        <span style="color: #E0E0E0; font-size: 0.9rem;">
        This income is an insurance premium paid to you for staking FOLD in the <b>Captive Insurance Vault</b>. 
        You are underwriting the risk of XGA failure.
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">MONTHLY INCOME</span><br>
            <span class="money-green">{sym}{my_income_annual/12:{fmt}}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">ANNUAL INCOME</span><br>
            <span class="money-green">{sym}{my_income_annual:{fmt}}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">PROJECTED VALUE</span><br>
            <span class="valuation-purple">{sym}{my_portfolio_val:{fmt}}</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 3: XGA REWARDS (BRANDED)
# ==========================================
with tab_xga:
    st.markdown("#### XGA INCENTIVE CALCULATOR")
    
    # 1. Inputs
    col_x1, col_x2 = st.columns([1, 2])
    with col_x1:
        st.markdown("**TARGET MARKET CAP ($M)**")
        xga_mcap_input = st.slider(
            "Target MCAP", 
            min_value=100, max_value=900, value=300, step=50,
            label_visibility="collapsed"
        )
        xga_mcap = xga_mcap_input * 1_000_000
        xga_price = xga_mcap / XGA_TOTAL_SUPPLY
    
    with col_x2:
        st.markdown("**INCENTIVE PARAMETERS**")
        st.info("Applies **340% ROI** (3-month active participation) to your capital base.")

    st.divider()

    # 2. Math
    # Retroactive Airdrop (Fixed 5x)
    est_airdrop_tokens = user_fold * AIRDROP_RATIO
    est_airdrop_value = est_airdrop_tokens * xga_price
    
    # Active Incentive Value
    base_capital = user_fold * st.session_state["current_price"]
    est_incentive_value = base_capital * 3.40 # Fixed 340%

    # 3. Display
    xc1, xc2, xc3 = st.columns(3)
    
    with xc1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">IMPLIED XGA PRICE</span><br>
            <span class="valuation-purple">${xga_price:.2f}</span><br>
            <span class="card-sub">${xga_mcap_input}M Cap / 270M Supply</span>
        </div>
        """, unsafe_allow_html=True)
        
    with xc2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">AIRDROP VALUE</span><br>
            <span class="money-green">${est_airdrop_value:,.2f}</span><br>
            <span class="card-sub">{est_airdrop_tokens:,.0f} XGA (5x Fixed)</span>
        </div>
        """, unsafe_allow_html=True)
        
    with xc3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">INCENTIVE VALUE</span><br>
            <span class="money-green">${est_incentive_value:,.2f}</span><br>
            <span class="card-sub">340% ROI (3 Mo)</span>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🧮 The 'Implied Value' Explained"):
        st.markdown(f"""
        **The 'Option' Thesis:**
        Sam has mentioned FOLD has an "implied value of $5." This matches the math of the Airdrop:
        
        * **XGA Price:** ${xga_price:.2f} (at ${xga_mcap_input}M Cap)
        * **Ratio:** 5 XGA per FOLD
        * **Value:** 5 * ${xga_price:.2f} = **${5 * xga_price:.2f} Value per FOLD**
        
        This effectively acts as a "floor price" or call option for holders who receive the airdrop.
        """)

# ==========================================
# TAB 4: FAQ (CLEAN)
# ==========================================
with tab_faq:
    st.markdown("#### RESOURCES")
    
    with st.expander("❓ Is the Lido Partnership Confirmed?"):
        st.write("""
        **Status: Final Stages.**
        In the Oct 14th call, Sam stated Manifold is a "Launch Partner" for Lido V3. 
        Integration depends on the Lido V3 mainnet launch (expected with Pectra).
        """)
        
    with st.expander("❓ How does Commit-Boost work?"):
        st.write("""
        **It's a Sidecar.**
        Commit-Boost allows validators to run XGA alongside MEV-Boost.
        They get paid TWICE: once for the XGA slot, and once for the rest of the block (Flashbots).
        """)
        
    with st.expander("❓ What about the 270M XGA Supply?"):
        st.write("""
        **Tokenomics:**
        Sam confirmed 270M total supply for the XGA incentive token. 
        It is designed to bootstrap liquidity. 10% of Protocol Revenue goes to XGA holders/DAO, 
        while 90% goes to FOLD holders (Insurance Vault).
        """)

# --- FOOTER ---
st.markdown("---")
st.caption("XGA Valuation Engine v18.0 | Not Financial Advice")
