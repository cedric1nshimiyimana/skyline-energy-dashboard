# skyline_aether_phase2_1_control.py — Phase 2.2 Ready (Audit & Data Logging)
# This version implements Audit Trails, Confirmation Dialogs, and Data Logging.

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
import time
import math
import uuid
import io
import threading
import json 
import csv # NEW: For simple data logging

# Optional imports that may not be available in static demo mode
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except Exception:
    MQTT_AVAILABLE = False

# autorefresh helper
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

# PDF lib
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except Exception:
    FPDF_AVAILABLE = False

# -------------------- Configuration & Environment --------------------
st.set_page_config(page_title="Skyline Aether — Phase 2.2 Ready", layout="wide", initial_sidebar_state="expanded")

# Recommended environment variables for Phase 2 (set these in your deploy environment)
BROKER_HOST = os.getenv('CERBO_MQTT_HOST', 'BROKER_IP') # replace BROKER_IP or set env var
BROKER_PORT = int(os.getenv('CERBO_MQTT_PORT', 1883))
BROKER_USER = os.getenv('CERBO_MQTT_USER', '')
BROKER_PASS = os.getenv('CERBO_MQTT_PASS', '')
MQTT_TOPIC_PREFIX = os.getenv('CERBO_MQTT_TOPIC_PREFIX', 'cerbo')
DATA_LOG_FILE = 'skyline_data_log.csv' # NEW: File for data logging

# -------------------- CSS: write style.css if missing --------------------
DEFAULT_CSS = '''
/* skyline style.css — Phase 2 default. Save as style.css to customize. */
.stApp { background: linear-gradient(180deg,#071025 0%, #001324 100%); color: #e6fbff; font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
h1 { color: #00d9ff; font-weight: 800; letter-spacing: 0.6px; }
.metric { background: rgba(20,30,50,0.7); padding: 16px; border-radius: 12px; border-left: 4px solid #00d9ff; }
.report-card { background: rgba(15,20,35,0.7); border-radius: 12px; padding: 18px; }
.glow { box-shadow: 0 8px 30px rgba(0,217,255,0.08); }
#dev-panel { background: rgba(0,0,0,0.85); border: 2px solid rgba(0,217,255,0.2); padding: 16px; border-radius: 12px; }
/* Energy flow visuals (for future SVG embedding) */
.energy-arrow { font-size: 2.6rem; }
'''

if not os.path.exists('style.css'):
    try:
        with open('style.css', 'w') as f:
            f.write(DEFAULT_CSS)
    except Exception:
        pass

# Load CSS into the app
try:
    with open('style.css') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    # fallback inline css
    st.markdown(f"<style>{DEFAULT_CSS}</style>", unsafe_allow_html=True)

# -------------------- Mock Fleet & Session --------------------
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Admin'
if 'username' not in st.session_state: # NEW: Added username for audit trail
    st.session_state.username = 'cedric'
if 'selected_site_id' not in st.session_state:
    st.session_state.selected_site_id = 'KIG-001'
if 'mqtt_started' not in st.session_state:
    st.session_state.mqtt_started = False
if 'audit_log' not in st.session_state: # NEW: Initialize Audit Log
    st.session_state.audit_log = []
if 'confirm_reboot' not in st.session_state: # NEW: Initialize Confirmation Flag
    st.session_state.confirm_reboot = False


MOCK_SITES = {
    'KIG-001': {'name': 'Kigali HQ', 'type': 'Commercial', 'status': 'Online', 'inverter': 'Victron MultiPlus-II'},
    'NBO-002': {'name': 'Nairobi Clinic', 'type': 'Healthcare', 'status': 'Warning', 'inverter': 'SMA Sunny Boy'},
    'DAR-003': {'name': 'Dar es Salaam School', 'type': 'Education', 'status': 'Online', 'inverter': 'Victron'},
    'KAM-004': {'name': 'Kampala Factory', 'type': 'Industrial', 'status': 'Offline', 'inverter': 'Growatt'},
}

