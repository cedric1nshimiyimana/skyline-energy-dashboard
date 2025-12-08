# skyline_aether_genesis_phase1.py — FULLY STATIC + ANIMATED MASTERPIECE
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import math

st.set_page_config(page_title="Skyline Aether: Genesis Edition", layout="wide", initial_sidebar_state="collapsed")

# ==================== FAKE STATIC DATA (PHASE 1) ====================
solar_kw = 5.72
battery_kw = -3.1
load_kw = 2.9
grid_kw = 0.0
battery_soc = 83
today_kwh = 20.3
lifetime_kwh = 121_742
co2_saved_kg = 123.4
solar_coins = 20

# 7-day chart
dates = [(datetime.now() - timedelta(days=i)).strftime("%a %d") for i in range(6,-1,-1)]
solar_daily = [13.1, 15.9, 17.2, 18.8, 16.5, 19.4, 19.4]
battery_daily = [8.0, 8.3, 8.1, 8.6, 8.2, 8.0, 7.7]
grid_daily = [0.0]*7

# ==================== CSS & ANIMATIONS ====================
st.markdown("""
<style>
/* APP BACKGROUND */
.stApp {background: radial-gradient(circle at 50% 30%, #0a1a3a 0%, #000 100%); color: white; overflow-x: hidden; transition: background 2s ease;}

/* HEADER */
h1 {font-size:4rem;font-weight:900;background:linear-gradient(90deg,#00ffff,#ff9f1c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin:20px 0;cursor:pointer;}

/* GLOW CARDS */
.glow-card {background: rgba(10,30,60,0.6);backdrop-filter: blur(12px);border-radius:20px;padding:20px;border:1px solid rgba(0,255,255,0.2);box-shadow:0 0 30px rgba(0,255,255,0.15);transition:0.3s;}
.big-num {font-size:4.2rem;font-weight:900;text-align:center;color:#00ffff;text-shadow:0 0 20px #00ffff;}
.label {font-size:1.1rem;color:#88ffff;text-align:center;}
.lifetime {font-size:2.4rem;color:#ff9f1c;font-weight:900;text-shadow:0 0 20px #ff9f1c;text-align:center;}

/* ENERGY FLOW */
@keyframes flow {0%,100%{opacity:0.6;transform:translateX(0)}50%{opacity:1;transform:translateX(10px);text-shadow:0 0 40px currentColor}}
.arrow {font-size:4rem;animation: flow 2.5s infinite;display:inline-block;cursor:pointer;transition:0.2s;}

/* BATTERY RADIAL PULSE */
@keyframes pulse {0%,100%{opacity:0.7}50%{opacity:1}}
.pulse {animation:pulse 2s infinite;}

/* ENERGY SPARKS */
@keyframes spark {0%{opacity:0}50%{opacity:1;transform:scale(1.3)}100%{opacity:0}}
.spark {color:#ffff00;font-size:2.5rem;animation:spark 0.5s infinite;display:inline-block;margin:0 5px;}

/* HIGHLIGHTS */
.flash-gold {animation: flashgold 2s;}
@keyframes flashgold {0%{background-color:transparent}50%{background-color:#FFD700}100%{background-color:transparent}}
.flash-red {animation: flashred 1.5s;}
@keyframes flashred {0%{background-color:transparent}50%{background-color:#ff4757}100%{background-color:transparent}}

/* TREES / CO2 */
.tree {color:#32CD32;font-size:2rem;display:inline-block;margin:0 2px;}

/* HIDDEN DEV PANEL */
#dev-panel {display:none;position:fixed;top:10%;left:10%;width:80%;height:80%;background-color:rgba(0,0,0,0.9);border:3px solid #00ffff;border-radius:20px;overflow:auto;z-index:999;padding:20px;}
</style>
""", unsafe_allow_html=True)

# ==================== DYNAMIC SUNRISE → SUNSET BACKGROUND (FAKE STATIC PHASE 1) ====================
# We'll fake it with a gradient change based on time
hour = datetime.now().hour
if 6 <= hour < 9:
    bg_color = "radial-gradient(circle at 50% 30%, #FFD700 0%, #0a1a3a 80%)"  # Morning gold
elif 9 <= hour < 17:
    bg_color = "radial-gradient(circle at 50% 30%, #0a1a3a 0%, #00008B 80%)"   # Noon deep blue
elif 17 <= hour < 19:
    bg_color = "radial-gradient(circle at 50% 30%, #FF4500 0%, #0a1a3a 80%)"   # Sunset orange
else:
    bg_color = "radial-gradient(circle at 50% 30%, #0a1a3a 0%, #000 80%)"      # Night
