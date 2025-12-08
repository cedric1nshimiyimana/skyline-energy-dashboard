# skyline_aether_phase2_dynamic.py — PHASE 2: DYNAMIC, STATEFUL, & CREATIVE EXPANSION

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np # Used for efficient, vectorized operations
import random
from datetime import datetime, timedelta
import time
import math

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Skyline Aether: Phase 2",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. DATA GENERATION & MOCK API (Vectorized Fix) ---
# Seed for consistent initial state
random.seed(42)

@st.cache_data(ttl=120) # Cache historical data for 2 minutes
def generate_history_data():
    """Generates 30 days of mock historical energy data using vectorized Pandas operations."""
    end_date = datetime.now().date()
    dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)][::-1]
    
    # 1. Create the base data arrays
    solar_kwh_array = np.array([round(random.uniform(15, 25) + (i / 10), 1) for i in range(30)])
    load_kwh_array = np.array([round(random.uniform(7, 10), 1) for i in range(30)])
    
    # 2. Build the DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Solar_KWH': solar_kwh_array,
        'Load_KWH': load_kwh_array,
    })
    
    # 3. FIX: Use vectorized operations to calculate derived columns
    # Grid_KWH calculation: MAX(0, Load - Solar + Random Noise)
    random_noise = np.array([random.uniform(-2, 2) for _ in range(30)])
    
    # Calculate the potential grid draw/export, then apply max(0, x) to get Grid_KWH (import)
    # The .apply() is used here to correctly apply the round and max functions element-wise
    df['Grid_KWH'] = (df['Load_KWH'] - df['Solar_KWH'] + random_noise).apply(lambda x: round(max(0, x), 1))
    
    # The rest of your derived columns (vectorized)
    df['Battery_KWH'] = (df['Solar_KWH'] * 0.4) - (df['Load_KWH'] * 0.1) 
    df['Net_KWH'] = df['Solar_KWH'] - df['Load_KWH']
    
    return df

def generate_live_data():
    """Generates mock live data, simulating an MQTT feed update."""
    solar_kw = round(random.uniform(0.1, 7.5), 2)
    load_kw = round(random.uniform(1.5, 4.0), 2)
    
    # Complex battery logic based on solar and load
    if solar_kw > load_kw + 1: # High solar surplus -> charge
        battery_kw = round(random.uniform(1.0, 4.0), 2) * -1
    elif load_kw > solar_kw + 1: # High load deficit -> discharge
        battery_kw = round(random.uniform(1.0, 3.5), 2)
    else: # Balanced or low power -> idle
        battery_kw = round(random.uniform(-0.5, 0.5), 2)
        
    grid_kw = round(max(0.0, load_kw - solar_kw - battery_kw), 2)
    
    # State-dependent SOC (mock)
    if 'battery_soc' not in st.session_state:
        st.session_state.battery_soc = random.randint(50, 95)
    
    if battery_kw < -0.1: # Charging
        st.session_state.battery_soc = min(100, st.session_state.battery_soc + 1)
    elif battery_kw > 0.1: # Discharging
        st.session_state.battery_soc = max(10, st.session_state.battery_soc - 1)
        
    # Mock lifetime counters
    if 'lifetime_kwh' not in st.session_state:
        st.session_state.lifetime_kwh = 121742
        st.session_state.co2_saved_kg = 123.4
        st.session_state.solar_coins = 20.0
        st.session_state.today_kwh = 0.0

    st.session_state.today_kwh += solar_kw * 0.05 # Mock small increment
    st.session_state.lifetime_kwh += solar_kw * 0.05
    st.session_state.co2_saved_kg += solar_kw * 0.005
    st.session_state.solar_coins += solar_kw * 0.001
    
    return {
        'solar_kw': solar_kw,
        'battery_kw': battery_kw,
        'load_kw': load_kw,
        'grid_kw': grid_kw,
        'battery_soc': st.session_state.battery_soc,
        'today_kwh': st.session_state.today_kwh,
        'lifetime_kwh': st.session_state.lifetime_kwh,
        'co2_saved_kg': st.session_state.co2_saved_kg,
        'solar_coins': st.session_state.solar_coins,
    }

# --- 3. STATE INITIALIZATION ---
# This must be run on every script rerun, but the 'if not in' ensures it only initializes once per session.
if 'data' not in st.session_state:
    st.session_state.data = generate_live_data()
if 'history_df' not in st.session_state:
    # This line is where the error occurred, now fixed in the function above
    st.session_state.history_df = generate_history_data() 