# -------------------- Data Engine --------------------
@st.cache_data(ttl=300)
def generate_site_history(site_id, days_back=30, forecast_days=7):
    # (Existing history generation function, unchanged)
    dates = [datetime.now().date() - timedelta(days=i) for i in range(days_back)][::-1]
    dates += [datetime.now().date() + timedelta(days=i) for i in range(1, forecast_days+1)]
    np.random.seed(hash(site_id) % 2**32)
    base_solar = np.linspace(12, 22, days_back + forecast_days)
    solar = base_solar + np.random.normal(0, 2, len(base_solar))
    load = np.random.normal(9, 1.5, len(base_solar))
    df = pd.DataFrame({'Date': [d.strftime('%Y-%m-%d') for d in dates], 'Solar_kWh': np.round(solar, 1), 'Load_kWh': np.round(load, 1)})
    df['Grid_kWh'] = np.round(np.maximum(0, df['Load_kWh'] - df['Solar_kWh'] + np.random.normal(0, 1, len(df))), 1)
    df['Self_Sufficiency_%'] = np.round(100 * df['Solar_kWh'] / (df['Load_kWh'] + 0.001), 1)
    df['Forecast'] = df.index >= days_back
    return df

# Live data getter (uses session_state for SOC persistence)
def get_live_data(site_id):
    # (Existing live data generation function, unchanged)
    if f'soc_{site_id}' not in st.session_state:
        st.session_state[f'soc_{site_id}'] = random.randint(30, 98)

    # Calculate new SOC based on mock battery flow
    battery_kw = round(random.uniform(-4.0, 3.0), 2)
    if battery_kw < -0.1:
        st.session_state[f'soc_{site_id}'] = min(100, st.session_state[f'soc_{site_id}'] + 1)
    elif battery_kw > 0.1:
        st.session_state[f'soc_{site_id}'] = max(10, st.session_state[f'soc_{site_id}'] - 1)

    data = {
        'solar_kw': round(random.uniform(0.5, 7.8), 2),
        'load_kw': round(random.uniform(2.0, 5.5), 2),
        'battery_soc': st.session_state[f'soc_{site_id}'], # Use updated SOC
        'inverter_temp': random.randint(32, 68),
        'uptime_24h': round(random.uniform(98.5, 100), 1),
        'lifetime_kwh': random.randint(100000, 250000),
        'battery_kw': battery_kw
    }
    data['grid_kw'] = round(max(0.0, data['load_kw'] - data['solar_kw'] - data['battery_kw']), 2)
    return data

