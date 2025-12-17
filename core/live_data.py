# core/live_data.py - Mock data generation and logging

import random
from datetime import datetime
import pandas as pd
import os

# --- Configuration ---
DATA_FILE = "historical_data.csv" 
SOC_DROP_PER_STEP = 0.05 

def get_latest_data(site_id):
    """
    Returns the latest live operational data for a given site.
    """
    current_time = datetime.now()
    current_hour = current_time.hour
    
    # --- 1. Load/Demand Simulation ---
    if 7 <= current_hour < 22:
        base_load = 8.0 
        load_kw = base_load + random.uniform(0.5, 1.5)
    else:
        base_load = 1.0
        load_kw = base_load + random.uniform(0.1, 0.5)

    # --- 2. Solar/Source Simulation ---
    if 9 <= current_hour <= 17:
        solar_kw = 10 * (1 - abs(current_hour - 13) / 4) + random.uniform(-1, 1)
        solar_kw = max(0, solar_kw)
    else:
        solar_kw = 0.0

    # --- 3. Battery State of Charge (SOC) Simulation ---
    history_df = get_historical_data(site_id)
    if not history_df.empty:
        last_soc = history_df['battery_soc'].iloc[-1]
    else:
        last_soc = 50 
    
    net_power = solar_kw - load_kw
    
    if net_power > 0:
        soc_change = net_power * 0.01 
    else:
        soc_change = net_power * 0.01

    new_soc = last_soc + soc_change
    new_soc = max(0, min(100, new_soc))
    
    # --- 4. Other Metrics ---
    inverter_temp = 30 + abs(net_power) * 0.5 + random.uniform(-0.5, 0.5)
    
    return {
        "timestamp": current_time,
        "solar_kw": solar_kw,
        "battery_soc": new_soc,
        "load_kw": load_kw,
        "inverter_temp": inverter_temp,
        "ambient_temp": 25.0 + random.uniform(-2, 3),
        "irradiance": solar_kw * 100,
        "uptime_24h": 99.5 + random.uniform(0, 0.5)
    }

get_live_data = get_latest_data

def log_live_data(site_id, data_dict):
    """Logs the current live and simulation data to a CSV file with integrity checks."""
    
    # Format timestamp
    if isinstance(data_dict['timestamp'], datetime):
        data_dict['timestamp'] = data_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    df_new = pd.DataFrame([data_dict])
    file_path = f"{site_id}_{DATA_FILE}"

    # --- INTEGRITY CHECK ---
    # If file exists, check if the column count matches
    if os.path.exists(file_path):
        try:
            # Read just the header
            existing_header = pd.read_csv(file_path, nrows=0).columns.tolist()
            new_columns = df_new.columns.tolist()
            
            # If columns don't match (e.g., we added Sim SOH), remove old file to prevent ParserError
            if len(existing_header) != len(new_columns):
                os.remove(file_path)
                header_needed = True
            else:
                header_needed = False
        except:
            os.remove(file_path)
            header_needed = True
    else:
        header_needed = True

    # --- WRITE DATA ---
    mode = 'w' if header_needed else 'a'
    df_new.to_csv(file_path, mode=mode, index=False, header=header_needed)


def get_historical_data(site_id):
    """Retrieves all logged historical data for a site."""
    file_path = f"{site_id}_{DATA_FILE}"
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
            # Use 'tail' or 'last' to avoid crashing on large files
            return df.tail(100) 
        except Exception as e:
            # If the file is corrupted, return empty so the system can restart
            return pd.DataFrame()
    return pd.DataFrame()