# --- 4. CSS & ANIMATIONS (Modularized) ---
def load_custom_css():
    """Loads all custom CSS for the Aether theme."""
    st.markdown("""
    <style>
    /* APP BACKGROUND */
    .stApp {background: radial-gradient(circle at 50% 30%, #0a1a3a 0%, #000 100%); color: white; overflow-x: hidden; transition: 0.5s;}

    /* HEADER */
    h1 {font-size:4rem;font-weight:900;background:linear-gradient(90deg,#00ffff,#ff9f1c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin:20px 0;cursor:pointer;}

    /* GLOW CARDS */
    .glow-card {background: rgba(10,30,60,0.6);backdrop-filter: blur(12px);border-radius:20px;padding:20px;border:1px solid rgba(0,255,255,0.2);box-shadow:0 0 30px rgba(0,255,255,0.15);transition:0.3s;}
    .big-num {font-size:4.2rem;font-weight:900;text-align:center;color:#00ffff;text-shadow:0 0 20px #00ffff;}
    .label {font-size:1.1rem;color:#88ffff;text-align:center;}
    .lifetime {font-size:2.4rem;color:#ff9f1c;font-weight:900;text-shadow:0 0 20px #ff9f1c;text-align:center;}
    .coin-label {color:#ff9f1c;}

    /* ENERGY FLOW */
    @keyframes flow {0%,100%{opacity:0.6;transform:translateX(0)}50%{opacity:1;}}
    .flow-arrow {font-size:4rem;animation: flow 2.5s infinite;display:inline-block;cursor:pointer;transition:0.2s;margin:0 10px;}
    .arrow-charge {color:#00ffff;} /* Battery charging */
    .arrow-discharge {color:#ff9f1c;} /* Battery discharging */
    .arrow-grid-out {color:#FFD700;} /* Exporting to Grid (Gold) */
    .arrow-grid-in {color:#FF0000;} /* Importing from Grid (Red Alert) */

    /* BATTERY RADIAL PULSE */
    @keyframes pulse {0%,100%{opacity:0.7}50%{opacity:1}}
    .pulse {animation:pulse 2s infinite;}

    /* SPARKS */
    @keyframes spark {0%{opacity:0}50%{opacity:1;transform:scale(1.3)}100%{opacity:0}}
    .spark {color:#ffff00;font-size:2.5rem;animation:spark 0.5s infinite;display:inline-block;margin:0 5px;}

    /* TREES / CO2 */
    .tree {color:#32CD32;font-size:2rem;display:inline-block;margin:0 2px;}
    
    /* PLOTLY THEME ADJUSTMENTS */
    .stPlotlyChart {border-radius:20px; box-shadow:0 0 20px rgba(0,255,255,0.1); padding: 10px;}

    /* TAB FIX */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1.2rem; font-weight:700; color:#00ffff;
    }
    </style>
    """, unsafe_allow_html=True)
load_custom_css()