st.markdown(f"<style>.stApp {{background:{bg_color};}}</style>", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown("<h1 id='skyline-logo'>SKYLINE AETHER: GENESIS</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#00ffff; margin-top:-20px;'>Live from Kigali • Cerbo GX MK2 • Phase 1 Static Demo</h3>", unsafe_allow_html=True)

# ==================== TOP CARDS ====================
c1, c2, c3, c4 = st.columns([1,1,1,1])
with c1:
    st.markdown(f"<div class='glow-card pulse'><div class='big-num'>{solar_kw:.2f}<small>kW</small></div><div class='label'>Solar Now</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='glow-card pulse'><div class='big-num'>{battery_soc}%</div><div class='label'>Battery SOC</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='glow-card pulse'><div class='big-num'>{load_kw:.2f}<small>kW</small></div><div class='label'>House Load</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='glow-card pulse'><div class='big-num'>{grid_kw:.2f}<small>kW</small></div><div class='label'>Grid</div></div>", unsafe_allow_html=True)

# ==================== ENERGY FLOW (ANIMATED + INTERACTIVE) ====================
st.markdown("<h2 style='text-align:center; color:#00ffff; margin:40px 0 20px;'>Energy Flow • Live (Static Phase 1)</h2>", unsafe_allow_html=True)
flow1, flow2, flow3, flow4, flow5 = st.columns([1,1,2,1,1])
with flow1:
    st.markdown("☀️")
with flow2:
    st.markdown(f"<span class='arrow' title='Solar → Battery'>{abs(battery_kw):.1f} kW →</span>", unsafe_allow_html=True)
    # Sparks for overproduction
    if solar_kw > load_kw:
        st.markdown("<span class='spark'>⚡</span><span class='spark'>⚡</span>", unsafe_allow_html=True)
with flow3:
    st.markdown("🔋", unsafe_allow_html=True)
with flow4:
    st.markdown(f"<span class='arrow' title='Battery → Load'>→ {load_kw:.1f} kW</span>", unsafe_allow_html=True)
with flow5:
    st.markdown("🏠")

# ==================== TODAY + LIFETIME + COINS + CO2 ====================
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.markdown(f"<div class='lifetime'>{today_kwh:.1f} kWh</div><div style='text-align:center; color:#88ffaa'>Produced Today</div>", unsafe_allow_html=True)
with col_b:
    st.markdown(f"<div class='lifetime'>{lifetime_kwh:,} kWh</div><div style='text-align:center; color:#ffdd88'>Lifetime Total</div>", unsafe_allow_html=True)
with col_c:
    st.markdown(f"<div class='lifetime'>{solar_coins}</div><div style='text-align:center; color:#00ffff'>Solar Coins</div>", unsafe_allow_html=True)
with col_d:
    # Tree counter for CO2
    num_trees = int(co2_saved_kg // 5)
    tree_html = "".join(["<span class='tree'>🌳</span>" for _ in range(num_trees)])
    st.markdown(f"<div class='lifetime'>{co2_saved_kg:.1f} kg</div><div style='text-align:center; color:#32CD32'>CO₂ Saved {tree_html}</div>", unsafe_allow_html=True)

# ==================== 7-DAY STACKED CHART ====================
st.markdown("<h2 style='text-align:center; margin:40px 0 20px; color:#00ffff'>Last 7 Days</h2>", unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Bar(x=dates, y=grid_daily, name="Grid", marker_color="#ff4757"))
fig.add_trace(go.Bar(x=dates, y=battery_daily, name="Battery", marker_color="#48cae4"))
fig.add_trace(go.Bar(x=dates, y=solar_daily, name="Solar", marker_color="#00ff88"))
fig.update_layout(barmode='stack', height=400, plot_bgcolor='rgba(0,0,0,0)',
                  paper_bgcolor='rgba(0,0,0,0)', font_color="#88ffff",
                  legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
st.plotly_chart(fig, use_container_width=True)

# ==================== RADIAL BATTERY PULSE (FAKE STATIC) ====================
st.markdown("<h2 style='text-align:center; color:#00ffff; margin:40px 0 20px;'>Battery Status</h2>", unsafe_allow_html=True)
battery_svg = f"""
<svg width="200" height="200">
  <circle cx="100" cy="100" r="90" stroke="#00ffff" stroke-width="15" fill="none" stroke-opacity="0.2"/>
  <circle cx="100" cy="100" r="90" stroke="#00ffff" stroke-width="15" fill="none"
          stroke-dasharray="{2*math.pi*90}" stroke-dashoffset="{2*math.pi*90*(1-battery_soc/100)}"
          stroke-linecap="round" style="transform:rotate(-90deg); transform-origin:center; animation: pulse 2s infinite;"/>
  <text x="100" y="115" text-anchor="middle" font-size="36" fill="#00ffff">{battery_soc}%</text>
</svg>
"""
st.markdown(battery_svg, unsafe_allow_html=True)

# ==================== HIDDEN DEV PANEL ====================
st.markdown("""
<div id="dev-panel">
<h2 style='color:#00ffff'>Developer Panel</h2>
<p>Advanced Controls & Diagnostics:</p>
<ul>
<li>Battery SOC threshold: 20%</li>
<li>Solar peak flash: 18 kW</li>
<li>Load override: 0-5 kW</li>
<li>MQTT topic placeholders</li>
<li>Debug logs here</li>
</ul>
<p>Replace static numbers with real MQTT feed to make live.</p>
<button onclick="document.getElementById('dev-panel').style.display='none'">Close</button>
</div>
""", unsafe_allow_html=True)

# JS for showing dev panel on long-press logo
st.markdown("""
<script>
let pressTimer;
const logo = document.getElementById('skyline-logo');
logo.addEventListener('mousedown', () => { pressTimer = window.setTimeout(()=>{document.getElementById('dev-panel').style.display='block'}, 1000)});
logo.addEventListener('mouseup', () => { clearTimeout(pressTimer) });
logo.addEventListener('mouseleave', () => { clearTimeout(pressTimer) });
</script>
""", unsafe_allow_html=True)

# ==================== PEAK / LOW FLASH EFFECTS ====================
# Fake logic for static demo
if solar_kw > load_kw + 2:
    st.markdown("<div class='flash-gold'></div>", unsafe_allow_html=True)
if battery_soc < 20:
    st.markdown("<div class='flash-red'></div>", unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("<p style='text-align:center; color:#00ffff; margin-top:60px; font-size:1.4rem;'>Made in Rwanda • Powered by Sun • Controlled by Aether • Phase 1 Static Demo</p>", unsafe_allow_html=True)

# ==================== AUTO-REFRESH TO KEEP ANIMATION ALIVE ====================
time.sleep(8)
st.experimental_rerun()
