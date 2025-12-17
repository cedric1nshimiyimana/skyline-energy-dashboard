# core/simulator.py

from datetime import datetime, timedelta
import time
import random

# FINAL FIX: We must use the package path relative to the project root (skyline_energy)
# This resolves the "attempted relative import beyond top-level package" error.
from physics.solar import SolarPanel
from physics.battery import Battery
from physics.load import LoadModel
from physics.SOHModel import SOHModel # <<< ADDED SOH IMPORT

# --- Site-Specific Parameters (Example Configuration) ---
# NOTE: These are the physical properties of the assets installed at your sites.
SITE_PARAMS = {
    "KIG-001": {
        # Solar Panel Parameters
        "panel_area_m2": 50,           # 50 sq meters of panels
        "panel_efficiency": 0.21,      # 21% efficient panels
        "panel_temp_coeff": 0.003,     # 0.3% loss per degree C
        # Battery Parameters
        "battery_capacity_kwh": 40,    # 40 kWh total storage (e.g., 4 x 10kWh units)
        "battery_charge_eff": 0.95,    # 95% charge efficiency
        "battery_thermal_coeff": 0.005, # Heat generation coefficient (lumped)
        # Load Parameters
        "base_load_kw": 3.0            # 3.0 kW average load
    },
    # The simulation will use the KIG-001 profile for all sites for now.
}

class SimulationCore:
    """
    Initializes and runs the combined Solar, Battery, and Load physics models.
    This class is the Digital Twin for one site. 
    """
    def __init__(self, site_id, initial_soc, initial_temp):
        self.site_id = site_id
        
        # Load parameters for the specific site (or fallback to KIG-001 if missing)
        # Extracts short ID (e.g., KIG-001) from full site name (e.g., KIG-001 (Kigali HQ))
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
        # We still initialize the LoadModel, but we will override its output
        self.load_model = LoadModel(
            base_load_kw=params["base_load_kw"]
        )
        
        # Set initial state (Crucial step: Syncing the model to the real world)
        self.battery_model.energy = params["battery_capacity_kwh"] * (initial_soc / 100.0)
        self.battery_model.temperature = initial_temp
        
        # VVV--- SOH INITIALIZATION ---VVV
        self.soh_model = SOHModel(initial_soh=100.0) # Initialize SOH to 100%
        # ^^^--- SOH INITIALIZATION ---^^^

    # VVV--- CHANGE IS HERE ---VVV
    def run_step(self, time_step_seconds, irradiance, ambient_temp, current_load_kw):
    # ^^^--- CHANGE IS HERE ---^^^
        """
        Runs one step of the Digital Twin simulation (e.g., a 10-second tick).
        
        Args:
            time_step_seconds (int): The duration of the step (e.g., 10 seconds).
            irradiance (float): Current sun power (W/m^2).
            ambient_temp (float): External air temperature (C).
            current_load_kw (float): The current measured load from the live data. 
            
        Returns:
            dict: The new simulated state (SOC, Temperature, Power Flows, SOH).
        """
        
        dt_hours = time_step_seconds / 3600.0 # Convert timestep to hours
        current_time = datetime.now()
        
        # 1. Physics Input: Calculate the power generated and demanded
        sim_solar_kw = self.solar_model.power_output(irradiance, ambient_temp)
        
        # We synchronize the simulation's load prediction with the live data for this step
        sim_load_kw = current_load_kw 
        
        # 2. Energy Flow Logic: Determine charge/discharge for the battery
        net_power = sim_solar_kw - sim_load_kw
        
        # For a simplified model, we assume the net power difference goes to the battery (charge/discharge)
        sim_battery_kw = net_power 
        
        # The Battery model expects Pin and Pout to be non-negative
        power_in = max(0.0, net_power)  # Only if positive net power
        power_out = max(0.0, -net_power) # Only if negative net power
        
        # Assume grid is only used when the battery is empty (simple for now)
        sim_grid_kw = 0.0
        
        # VVV--- SOH UPDATE LOGIC ---VVV
        # 3. Battery Physics: Update SOC and Temperature
        # Capture the previous SOC before the step runs
        prev_soc = self.battery_model.get_soc() 
        
        sim_soc, sim_temp = self.battery_model.step(
            power_in_kw=power_in,
            power_out_kw=power_out,
            dt_hours=dt_hours,
            env_temp=ambient_temp
        )

        # 4. SOH Physics: Calculate Degradation based on stress
        soc_change_percent = sim_soc - prev_soc
        
        sim_soh = self.soh_model.update_soh(
            soc_change_percent=abs(soc_change_percent), # SOH cares about absolute change (Depth of Discharge)
            battery_temp_c=sim_temp,
            dt_hours=dt_hours
        )
        # ^^^--- SOH UPDATE LOGIC ---^^^

        # VVV--- RETURN SOH ---VVV
        return {
            "sim_soc": round(sim_soc, 1),
            "sim_temp": round(sim_temp, 1),
            "sim_soh": round(sim_soh, 4), # Returned SOH for tracking
            "sim_solar_kw": round(sim_solar_kw, 2),
            "sim_load_kw": round(sim_load_kw, 2),
            "sim_net_kw": round(net_power, 2),
            "sim_battery_kw": round(sim_battery_kw, 2),
            "sim_grid_kw": round(sim_grid_kw, 2),
        }
        # ^^^--- RETURN SOH ---^^^