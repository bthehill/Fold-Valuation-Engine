import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any

# --- CONFIGURATION & CONSTANTS ---
PAGE_TITLE = "FOLD Valuation Engine"
BLOCKS_PER_YEAR = 2_628_000  # 7,200 slots/day * 365
FOLD_TOTAL_SUPPLY = 2_000_000

# XGA Constants
XGA_TOTAL_SUPPLY = 270_000_000
AIRDROP_RATIO = 5.0 # Fixed: 5 XGA per 1 FOLD

SCENARIO_PRESETS: Dict[str, Dict[str, float]] = {
    "Sam – Conservative": {
        "market_share_pct": 10,
        "adjustment_rate_pct": 25,
        "success_rate_pct": 30,
        "avg_bid_eth": 0.05,
    },
    "Sam – Realistic": {
        "market_share_pct": 25,
        "adjustment_rate_pct": 40,
        "success_rate_pct": 50,
        "avg_bid_eth": 0.10,
    },
    "Sam – Optimistic": {
        "market_share_pct": 40,
        "adjustment_rate_pct": 60,
        "success_rate_pct": 70,
        "avg_bid_eth": 0.15,
    },
}

# --- PAGE SETUP ---
st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon="⚡")

st.markdown("""
<style>
    /* Main Background - Pure Black */
    .stApp { background-color: #000000; }
    
    /* Sleek Cards */
    .metric-card {
        background-color: #121212;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    
    /* Text Overrides - High Visibility */
    h1, h2, h3, p, span, li, label { color: #ffffff !important; }
    .stMetricLabel { color: #cccccc !important; }
    .stMetricValue { color: #ffffff !important; }
    
    /* Custom Typography */
    .money-green { color: #00e676 !important; font-weight: bold; font-size: 1.8rem; }
    .valuation-blue { color: #2979ff !important; font-weight: bold; font-size: 1.8rem; }
    .card-label { color: #ffffff; font-size: 1.1rem; font-weight: 600; }
    .card-sub { color: #999999; font-size: 0.9rem; }
    
    /* Disclaimer */
    .disclaimer-box {
        background-color: #1a1a1a;
        border: 1px solid #ffb300;
        border-radius: 8px;
        padding: 15px;
        font-size: 0.8rem;
        color: #ffb300 !important;
        margin-top: 20px;
    }
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
    """Calculates annual ETH revenue flowing to the FOLD vault."""
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
    defaults = SCENARIO_PRESETS["Sam – Realistic"]
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
    st.title("⚡ Settings")
    
    # 1. Currency Toggle
    st.session_state["currency_mode"] = st.radio(
        "Currency", ["USD ($)", "ETH (Ξ)"], horizontal=True
    )
    is_usd = st.session_state["currency_mode"] == "USD ($)"
    sym = "$" if is_usd else "Ξ"

    # 2. Preset Selector
    st.selectbox(
        "Load Scenario",
        options=list(SCENARIO_PRESETS.keys()) + ["Custom"],
        index=1,
        key="preset_selector",
        on_change=update_from_preset
    )
    st.markdown("---")

    # 3. Market Environment
    st.header("1. Market Environment")
    st.number_input("ETH Price ($)", min_value=0.0, step=50.0, key="eth_price")
    
    st.checkbox("Lock Staked Amount (400k Cap)", key="staked_lock")
    if st.session_state["staked_lock"]:
        st.session_state["staked_pct"] = 20
        st.caption("✅ Locked at 20% (400k FOLD)")
    else:
        st.slider("% FOLD Staked", 0, 100, key="staked_pct")

    # GLOBAL USER FOLD INPUT
    st.markdown("👇 **Your Position (Drives All Tabs)**")
    st.number_input("My FOLD Balance", min_value=0.0, step=100.0, key="user_fold")

    st.markdown("---")

    # 4. XGA Assumptions
    st.header("2. XGA Adoption")
    st.slider("Market Share %", 0, 50, key="market_share_pct")
    st.slider("Adjustment Rate %", 0, 100, key="adjustment_rate_pct")
    st.slider("Success Rate %", 0, 100, key="success_rate_pct")
    st.number_input("Avg. Bid Delta (ETH)", min_value=0.0, format="%.3f", key="avg_bid_eth")

    st.markdown("---")

    # 5. Valuation
    st.header("3. Valuation")
    st.slider("Target P/E Ratio", 5, 60, key="pe_ratio")
    st.number_input("Ref. FOLD Price ($)", min_value=0.0, step=0.05, key="current_price")

    st.markdown("""
    <div class="disclaimer-box">
        <b>⚠️ DISCLAIMER</b><br>
        Not financial advice. Based on hypothetical models.
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
st.title(f"⚡ {PAGE_TITLE}")

tab_dash, tab_prof, tab_xga, tab_faq = st.tabs([
    "📊 Market Dashboard", 
    "👤 My Portfolio", 
    "🎁 XGA Rewards", 
    "📚 FAQ & Resources"
])

# ==========================================
# TAB 1: DASHBOARD
# ==========================================
with tab_dash:
    st.markdown("### 📈 Protocol Health")
    
    m1, m2, m3, m4 = st.columns(4)
    
    # Formatting Logic: 4 decimals for ETH, 2 for USD
    fmt = ",.2f" if is_usd else ",.4f"
    
    label_rev = f"{sym}{vault_rev_display/1_000_000:.1f}M" if is_usd else f"{sym}{vault_rev_display:,.0f}"
    
    m1.metric("Annual Vault Revenue", label_rev, help="Net revenue after kickbacks")
    
    # Applied special formatting to these two:
    m2.metric("Dividend Per Staked Token", f"{sym}{yield_per_token:{fmt}}", help="Cash flow to STAKED tokens")
    m3.metric("Implied FOLD Price", f"{sym}{implied_price:{fmt}}", help=f"Based on {st.session_state['pe_ratio']}x P/E")
    
    m4.metric(f"Upside vs Current", f"{upside:,.0f}%", f"Yield: {div_yield:.1%}")

    st.caption(f"**Stats:** Effective Fill: `{eff_fill:.1%}` | Staked: `{staked_amt:,.0f}` FOLD")
    st.divider()

    # Sensitivity
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Market Share Sensitivity")
        ms_range = range(5, 55, 5)
        prices = []
        for x in ms_range:
            r_eth = calculate_vault_revenue_eth(x/100, ar, sr, st.session_state["avg_bid_eth"], kr, fs)
            r_val = r_eth * eth_p if is_usd else r_eth
            mcap = r_val * st.session_state["pe_ratio"]
            prices.append(safe_divide(mcap, FOLD_TOTAL_SUPPLY))
        st.line_chart(pd.DataFrame({"Share %": ms_range, "Price": prices}).set_index("Share %"))

    with c2:
        st.subheader("📊 36-Month Ramp")
        ramp_data = []
        for m in [1, 12, 24, 36]:
            factor = np.interp(m, [1, 36], [0.1, 1.0])
            ramp_rev = vault_rev_display * factor
            ramp_data.append({"Month": m, "Revenue": ramp_rev})
        st.bar_chart(pd.DataFrame(ramp_data).set_index("Month"))

# ==========================================
# TAB 2: MY PROFILE
# ==========================================
with tab_prof:
    st.header("👤 Personal Income Projector")
    st.info(f"Projections based on holding **{user_fold:,.0f} FOLD** (set in Sidebar).")
    
    st.markdown("""
    <div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; border-left: 5px solid #00e676; margin-bottom: 20px;">
        <b>💸 Source of Funds: Providing Captive Insurance</b><br>
        This income is an insurance premium paid to you for staking FOLD in the Captive Insurance Vault. 
        You are underwriting the risk of the XGA Relay.
    </div>
    """, unsafe_allow_html=True)
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    # Use same formatting precision here for consistency
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Monthly Passive Income</span><br>
            <span class="money-green">{sym}{my_income_annual/12:{fmt}}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Annual Passive Income</span><br>
            <span class="money-green">{sym}{my_income_annual:{fmt}}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Projected Portfolio Value</span><br>
            <span class="valuation-blue">{sym}{my_portfolio_val:{fmt}}</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 3: XGA REWARDS (UPDATED)
# ==========================================
with tab_xga:
    st.header("🎁 XGA Incentive Calculator")
    st.markdown("Estimates based on Sam Bacha's target metrics.")
    
    # 1. Inputs
    col_x1, col_x2 = st.columns([1, 2])
    with col_x1:
        st.markdown("#### 1. Market Cap Settings")
        xga_mcap_input = st.slider(
            "XGA Target Market Cap ($M)", 
            min_value=100, max_value=900, value=300, step=50,
            help="Sam estimated between $300M - $600M start."
        )
        xga_mcap = xga_mcap_input * 1_000_000
        xga_price = xga_mcap / XGA_TOTAL_SUPPLY
    
    with col_x2:
        st.markdown("#### 2. Incentive Settings")
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
            <span class="card-label">Implied XGA Price</span><br>
            <span class="valuation-blue">${xga_price:.2f}</span><br>
            <span class="card-sub">${xga_mcap_input}M Cap / 270M Supply</span>
        </div>
        """, unsafe_allow_html=True)
        
    with xc2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Retroactive Airdrop Value</span><br>
            <span class="money-green">${est_airdrop_value:,.2f}</span><br>
            <span class="card-sub">{est_airdrop_tokens:,.0f} XGA Tokens (5x Fixed)</span>
        </div>
        """, unsafe_allow_html=True)
        
    with xc3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="card-label">Active Incentive Value</span><br>
            <span class="money-green">${est_incentive_value:,.2f}</span><br>
            <span class="card-sub">340% ROI on Capital (3 Mo)</span>
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
# TAB 4: FAQ (NEW)
# ==========================================
with tab_faq:
    st.header("📚 FAQ & Resources")
    
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
        
    with st.expander("❓ Why 36 Months?"):
        st.write("""
        **Market Liquidity.**
        Even if tech is ready, Searchers (traders) need time to build bots to buy these new 'Future Slots'.
        Sam models utilization ramping from 10% to 86% over 3 years.
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
st.caption("Community Edition v16.1 | Disclaimer: Hypothetical model for exploratory purposes. Not financial advice.")