# --- 5. DYNAMIC COMPONENTS (Logic Functions) ---
def render_dynamic_flow(data):
    """Renders the complex energy flow diagram based on live data."""
    solar_kw = data['solar_kw']
    battery_kw = data['battery_kw']
    load_kw = data['load_kw']
    grid_kw = data['grid_kw']
    
    # 5.1 FLOW LOGIC
    solar_to_battery = battery_kw < -0.1
    solar_to_load = solar_kw > 0.1 and load_kw > 0.1
    grid_export = solar_kw > load_kw + abs(battery_kw) + 0.1 and abs(grid_kw) > 0.1 # True export logic
    grid_import = grid_kw > 0.1
    
    # 5.2 RENDER FLOW
    st.markdown("<h2 style='text-align:center; color:#00ffff; margin:40px 0 20px;'>Energy Flow • Dynamic View</h2>", unsafe_allow_html=True)
    
    flow_cols = st.columns([1, 0.5, 2, 0.5, 1])
    with flow_cols[0]: # Solar Icon
        st.markdown(f"<p style='font-size:5rem; text-align:center;'>☀️</p>", unsafe_allow_html=True)
        if solar_kw > 5:
            st.markdown("<p style='text-align:center;'><span class='spark'>⚡</span> High Production</p>", unsafe_allow_html=True)
    
    # Arrow 1: Solar to System
    with flow_cols[1]:
        arrow_style = "arrow-charge"
        st.markdown(f"<span class='flow-arrow {arrow_style}' title='Solar Generation'>{solar_kw:.1f} kW →</span>", unsafe_allow_html=True)

    # Central Hub (Load/Battery/Grid Interactions)
    with flow_cols[2]:
        # 5.3 BATTERY + LOAD ROW
        load_battery_cols = st.columns([1, 1, 1])
        
        # Grid/Battery Status (Above)
        with load_battery_cols[0]:
            if grid_import:
                st.markdown(f"<p style='text-align:center; color:#FF0000;'>**Grid IN** ({grid_kw:.1f} kW)</p>", unsafe_allow_html=True)
            elif grid_export:
                 st.markdown(f"<p style='text-align:center; color:#FFD700;'>**Grid OUT** ({abs(grid_kw):.1f} kW)</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align:center; color:#88ffff;'>Grid Idle</p>", unsafe_allow_html=True)

        with load_battery_cols[1]:
            st.markdown(f"<p style='font-size:5rem; text-align:center;'>🏠</p>", unsafe_allow_html=True)
        
        with load_battery_cols[2]:
            st.markdown(f"<p style='font-size:5rem; margin-top:-20px;'>🔋</p>", unsafe_allow_html=True)
            charge_state = "Charging" if battery_kw < -0.1 else ("Discharging" if battery_kw > 0.1 else "Idle")
            st.markdown(f"<p style='text-align:center; color:#48cae4;'>{charge_state} ({abs(battery_kw):.1f} kW)</p>", unsafe_allow_html=True)
            
        # 5.4 ARROWS BETWEEN BATTERY & LOAD (Below)
        st.markdown("<div style='display:flex; justify-content:space-around;'>", unsafe_allow_html=True)
        
        # Determine the primary source for the load
        if grid_import:
            flow_desc = f"Grid → Load ({load_kw:.1f} kW)"
            flow_style = "arrow-grid-in"
        elif battery_kw > 0.1:
            flow_desc = f"Battery → Load ({load_kw:.1f} kW)"
            flow_style = "arrow-discharge"
        elif solar_to_load:
             flow_desc = f"Solar → Load ({load_kw:.1f} kW)"
             flow_style = "arrow-charge"
        else:
            flow_desc = "Load Idle"
            flow_style = ""
            
        st.markdown(f"<span class='flow-arrow {flow_style}' style='font-size:2rem;' title='Primary Load Source'>{flow_desc}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_kpis(data):
    """Renders the Lifetime and CO2 cards."""
    co2_saved_kg = data['co2_saved_kg']
    solar_coins = data['solar_coins']
    lifetime_kwh = data['lifetime_kwh']
    today_kwh = data['today_kwh']
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.markdown(f"<div class='lifetime'>{today_kwh:.1f} kWh</div><div style='text-align:center; color:#88ffaa'>Produced Today</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"<div class='lifetime'>{lifetime_kwh:,.0f} kWh</div><div style='text-align:center; color:#ffdd88'>Lifetime Total</div>", unsafe_allow_html=True)
    with col_c:
        st.markdown(f"<div class='lifetime'>{solar_coins:.2f}</div><div style='text-align:center; color:#00ffff'>Solar Coins</div>", unsafe_allow_html=True)
    with col_d:
        # 5 kg of CO2 saved per mock tree planted
        num_trees = int(co2_saved_kg // 5)
        tree_html = "".join(["<span class='tree'>🌳</span>" for _ in range(min(5, num_trees))])
        st.markdown(f"<div class='lifetime'>{co2_saved_kg:.1f} kg</div><div style='text-align:center; color:#32CD32'>CO₂ Saved {tree_html}</div>", unsafe_allow_html=True)


# --- 6. PAGE FUNCTIONS (Multi-Tab Structure) ---
def page_dashboard(data):
    """The main Dashboard view."""
    
    st.markdown("<h3 style='text-align:center; color:#00ffff; margin-top:-20px;'>Live from Kigali • Cerbo GX MK2 • Phase 2 Dynamic</h3>", unsafe_allow_html=True)
    
    # 6.1 TOP CARDS
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        st.markdown(f"<div class='glow-card pulse'><div class='big-num'>{data['solar_kw']:.2f}<small>kW</small></div><div class='label'>Solar Now</div></div>", unsafe_allow_html=True)
    with c2:
        pulse_class = "pulse" if 20 < data['battery_soc'] < 95 else ""
        st.markdown(f"<div class='glow-card {pulse_class}'><div class='big-num'>{data['battery_soc']}%</div><div class='label'>Battery SOC</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='glow-card pulse'><div class='big-num'>{data['load_kw']:.2f}<small>kW</small></div><div class='label'>House Load</div></div>", unsafe_allow_html=True)
    with c4:
        # Conditional color/title for Grid
        grid_status = "Grid IN" if data['grid_kw'] > 0.1 else ("Grid OUT" if data['grid_kw'] < -0.1 else "Grid IDLE")
        grid_color = "#FF0000" if data['grid_kw'] > 0.1 else ("#00ff88" if data['grid_kw'] < -0.1 else "#88ffff")
        st.markdown(f"<div class='glow-card'><div class='big-num' style='color:{grid_color};'>{abs(data['grid_kw']):.2f}<small>kW</small></div><div class='label'>{grid_status}</div></div>", unsafe_allow_html=True)
    
    # 6.2 DYNAMIC ENERGY FLOW
    render_dynamic_flow(data)
    
    # 6.3 LIFETIME KPIS
    st.markdown("---")
    render_kpis(data)
    st.markdown("---")

    # 6.4 RADIAL BATTERY GAUGE
    col_left, col_gauge, col_right = st.columns([1, 1, 1])
    with col_gauge:
        battery_soc = data['battery_soc']
        # SVG for an animated radial gauge
        battery_svg = f"""
        <svg width="200" height="200" style="display:block; margin:auto;">
            <circle cx="100" cy="100" r="90" stroke="#00ffff" stroke-width="15" fill="none" stroke-opacity="0.2"/>
            <circle cx="100" cy="100" r="90" stroke="#00ffff" stroke-width="15" fill="none"
                    stroke-dasharray="{2*math.pi*90}" stroke-dashoffset="{2*math.pi*90*(1-battery_soc/100)}"
                    stroke-linecap="round" style="transform:rotate(-90deg); transform-origin:center; animation: pulse 2s infinite;"/>
            <text x="100" y="115" text-anchor="middle" font-size="36" fill="#00ffff">{battery_soc}%</text>
            <text x="100" y="150" text-anchor="middle" font-size="16" fill="#88ffff">State of Charge</text>
        </svg>
        """
        st.markdown(battery_svg, unsafe_allow_html=True)


def page_history(df):
    """The historical data analysis view."""
    st.header("🌌 Historical Energy Trends")
    st.markdown("Review your 30-day performance.")
    
    # 6.5 INTERACTIVE PLOTLY CHART
    st.subheader("30-Day Daily Energy Balance (kWh)")
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df['Date'], y=df['Solar_KWH'], mode='lines', name='Solar Generated', line=dict(color='#00ff88', width=3)))
    fig.add_trace(go.Bar(x=df['Date'], y=df['Load_KWH'], name='House Load', marker_color='#ff9f1c', opacity=0.7))
    fig.add_trace(go.Bar(x=df['Date'], y=df['Grid_KWH'], name='Grid Used (Import)', marker_color='#FF0000', opacity=0.9))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color="#88ffff",
        height=500,
        xaxis_title="Date",
        yaxis_title="Energy (kWh)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='rgba(136, 255, 255, 0.2)'),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Data Table")
    st.dataframe(df.set_index('Date').sort_index(ascending=False), use_container_width=True)


