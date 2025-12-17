import streamlit as st
import pandas as pd
import random
from datetime import datetime
import time

# Core Modules
from core.live_data import get_live_data, log_live_data, get_historical_data
from core.simulator import SimulationCore 
from utils.InsightEngine import generate_insights 

# --- 1. ENTERPRISE GLOBAL STYLING (The "Secret Sauce") ---
st.set_page_config(page_title="Skyline Aether - Enterprise DT", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Deep radial background for depth */
        .stApp {
            background: radial-gradient(circle at 20% 20%, #0e1525 0%, #05080d 100%);
            color: #e2e8f0;
        }
        
        /* Glassmorphism Cards */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
        }

        /* Hero Text Gradient */
        .hero-value {
            font-size: 85px !important;
            font-weight: 800 !important;
            background: linear-gradient(180deg, #00f2ff 0%, #0072ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }

        /* Section Labels */
        .label-text {
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        
        /* Status LED pulse */
        .led-green {
            height: 10px; width: 10px;
            background-color: #00ff00;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 10px #00ff00;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA & LOGIC ---
if 'simulator_core' not in st.session_state: 
    st.session_state.simulator_core = SimulationCore("KIG-001", 50, 30)

current_site_id = "KIG-001"
live_data = get_live_data(current_site_id)

# Weather/Sim Logic
current_hour = datetime.now().hour
irradiance = max(0, 1000 * (1 - abs(current_hour - 13) / 4) + random.uniform(-50, 50)) if 9 <= current_hour <= 17 else 0.0
ambient_temp = 25.0 + random.uniform(-2, 3)

sim_state = st.session_state.simulator_core.run_step(
    time_step_seconds=10, 
    irradiance=irradiance, 
    ambient_temp=ambient_temp,
    current_load_kw=live_data['load_kw']
)
system_insight = generate_insights(sim_state, live_data)
live_data.update(sim_state)
log_live_data(current_site_id, live_data)

# --- 3. MAIN UI LAYOUT ---
# Header Row
h_left, h_right = st.columns([3, 1])
with h_left:
    st.markdown(f"<h1><span class='led-green'></span> {current_site_id} Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00f2ff; margin-top:-15px;'>SYSTEM STATUS: OPTIMAL</p>", unsafe_allow_html=True)

# Hero Section: 3-Column Grid
st.markdown("---")
hero_1, hero_2, hero_3 = st.columns([1, 2, 1])

with hero_1:
    st.markdown('<p class="label-text">Supply / Generation</p>', unsafe_allow_html=True)
    st.metric("Solar Output", f"{live_data['solar_kw']:.2f} kW")
    st.metric("Grid Feedback", "0.00 kW")

with hero_2:
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    st.markdown('<p class="label-text">Battery Storage Level</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="hero-value">{live_data["battery_soc"]:.1f}%</p>', unsafe_allow_html=True)
    st.progress(int(live_data["battery_soc"]))
    st.markdown('</div>', unsafe_allow_html=True)

with hero_3:
    st.markdown('<p class="label-text">Demand / Consumption</p>', unsafe_allow_html=True)
    st.metric("Total Load", f"{live_data['load_kw']:.2f} kW", delta_color="inverse")
    st.metric("Critical Systems", "99.9%")

# Intelligence & Health Row
st.markdown("---")
st.markdown('<p class="label-text">Digital Twin Predictive Maintenance</p>', unsafe_allow_html=True)

# Intelligence Panel
with st.container():
    i_col, v_col = st.columns([0.8, 0.2])
    i_col.info(f"🧠 {system_insight}")
    if v_col.button("🔊 Listen", use_container_width=True):
        st.components.v1.html(f'<script>window.speechSynthesis.speak(new SpeechSynthesisUtterance("{system_insight}"));</script>', height=0)

# Predictive Stats
p_cols = st.columns(4)
p_cols[0].metric("Pred. SOC (1hr)", f"{live_data.get('sim_soc', 0):.1f}%")
p_cols[1].metric("Core Temp", f"{live_data.get('sim_temp', 0):.1f}°C")

soh = live_data.get('sim_soh', 100.0)
p_cols[2].metric("State of Health", f"{soh:.2f}%")

# Smart Years-to-Retirement Logic
loss = (100 - soh)
years = ((soh - 80) / (loss/100) * 10) / (3600*24*365) if loss > 0 else 12.5
p_cols[3].metric("Est. Useful Life", f"{years:.1f} Yrs")

# Auto-Reload Script
st.components.v1.html("<script>setTimeout(function(){ window.parent.location.reload(); }, 10000);</script>", height=0)