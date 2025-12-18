# core/live_data.py

import random
from datetime import datetime

# --- 1. THE ASSET LEDGER (Persistence Simulation) ---
# In a production system, this value would be saved to a database.
# For now, it stays in memory as your "Monotonic Odometer".
if 'persistent_throughput' not in globals():
    global persistent_throughput
    persistent_throughput = 450.0  # Starting value in kWh

def get_live_data(site_id, sim_net_kw=0.0, time_step_seconds=10):
    """
    Generates and tracks live system data with causal integrity.
    
    Args:
        site_id (str): The ID of the energy site.
        sim_net_kw (float): The net power flow from the simulator.
        time_step_seconds (int): Time elapsed since last update.
    """
    global persistent_throughput
    
    # 2. Independent Causal Signal (Ambient Temp)
    # This represents the actual environment, separate from battery heat
    ambient_celsius = 24.5 + random.uniform(-1.5, 1.5)
    
    # 3. Energy Throughput Logic (The Odometer)
    # Power (kW) * Time (Hours) = Energy (kWh)
    delta_hours = time_step_seconds / 3600.0
    energy_increment = abs(sim_net_kw) * delta_hours
    persistent_throughput += energy_increment
    
    # 4. Generate Live Readings
    # We simulate these to match the site's expected scale
    load_kw = 12.0 + random.uniform(-2, 4)
    solar_kw = max(0, load_kw + sim_net_kw) # Derived from physics flow
    
    return {
        "site_id": site_id,
        "timestamp": datetime.now().isoformat(),
        "solar_kw": round(solar_kw, 2),
        "load_kw": round(load_kw, 2),
        "ambient_temp": round(ambient_celsius, 1), # Causal Separator
        "energy_throughput_kwh": round(persistent_throughput, 4), # Asset Odometer
        "battery_soc": 85.0, # Placeholder: will be updated by sim_state in app.py
        "critical_load_ratio": 0.45, # Strategic Governance metric
    }

def log_live_data(site_id, data):
    """Placeholder for future database logging."""
    # print(f"📝 [LOG] Site {site_id} updated: {data['energy_throughput_kwh']} kWh total.")
    pass

def get_historical_data(site_id, limit=20):
    """Placeholder for fetching trend data."""
    return []