def page_aether_coins(data):
    """Gamification and Rewards System."""
    st.header("💰 Aether Coin Exchange")
    st.markdown("Aether Coins are rewarded for self-sufficiency and high solar production. You can use them for virtual system upgrades.")
    
    st.subheader(f"Your Balance: **{data['solar_coins']:.2f} AETHER** 🪙")
    
    col_buy, col_stats = st.columns(2)
    
    with col_buy:
        st.markdown("<div class='glow-card'><h4 style='color:#00ffff;'>Aether Staking Protocol</h4>", unsafe_allow_html=True)
        st.markdown("Lock your coins to earn passive rewards. Expected APY: **12.5%**.")
        
        # Use a key to ensure widget state is managed in session_state
        stake_amount = st.slider("Amount to Stake", min_value=0.0, max_value=data['solar_coins'], step=0.01, key="stake_slider")
        
        if st.button("🚀 Confirm Stake", use_container_width=True, key="stake_btn"):
            if stake_amount > 0:
                st.session_state.data['solar_coins'] -= stake_amount
                st.success(f"Successfully staked **{stake_amount:.2f} AETHER**. New Balance: {st.session_state.data['solar_coins']:.2f}")
                st.rerun() # Rerun to update the balance immediately
            else:
                st.error("Stake amount must be greater than zero.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_stats:
        st.markdown("<div class='glow-card'><h4 style='color:#ff9f1c;'>Community Rankings (Mock)</h4>", unsafe_allow_html=True)
        
        ranking_data = [
            ("Aether_User_001", 5432.1), ("You", data['solar_coins']), ("Solar_God_X", 3122.9),
            ("Kigali_Node_7", 1980.5), ("EcoWarrior", 1000.0), ("Phase1_Dev", 50.0)
        ]
        
        ranking_df = pd.DataFrame(ranking_data, columns=['User', 'AETHER Balance'])
        ranking_df['Rank'] = ranking_df['AETHER Balance'].rank(method='dense', ascending=False).astype(int)
        ranking_df = ranking_df.sort_values('Rank').set_index('Rank')
        
        # Highlight the current user
        def highlight_you(s):
            is_you = s.index.get_level_values('User') == 'You'
            return ['background-color: #00ffff33' if v else '' for v in is_you]

        st.dataframe(ranking_df.style.apply(highlight_you, axis=1), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def page_diagnostics():
    """The hidden Developer/Diagnostics Panel, now a visible tab."""
    st.header("⚙️ System Diagnostics & Control")
    st.markdown("This panel simulates access to the Cerbo GX settings. Changes here would persist across reruns (mock).")
    
    col_d1, col_d2 = st.columns(2)
    
    # Use session_state to hold control values persistently
    if 'min_soc_setting' not in st.session_state: st.session_state.min_soc_setting = 20
    if 'max_charge_limit' not in st.session_state: st.session_state.max_charge_limit = 80
    if 'load_priority' not in st.session_state: st.session_state.load_priority = "Solar First"

    def apply_settings_callback():
        st.info(f"Settings Applied! Min SOC: {st.session_state.min_soc_setting}%, Max Charge: {st.session_state.max_charge_limit}A.")

    with col_d1:
        st.subheader("Battery Management")
        st.slider("Min Discharge SOC (%)", 10, 50, key='min_soc_setting', help="Minimum State of Charge before the system switches to Grid/Generator.")
        st.slider("Max Solar Charge Rate (A)", 10, 100, key='max_charge_limit')
        
        st.button("Apply Battery Settings", type="primary", on_click=apply_settings_callback)

    with col_d2:
        st.subheader("Grid & Load Control")
        st.radio("Load Power Source Priority", ["Solar First", "Battery First", "Grid Always"], key='load_priority')
        
        st.checkbox("Enable Automatic Grid Export (Sell)", value=True, help="Allows excess solar power to be sold back to the grid.")
        st.text_area("System Log Viewer", "18:15: Battery SOC 85%\n18:10: Solar production peaking at 7.2 kW\n18:05: System self-test OK. (Log is mock/static in this demo)", height=150)


# --- 7. MAIN APP EXECUTION ---
st.markdown("<h1 id='skyline-logo'>SKYLINE AETHER: GENESIS</h1>", unsafe_allow_html=True)

# Main Navigation
tab_dashboard, tab_history, tab_coins, tab_diag = st.tabs(["Dashboard", "History", "Aether Coins", "Diagnostics"])

with tab_dashboard:
    page_dashboard(st.session_state.data)

with tab_history:
    page_history(st.session_state.history_df)

with tab_coins:
    page_aether_coins(st.session_state.data)

with tab_diag:
    page_diagnostics()

# --- 8. LIVE DATA REFRESH MECHANISM (Proper Streamlit Pattern) ---
st.markdown("---")
col_refresh, col_status = st.columns([1, 4])

def update_data_and_rerun():
    """Callback function to update state and trigger a rerun."""
    st.session_state.data = generate_live_data()
    # st.rerun() is implicitly called when a button with an on_click callback is pressed

with col_refresh:
    # Use on_click callback for cleaner state management and implicit rerun
    st.button("Simulate Data Update", type="secondary", use_container_width=True, on_click=update_data_and_rerun)

# Status and Footer
with col_status:
    st.markdown(f"<p style='text-align:right; color:#00ffff; margin-top:10px; font-size:1.2rem;'>Last Updated: **{datetime.now().strftime('%H:%M:%S')}** • Phase 2 Dynamic Demo</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#00ffff; font-size:1rem;'>Made in Rwanda • Powered by Sun • Controlled by Aether</p>", unsafe_allow_html=True)