# core/simulator.py

from datetime import datetime, timedelta
import time
import random

# Package paths relative to the project root
from physics.solar import SolarPanel
from physics.battery import Battery
from physics.load import LoadModel
from physics.SOHModel import SOHModel 

# --- Site-Specific Parameters ---
SITE_PARAMS = {
    "KIG-001": {
        "panel_area_m2": 50,           
        "panel_efficiency": 0.21,      
        "panel_temp_coeff": 0.003,     
        "battery_capacity_kwh": 40,    
        "battery_charge_eff": 0.95,    
        "battery_thermal_coeff": 0.005, 
        "base_load_kw": 3.0            
    },
}

class SimulationCore:
    """
    Initializes and runs the combined Solar, Battery, and Load physics models.
    Updated with Causal Separators (Idle State and Ambient Tracking).
    """
    def __init__(self, site_id, initial_soc, initial_temp):
        self.site_id = site_id
        
        # Extracts short ID from full name
        short_site_id = site_id.split(' ')[0]
        params = SITE_PARAMS.get(short_site_id, SITE_PARAMS["KIG-001"]) 
        
        # 1. Initialize Physics Components
        self.solar_model = SolarPanel(
            area=params["panel_area_m2"],
            efficiency=params["panel_efficiency"],
            temp_coeff=params["panel_temp_coeff"]
        )
        self.battery_model = Battery(
            capacity_kwh=params["battery_capacity_kwh"],
            efficiency_charge=params["battery_charge_eff"],
            thermal_coeff=params["battery_thermal_coeff"]
        )
        self.load_model = LoadModel(
            base_load_kw=params["base_load_kw"]
        )
        
        # Set initial state
        self.battery_model.energy = params["battery_capacity_kwh"] * (initial_soc / 100.0)
        self.battery_model.temperature = initial_temp
        
        # SOH INITIALIZATION
        self.soh_model = SOHModel(initial_soh=100.0) 

    def run_step(self, time_step_seconds, irradiance, ambient_temp, current_load_kw):
        """
        Runs one step of the Digital Twin simulation with Causal Guardrails.
        """
        dt_hours = time_step_seconds / 3600.0 
        
        # 1. Physics Input: Solar Generation
        # Uses ambient_temp to calculate efficiency losses
        sim_solar_kw = self.solar_model.power_output(irradiance, ambient_temp)
        sim_load_kw = current_load_kw 
        
        # 2. Causal Logic: Identify the Physics Mode (The "Heartbeat")
        net_power = sim_solar_kw - sim_load_kw
        
        # Noise-Resistant Deadband: Prevents AI from learning from sensor chatter
        if abs(net_power) < 0.1:
            system_state = "Idle"
        elif net_power > 0:
            system_state = "Charging"
        else:
            system_state = "Discharging"
            
        # 3. Battery Physics: Update SOC and Temperature
        power_in = max(0.0, net_power)  
        power_out = max(0.0, -net_power) 
        
        prev_soc = self.battery_model.get_soc() 
        
        # Calculates heat based on env_temp + internal resistance
        sim_soc, sim_temp = self.battery_model.step(
            power_in_kw=power_in,
            power_out_kw=power_out,
            dt_hours=dt_hours,
            env_temp=ambient_temp
        )

        # 4. SOH Physics: Calculate Degradation
        soc_change_percent = sim_soc - prev_soc
        
        sim_soh = self.soh_model.update_soh(
            soc_change_percent=abs(soc_change_percent),
            battery_temp_c=sim_temp,
            dt_hours=dt_hours
        )

        # 5. Return the Evidence Package
        return {
            "sim_soc": round(sim_soc, 1),
            "sim_temp": round(sim_temp, 1),
            "sim_soh": round(sim_soh, 4),
            "sim_solar_kw": round(sim_solar_kw, 2),
            "sim_load_kw": round(sim_load_kw, 2),
            "sim_net_kw": round(net_power, 2),
            "system_state": system_state,          # Causal State
            "ambient_temp": round(ambient_temp, 1) # Independent Signal
        }