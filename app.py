import streamlit as st
import pandas as pd
import random
from datetime import datetime
import time

# Core Modules
from core.live_data import get_live_data, log_live_data, get_historical_data
from core.simulator import SimulationCore 
from utils.InsightEngine import generate_insights 

def main_dashboard():
    # --- 1. ENTERPRISE GLOBAL STYLING ---
    st.set_page_config(page_title="Skyline Aether - Enterprise DT", layout="wide", initial_sidebar_state="collapsed")

    st.markdown("""
        <style>
            .stApp {
                background: radial-gradient(circle at 20% 20%, #0e1525 0%, #05080d 100%);
                color: #e2e8f0;
            }
            [data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 12px !important;
                padding: 20px !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
            }
            .hero-value {
                font-size: 85px !important;
                font-weight: 800 !important;
                background: linear-gradient(180deg, #00f2ff 0%, #0072ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0px;
            }
            .label-text {
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                font-size: 0.75rem;
                font-weight: 700;
            }
            .led-green { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #00ff00; }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. INITIALIZE DT STATE ---
    if 'simulator_core' not in st.session_state: 
        st.session_state.simulator_core = SimulationCore("KIG-001", 85, 28)

    # --- 3. DATA & PHYSICS SYNC ---
    current_site_id = "KIG-001"
    
    # Get environmental context first
    current_hour = datetime.now().hour
    irradiance = max(0, 1000 * (1 - abs(current_hour - 13) / 4) + random.uniform(-50, 50)) if 9 <= current_hour <= 17 else 0.0
    
    # We pull live data with the "odometer" logic
    # Note: sim_net_kw from last step is used here
    prev_net_kw = st.session_state.get('last_net_kw', 0.0)
    live_data = get_live_data(current_site_id, sim_net_kw=prev_net_kw)

    # Run the Physics Step with Causal Separators
    sim_state = st.session_state.simulator_core.run_step(
        time_step_seconds=10, 
        irradiance=irradiance, 
        ambient_temp=live_data['ambient_temp'],
        current_load_kw=live_data['load_kw']
    )
    
    # Update Session State
    st.session_state.last_net_kw = sim_state['sim_net_kw']
    live_data.update(sim_state)
    system_insight = generate_insights(sim_state, live_data)

    # --- 4. MAIN UI LAYOUT ---
    h_left, h_right = st.columns([3, 1])
    with h_left:
        st.markdown(f"<h1><span class='led-green'></span> {current_site_id} Digital Twin</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#00f2ff; margin-top:-15px;'>MODE: {live_data['system_state']}</p>", unsafe_allow_html=True)

    # Hero Section
    st.markdown("---")
    hero_1, hero_2, hero_3 = st.columns([1, 2, 1])

    with hero_1:
        st.markdown('<p class="label-text">Generation</p>', unsafe_allow_html=True)
        st.metric("Solar Output", f"{live_data['sim_solar_kw']:.2f} kW")
        st.metric("Ambient Temp", f"{live_data['ambient_temp']:.1f}°C")

    with hero_2:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        st.markdown('<p class="label-text">Battery Storage Level</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="hero-value">{live_data["sim_soc"]:.1f}%</p>', unsafe_allow_html=True)
        st.progress(int(live_data["sim_soc"]))
        st.markdown('</div>', unsafe_allow_html=True)

    with hero_3:
        st.markdown('<p class="label-text">Demand</p>', unsafe_allow_html=True)
        st.metric("Total Load", f"{live_data['sim_load_kw']:.2f} kW")
        st.metric("Critical Ratio", f"{live_data['critical_load_ratio']*100:.0f}%")

    # EVIDENCE PANEL (Heartbeat)
    st.markdown("---")
    st.markdown('<p class="label-text">System Heartbeat & Causal Evidence</p>', unsafe_allow_html=True)
    
    ev_1, ev_2, ev_3, ev_4 = st.columns(4)
    ev_1.metric("Battery Core", f"{live_data['sim_temp']:.1f}°C")
    ev_2.metric("Odometer", f"{live_data['energy_throughput_kwh']:.2f} kWh")
    ev_3.metric("State of Health", f"{live_data['sim_soh']:.2f}%")
    
    # State Badge
    state_color = "#00ff00" if live_data['system_state'] == "Charging" else "#ff4b4b" if live_data['system_state'] == "Discharging" else "#888888"
    ev_4.markdown(f"""
        <div style="background:{state_color}22; border:1px solid {state_color}; border-radius:10px; padding:10px; text-align:center;">
            <p style="color:{state_color}; margin:0; font-weight:bold; font-size:14px;">{live_data['system_state']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Intelligence Panel
    st.info(f"🧠 {system_insight}")

    # Auto-Reload Script
    st.components.v1.html("<script>setTimeout(function(){ window.parent.location.reload(); }, 10000);</script>", height=0)

if __name__ == "__main__":
    main_dashboard()