# NEW: Function to log live data to CSV (Suggestion #4)
def log_live_data(site_id, data):
    """Logs the current live data reading to a CSV file for training/auditing."""
    # Define the header for the CSV file
    fieldnames = ['timestamp', 'site_id'] + list(data.keys())
    
    # Prepare the row data
    row = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'site_id': site_id}
    row.update(data)
    
    # Check if the file exists to decide whether to write headers
    file_exists = os.path.exists(DATA_LOG_FILE)
    
    try:
        with open(DATA_LOG_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write the data row
            writer.writerow(row)
    except Exception as e:
        # In a production app, we would log this error. Here, we just fail silently.
        pass


# -------------------- MQTT Background Worker & Command Publisher --------------------

def _mqtt_on_message(client, userdata, message):
    """Callback function executed on receiving an MQTT message."""
    topic = message.topic.replace('/', '_')
    payload = message.payload.decode('utf-8')
    try:
        val = float(payload)
    except Exception:
        val = payload
    # Write to session_state
    st.session_state[topic] = val

def start_mqtt_thread(broker=BROKER_HOST, port=BROKER_PORT, username=BROKER_USER, password=BROKER_PASS, prefix=MQTT_TOPIC_PREFIX):
    """Initializes and starts the MQTT client thread for listening."""
    if not MQTT_AVAILABLE:
        st.warning('paho-mqtt not available — running in mock mode.')
        return None
    try:
        client_id = f"skyline_{uuid.uuid4().hex[:6]}"
        client = mqtt.Client(client_id)
        if username and password:
            client.username_pw_set(username, password)
        client.on_message = _mqtt_on_message
        client.connect(broker, port, 60)
        client.subscribe(f"{prefix}/#")
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()
        st.session_state['mqtt_client'] = client
        st.session_state['mqtt_started'] = True
        return client
    except Exception as e:
        st.error(f"MQTT connection failed: {e}")
        return None

def send_mqtt_command(site_id, control_path, value):
    """
    PUBLISH function: Sends a control command back to the Cerbo GX via MQTT.
    (Updated to include Audit Logging - Suggestion #2)
    """
    command_name = control_path.split('/')[-1].upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not st.session_state.mqtt_started or 'mqtt_client' not in st.session_state:
        status = "FAILED (Client Offline)"
        st.error(f"MQTT Client is not active. Command {command_name} not sent.")
        
        # Log FAILED command
        st.session_state.audit_log.append({
            "time": timestamp,
            "user": st.session_state.username,
            "site": site_id,
            "action": command_name,
            "value": value,
            "status": status
        })
        return False
    
    try:
        # Construct the topic for writing to the device
        topic = f"{MQTT_TOPIC_PREFIX}/{site_id}/{control_path}"
        payload = json.dumps({"value": value}) 
        
        st.session_state['mqtt_client'].publish(topic, payload, qos=1, retain=False)
        status = "SUCCESS"
        st.success(f"Command Published to **{topic}**: {payload}")
        
    except Exception as e:
        status = f"FAILED ({e})"
        st.error(f"Failed to publish MQTT command: {e}")
        
    # Log command result
    st.session_state.audit_log.append({
        "time": timestamp,
        "user": st.session_state.username,
        "site": site_id,
        "action": command_name,
        "value": value,
        "status": status
    })
    return status == "SUCCESS"


# Start MQTT if not started and environment seems configured
if not st.session_state.mqtt_started and MQTT_AVAILABLE and BROKER_HOST not in ('', 'BROKER_IP'):
    start_mqtt_thread()

# -------------------- UI: Sidebar --------------------
with st.sidebar:
    st.image('https://flagcdn.com/w160/rw.png', width=80)
    st.title('Skyline Aether')
    st.markdown('### Fleet Control Center')
    site_id = st.selectbox('Active Site', options=list(MOCK_SITES.keys()), format_func=lambda x: f"{x} — {MOCK_SITES[x]['name']}")
    st.session_state.selected_site_id = site_id
    
    # NEW: Data Source Indicator (Suggestion #1)
    use_mqtt = all(k in st.session_state for k in [f'{MQTT_TOPIC_PREFIX}_{site_id}_solar_kw', f'{MQTT_TOPIC_PREFIX}_{site_id}_battery_soc']) and st.session_state.mqtt_started
    
    if use_mqtt:
        source_status = "🟢 Live MQTT"
        st.sidebar.metric("Data Source", source_status)
    else:
        source_status = "🔴 Mock Data"
        st.sidebar.metric("Data Source", source_status)
        st.info('MQTT not started. Set env vars to enable live data.')

    st.markdown(f"**Status:** <span style='color: {'#00ff00' if MOCK_SITES[site_id]['status']=='Online' else '#ff9900'}; font-weight:bold;'>{MOCK_SITES[site_id]['status']}</span>", unsafe_allow_html=True)
    st.markdown('---')
    st.markdown('#### User Session (RBAC)')
    st.session_state.username = st.text_input("Username (for Audit)", value=st.session_state.username, max_chars=10) # Allows changing username for audit
    st.write(f"Role: **{st.session_state.user_role}**")
    if st.button('Toggle Role'):
        roles = ['Admin', 'Integrator', 'End-User']
        idx = roles.index(st.session_state.user_role)
        st.session_state.user_role = roles[(idx+1) % len(roles)]
        st.rerun() # Use st.rerun() for Streamlit >= 1.29
    st.markdown('---')


# -------------------- Load / Live Data --------------------
current_site_id = st.session_state.selected_site_id
if st.session_state.get('last_site') != current_site_id:
    st.session_state.last_site = current_site_id
    st.session_state.history = generate_site_history(current_site_id)

# If MQTT is active, attempt to read topic keys for the site, else fallback to get_live_data
live_keys = {
    'solar_kw': f"{MQTT_TOPIC_PREFIX}_{current_site_id}_solar_kw",
    'load_kw': f"{MQTT_TOPIC_PREFIX}_{current_site_id}_load_kw",
    'battery_kw': f"{MQTT_TOPIC_PREFIX}_{current_site_id}_battery_kw",
    'battery_soc': f"{MQTT_TOPIC_PREFIX}_{current_site_id}_battery_soc",
    'grid_kw': f"{MQTT_TOPIC_PREFIX}_{current_site_id}_grid_kw",
}

# Determine data source again for main script body
use_mqtt = all(k in st.session_state for k in live_keys.values()) and st.session_state.mqtt_started
if use_mqtt:
    live = {k: st.session_state.get(live_keys[k], 0.0) for k in live_keys} # Use .get for safety
    live.update({
        'inverter_temp': st.session_state.get(f'{MQTT_TOPIC_PREFIX}_{current_site_id}_inverter_temp', 45),
        'uptime_24h': st.session_state.get(f'{MQTT_TOPIC_PREFIX}_{current_site_id}_uptime_24h', 99.9),
        'lifetime_kwh': st.session_state.get(f'{MQTT_TOPIC_PREFIX}_{current_site_id}_lifetime_kwh', 120000),
    })
    live['battery_soc'] = int(live.get('battery_soc', 0)) 
else:
    live = get_live_data(current_site_id)

# NEW: Log current readings for training data (Suggestion #4)
log_live_data(current_site_id, live)

# -------------------- Auto-refresh (lightweight) --------------------
if AUTOREFRESH_AVAILABLE:
    st_autorefresh(interval=10_000, limit=None, key=f"autorefresh_{current_site_id}")

# -------------------- Main Tabs --------------------
# NEW: Added Audit Trail tab
tab_overview, tab_analytics, tab_reports, tab_control, tab_audit = st.tabs(["Overview", "Analytics", "Reporting", "Remote Control", "Audit Trail"])

# Selective update containers
overview_placeholder = st.empty()
analytics_placeholder = st.empty()
reports_placeholder = st.empty()
control_placeholder = st.empty()
audit_placeholder = st.empty()


with overview_placeholder.container():
    with tab_overview:
        st.header(f"{MOCK_SITES[current_site_id]['name']} — Live Dashboard")
        cols = st.columns(4)
        cols[0].metric('Solar Now', f"{live['solar_kw']:.2f} kW")
        cols[1].metric('Battery SOC', f"{live['battery_soc']:.0f}%")
        cols[2].metric('Load', f"{live['load_kw']:.2f} kW")
        cols[3].metric('Uptime 24h', f"{live.get('uptime_24h', 99.9):.1f}%")

        st.markdown('### Operational Flow')
        flow_cols = st.columns([1,1,2,1,1])
        with flow_cols[0]:
            st.markdown('☀️')
        with flow_cols[1]:
            # Use battery_kw for flow direction
            flow_kw = live.get('battery_kw', 0)
            if flow_kw > 0.1: arrow_text = f"{flow_kw:.1f} kW →" # Charging
            elif flow_kw < -0.1: arrow_text = f"← {abs(flow_kw):.1f} kW" # Discharging
            else: arrow_text = "0.0 kW"
            
            st.markdown(f"<div class='energy-arrow'>{arrow_text}</div>", unsafe_allow_html=True)
            if live['solar_kw'] > live['load_kw']:
                st.markdown("<div>⚡ Overproduction! ⚡</div>", unsafe_allow_html=True)
        with flow_cols[2]:
            st.markdown('🔋')
        with flow_cols[3]:
            st.markdown(f"<div class='energy-arrow'>→ {live['load_kw']:.1f} kW</div>", unsafe_allow_html=True)
        with flow_cols[4]:
            st.markdown('🏠')

        # Small summary cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Inverter Model', MOCK_SITES[current_site_id]['inverter'])
        c2.metric('Inverter Temp', f"{live.get('inverter_temp',45)}°C")
        c3.metric('Grid (kW)', f"{live.get('grid_kw',0.0):.2f} kW")
        c4.metric('Lifetime kWh', f"{live.get('lifetime_kwh', 0):,}")

with analytics_placeholder.container():
    with tab_analytics:
        st.header('Predictive Analytics & Historical Performance')
        hist = st.session_state.history[~st.session_state.history['Forecast']]
        pred = st.session_state.history[st.session_state.history['Forecast']]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Solar_kWh'], mode='lines', name='Solar (Actual)', line=dict(color='#00ff88', width=3)))
        fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Load_kWh'], mode='lines', name='Load (Actual)', line=dict(color='#ff9f1c', width=3)))
        fig.add_trace(go.Scatter(x=pred['Date'], y=pred['Solar_kWh'], mode='lines', name='Solar (Forecast)', line=dict(color='#00ff88', dash='dot')))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#e6fbff')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('---')
        avg_ss = hist['Self_Sufficiency_%'].mean()
        total_grid_import = hist['Grid_kWh'].sum()
        s1, s2, s3 = st.columns(3)
        s1.metric('Avg. Self-Sufficiency', f"{avg_ss:.1f}%")
        s2.metric('Total Grid Import (30D)', f"{total_grid_import:.1f} kWh")
        s3.metric('Lifetime Production', f"{live.get('lifetime_kwh',0):,} kWh")

with reports_placeholder.container():
    with tab_reports:
        st.header('Client Reporting Engine')
        col1, col2 = st.columns([1,2])
        with col1:
            st.subheader("Report Configuration")
            period = st.selectbox('Report Period', ['Last 7 Days','Last 30 Days','Last Quarter','Custom Range'])
            if period == 'Custom Range':
                start = st.date_input('Start Date', value=datetime.now().date()-timedelta(days=7))
                end = st.date_input('End Date', value=datetime.now().date())
            report_data = st.session_state.history[~st.session_state.history['Forecast']]
            if period == 'Last 7 Days':
                report_data = report_data.tail(7)
            report_metrics = {
                'Total Solar Yield': f"{report_data['Solar_kWh'].sum():.1f} kWh",
                'Avg. Self-Sufficiency': f"{report_data['Self_Sufficiency_%'].mean():.1f}%",
                'CO2 Emissions Avoided': f"{report_data['Solar_kWh'].sum()*0.5:,.1f} kg"
            }
        with col2:
            st.subheader("Report Preview & Download")
            st.json(report_metrics)
            st.markdown(f"**Report Target:** {MOCK_SITES[current_site_id]['name']} | **Generated:** {datetime.now().strftime('%Y-%m-%d')}")
            if FPDF_AVAILABLE:
                if st.button('Generate & Download PDF Report', key=f"download_btn_{current_site_id}"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font('Arial','B',16)
                    pdf.cell(200,10,txt=f"Skyline Report - {MOCK_SITES[current_site_id]['name']}",ln=1,align='C')
                    pdf.set_font('Arial','',12)
                    pdf.cell(200,10,txt=f"Period: {period}",ln=1)
                    for k,v in report_metrics.items():
                        pdf.cell(200,8,txt=f"- {k}: {v}",ln=1)
                    buf = io.BytesIO()
                    buf.write(pdf.output(dest='S').encode('latin1'))
                    buf.seek(0)
                    st.download_button('Download PDF', data=buf, file_name=f"skyline_report_{current_site_id}_{period.replace(' ','_')}.pdf", mime='application/pdf')
            else:
                st.info('fpdf not installed — PDF export disabled. pip install fpdf2')

with control_placeholder.container():
    with tab_control:
        if st.session_state.user_role in ['Admin','Integrator']:
            st.header('Remote System Control & Maintenance')
            st.warning('🚨 You have elevated privileges. Control actions trigger real-time MQTT commands.')
            
            # Reset confirmation flag if site is switched
            if st.session_state.get('last_site') != current_site_id:
                st.session_state.confirm_reboot = False
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader('Operational Commands')
                
                # Command 1: Reboot (Using Confirmation Dialog - Suggestion #3)
                if st.button('REBOOT INVERTER (Critical)', type="primary", key="reboot_trigger"):
                    st.session_state.confirm_reboot = True
                
                if st.session_state.get('confirm_reboot', False):
                    st.error("⚠️ **CONFIRM ACTION:** Are you sure you want to reboot the Inverter at this site? This action is critical and interrupts power.")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("YES, REBOOT NOW", key="reboot_yes"):
                            send_mqtt_command(current_site_id, 'system/reboot', 1) 
                            st.session_state.confirm_reboot = False
                            st.rerun() # Rerun to clear the error message
                    with col_cancel:
                        if st.button("CANCEL", key="reboot_no"):
                            st.session_state.confirm_reboot = False
                            st.rerun()
                
                # Command 2: Force Grid Charge
                if st.button('FORCE GRID CHARGE (Maintenance)'):
                    send_mqtt_command(current_site_id, 'settings/charge_mode', 'Forced')
                    
            with c2:
                st.subheader('Parameter Adjustments')
                # Command 3: Min Discharge SOC (Numerical setting)
                min_soc = st.slider('Min Discharge SOC (%)', 10, 50, 20, key='min_soc_slider')
                
                if st.button('APPLY PARAMETERS', type="secondary"):
                    send_mqtt_command(current_site_id, 'settings/min_soc', min_soc)
                    
        else:
            st.error('ACCESS DENIED: Restricted to Admin/Integrator roles for two-way control.')

with audit_placeholder.container():
    with tab_audit:
        st.header('Command Audit Trail')
        st.info("The Audit Trail records every remote action, timestamp, user, and final status (Sent/Failed).")
        
        # Displaying the audit log in reverse chronological order
        if st.session_state.audit_log:
            df_audit = pd.DataFrame(st.session_state.audit_log)
            # Filter by current site for clarity
            df_audit_site = df_audit[df_audit['site'] == current_site_id]
            st.dataframe(df_audit_site.sort_values(by='time', ascending=False), use_container_width=True)
        else:
            st.markdown("No commands have been logged yet for this site.")


# -------------------- Utility: Show MQTT keys (debug) --------------------
with st.expander('Developer / Debug'):
    st.markdown('<div id="dev-panel">', unsafe_allow_html=True)
    st.markdown(f'**MQTT Status:** {"🟢 Started" if st.session_state.get("mqtt_started") else "🔴 Not Started (Mocking)"}')
    st.markdown(f'**Data Log File:** `{DATA_LOG_FILE}` ({len(pd.read_csv(DATA_LOG_FILE)) if os.path.exists(DATA_LOG_FILE) else "0"} rows)')
    keys = [k for k in st.session_state.keys() if k.startswith(MQTT_TOPIC_PREFIX+'_')]
    st.write(f'Topics seen in session_state ({len(keys)} total):')
    st.json({k: st.session_state[k] for k in keys[:5]}) # Show first 5 keys
    st.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.mqtt_started:
        if st.button('Start MQTT Manually (Requires Broker/paho-mqtt)'):
            if MQTT_AVAILABLE:
                start_mqtt_thread()
            else:
                st.warning('paho-mqtt not installed. Cannot start.')

# -------------------- Footer --------------------
st.markdown('---')
st.caption('Skyline Aether — Phase 2.2 Ready (Audit & Data Logging) • This file contains the architecture for a multi-million dollar valuation.')