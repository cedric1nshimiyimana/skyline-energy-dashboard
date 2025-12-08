# skyline_energy_app_v2.py
# Streamlit app: Skyline Energy — "Your Energy = Your Money" (v2)
# This single-file app implements the 5 priority features requested:
# 1) Energy Balance Sheet Dashboard (Home)
# 2) User Profile in sidebar (Energy Identity)
# 3) Proof History tab (downloadable proofs)
# 4) Carbon Credit Estimator
# 5) Final heartbeat "YOUR SOLAR IS NOW MONEY"

# NOTE: Replace the simulated data blocks with your real MQTT/API/Cerbo GX inputs later.

import streamlit as st
from datetime import datetime
import io
import json

st.set_page_config(page_title="Skyline Energy — Energy Wallet", layout="wide")

# -------------------------------
# Simple CSS
# -------------------------------
st.markdown("""
<style>
body {background-color: #0f172a; color: #e6eef8}
.glow-text {font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color:#7c3aed;}
.metric-card{background:linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02)); padding:18px; border-radius:12px; text-align:center;}
.metric-card h2{margin:0; font-size:28px}
.small-muted{color:#94a3b8}
.footer-heart{background:rgba(34,211,153,0.08); border:3px solid rgba(34,211,153,0.45); border-radius:20px; padding:30px;}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar: Navigation + Profile
# -------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/44/Sun_icon.svg", width=80)
st.sidebar.markdown("# Skyline Energy")

# Profile / Energy Identity
st.sidebar.markdown("### Your Energy Identity")
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = 'Cedric'
if 'user_phone' not in st.session_state:
    st.session_state['user_phone'] = '078xxxxxxx'

user_name = st.sidebar.text_input("Your Name", value=st.session_state['user_name'])
user_phone = st.sidebar.text_input("Phone", value=st.session_state['user_phone'])
if st.sidebar.button("Save Profile"):
    st.session_state['user_name'] = user_name
    st.session_state['user_phone'] = user_phone
    st.sidebar.success("Profile saved — your energy now has an owner")

st.sidebar.markdown("---")

menu = st.sidebar.radio("Navigate", ["Home", "My Proofs", "Battery Usage", "Load Calculator", "Forecasting", "Gates & Security", "Settings"], index=0)

# -------------------------------
# Helper: PDF / text export (simple)
# -------------------------------
def make_proof_text(owner, period, total_kwh, uptime, revenue_text, extra_notes=""):
    proof = f"""
SKYLINE ENERGY • ENERGY WEALTH CERTIFICATE
Owner: {owner}
Period: {period}
Total Production: {total_kwh:.1f} kWh
Uptime: {uptime}
Revenue (est): {revenue_text}
Notes: {extra_notes}
Issued: {datetime.now().strftime('%d %B %Y')} • Kigali, Rwanda
"""
    return proof

# -------------------------------
# Simulated Real Data (replace with MQTT/API later)
# -------------------------------
# For initial demo these values are static. Later, wire this to real telemetry.
today_produced = 14.7  # kWh
today_consumed = 9.2   # kWh
net_surplus = today_produced - today_consumed
battery_stored = 32.4  # kWh
rwf_per_kwh = 240      # average Rwanda tariff (RWF)
monthly_projection = today_produced * 30 * rwf_per_kwh

# -------------------------------
# HOME: Energy Balance Sheet Dashboard
# -------------------------------
if menu == "Home":
    st.markdown("<h1 class='glow-text'>My Energy Wallet</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#94a3b8;'>Your solar is now your personal currency • Made in Rwanda</h3>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><h2>{today_produced:.1f} kWh</h2><p class='small-muted'>Produced Today</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h2>{today_consumed:.1f} kWh</h2><p class='small-muted'>Consumed</p></div>", unsafe_allow_html=True)
    with col3:
        sign = '+' if net_surplus >= 0 else ''
        st.markdown(f"<div class='metric-card'><h2 style='color:#34d399'>{sign}{net_surplus:.1f} kWh</h2><p class='small-muted'>Net Surplus</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><h2>{battery_stored:.1f} kWh</h2><p class='small-muted'>Stored (Your Cash Reserve)</p></div>", unsafe_allow_html=True)

    st.markdown("## Money Made This Month")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("From Solar Production", f"RWF {today_produced * rwf_per_kwh:,.0f}", f"+{today_produced * rwf_per_kwh:,.0f} today")
    col_b.metric("Projected This Month", f"RWF {monthly_projection:,.0f}")
    col_c.metric("CO₂ Avoided", f"{today_produced * 0.78:.1f} kg", "equals 3 trees")

    st.markdown("---")
    st.markdown("### Energy Flow (Simulated)")
    st.write("Note: Replace with live Sankey / chart fed by your inverter or Cerbo GX API.")

    # Certificate generator
    if st.button("Generate My Energy Proof Certificate", use_container_width=True):
        owner = st.session_state.get('user_name', 'Cedric')
        period = datetime.now().strftime('%B %Y')
        total_month_kwh = today_produced * 30
        uptime = "99.4%"
        revenue_text = f"RWF {total_month_kwh * rwf_per_kwh:,.0f}"
        proof_text = make_proof_text(owner, period, total_month_kwh, uptime, revenue_text, extra_notes="Verified by AETHER CORE (sim)")

        st.code(proof_text)
        buf = io.BytesIO()
        buf.write(proof_text.encode('utf-8'))
        buf.seek(0)
        st.download_button("Download Proof (TXT)", data=buf, file_name=f"Skyline_Proof_{datetime.now().strftime('%Y%m')}.txt")
        st.success("Proof ready! Send to bank or carbon buyer")

    # Carbon Credits expander (also in Home)
    with st.expander("Carbon Credits (I-REC Ready)"):
        co2_avoided_month_kg = today_produced * 30 * 0.78
        credit_price_usd_per_ton = st.number_input("Carbon price (USD/ton)", value=12.0)
        potential_usd = (co2_avoided_month_kg / 1000) * credit_price_usd_per_ton
        st.write(f"**{co2_avoided_month_kg:.1f} kg CO₂ avoided this month**")
        st.success(f"Potential Earnings: **${potential_usd:.2f} USD** when you sell I-RECs")
        if st.button("Connect to Carbon Buyer (Simulate)"):
            st.write("(Simulated) Sending proof to South Pole / Buyer... done.")

    st.markdown("---")

    # Final heartbeat message (small)
    st.markdown("""
    <div class='footer-heart'>
        <h2 style='color:#34d399; margin:0;'>YOUR SOLAR IS NOW MONEY</h2>
        <h4>You don't monitor energy.<br><b>You create wealth every sunrise.</b></h4>
        <p><i>Skyline Energy • Turning African Sunlight into African Wealth</i></p>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------
# My Proofs: proof history and downloads
# -------------------------------
elif menu == "My Proofs":
    st.markdown("<h1>My Energy Proof Certificates</h1>", unsafe_allow_html=True)
    st.info("These documents are trusted by banks, carbon buyers, and microgrid investors (demo data)")

    # Example historical data: replace with DB / S3 later
    proofs = [
        {"month": "November 2025", "kwh": 423, "uptime": "99.1%", "revenue": "RWF 101,520"},
        {"month": "October 2025", "kwh": 398, "uptime": "98.7%", "revenue": "RWF 95,520"},
        {"month": "September 2025", "kwh": 412, "uptime": "99.8%", "revenue": "RWF 98,880"},
    ]

    for p in proofs:
        with st.expander(f"{p['month']} • {p['kwh']} kWh • {p['revenue']}"):
            st.write(f"Uptime: {p['uptime']} • Verified by AETHER CORE")
            proof_text = make_proof_text(st.session_state.get('user_name','Cedric'), p['month'], p['kwh'], p['uptime'], p['revenue'], extra_notes="Historic record")
            st.code(proof_text)
            # Provide a simple download
            buf = io.BytesIO()
            buf.write(proof_text.encode('utf-8'))
            buf.seek(0)
            st.download_button(f"Download Certificate ({p['month']})", data=buf, file_name=f"proof_{p['month'].replace(' ','_')}.txt")

# -------------------------------
# Battery Usage (placeholder) - useful UX scaffolding
# -------------------------------
elif menu == "Battery Usage":
    st.markdown("# Battery Usage")
    st.write("This page is a placeholder for raw battery telemetry, cycles, and health predictions.")
    st.write("Sample metrics:")
    st.metric("State of Charge (SoC)", "64%")
    st.metric("Battery Health", "95%")
    st.write("Add your battery management system (BMS) or Cerbo GX data feed here.")

# -------------------------------
# Load Calculator (simple)
# -------------------------------
elif menu == "Load Calculator":
    st.markdown("# Load Calculator")
    st.write("Estimate daily kWh needs and how many panels/battery you need.")
    avg_daily_kwh = st.number_input("Average daily consumption (kWh)", value=10.0)
    days_of_backup = st.slider("Days of backup required", 0, 7, 1)
    battery_size_needed = avg_daily_kwh * days_of_backup
    st.write(f"You'd need ~ {battery_size_needed:.1f} kWh to cover {days_of_backup} days of backup.")

# -------------------------------
# Forecasting (placeholder)
# -------------------------------
elif menu == "Forecasting":
    st.markdown("# Forecasting")
    st.write("Forecasting shows next 7 days production based on irradiance forecast and historical data.")
    st.write("(Placeholder) Next 7 days: [13.2, 14.1, 12.8, 15.0, 14.6, 13.9, 14.3] kWh")

# -------------------------------
# Gates & Security (placeholder)
# -------------------------------
elif menu == "Gates & Security":
    st.markdown("# Gates & Security")
    st.write("Control access to physical gates, relays, and alarms")
    st.button("Open Gate (Simulated)")
    st.button("Arm Alarm (Simulated)")

# -------------------------------
# Settings
# -------------------------------
elif menu == "Settings":
    st.markdown("# Settings")
    st.write("Settings and integrations: MQTT broker, Cerbo GX, Inverter API, Carbon buyer webhook, Accounting export (CSV)")

    if st.button("Export settings (simulate)"):
        settings = {
            'user': st.session_state.get('user_name','Cedric'),
            'phone': st.session_state.get('user_phone','078xxxxxxx'),
            'rwf_per_kwh': rwf_per_kwh
        }
        st.download_button("Download settings JSON", data=json.dumps(settings), file_name='skyline_settings.json')
        st.success("Settings exported")

# -------------------------------
# Footer / small help
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("Need help? Reply to the dev: Cedric • Kigali")

# -------------------------------
# End of file
# -------------------------------
# Integration notes:
# - Replace simulated telemetry (today_produced, battery_stored, etc.) with live inputs from MQTT, InfluxDB, or a REST API.
# - Persist proofs to a database (Postgres / Supabase / S3) so "My Proofs" can be auto-populated.
# - Replace TXT downloads with real PDFs (reportlab / weasyprint) when needed for banks.
# - Add authentication (OAuth / Magic Link) before issuing official proofs.
