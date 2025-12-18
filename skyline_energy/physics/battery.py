# physics/battery.py
import math

class Battery:
    """
    Models the energy state (SOC) and thermal state (Temperature) of the battery.
    Uses Energy Balance (Newton) and Lumped Thermal (Fourier-inspired).
    """
    def __init__(self, capacity_kwh, efficiency_charge, thermal_coeff):
        # Corrected variable names to match SimulationCore for consistency
        self.capacity_kwh = capacity_kwh        # Nominal maximum capacity (kWh) <<< FIXED NAME
        self.efficiency_charge = efficiency_charge # Charge efficiency (e.g., 0.95) <<< FIXED NAME
        self.thermal_coeff = thermal_coeff      # Heat generation coefficient (C/kW*h)
        
        # Initial state (will be set to live data later)
        self.energy = capacity_kwh * 0.5        # Current stored energy (kWh), defaults to full
        self.temperature = 25.0                 # Internal battery temperature (C)
        self.max_temp = 55.0                    # Safety limit for temperature (C)
        self.max_power_kw = capacity_kwh * 4.0  # Max power limit (e.g., 4C rate)
        
    def get_soc(self):
        """
        Calculates and returns the current State of Charge (SOC) in percent.
        This method is critical for the SOH calculation in simulator.py.
        """
        # SOC = (Current Energy / Total Capacity) * 100
        soc = (self.energy / self.capacity_kwh) * 100.0
        # Ensure it stays within physical limits
        return max(0.0, min(100.0, soc))

    def step(self, power_in_kw, power_out_kw, dt_hours, env_temp):
        """
        Updates the state over a time step (dt_hours).
        """
        
        # 1. Energy Balance (Newton)
        # Apply charge efficiency to incoming power
        effective_power_in = power_in_kw * self.efficiency_charge
        
        # Max discharge rate limit (using a max power limit to prevent crash)
        power_out_kw = min(power_out_kw, self.max_power_kw)
        
        energy_change = (effective_power_in - power_out_kw) * dt_hours
        self.energy += energy_change
        
        # Constrain energy to be within capacity limits
        self.energy = max(0.0, min(self.energy, self.capacity_kwh)) # <<< USED CORRECT CAPACITY NAME

        # Calculate SOC
        soc = self.get_soc() # Use the new helper method
        
        # 2. Thermal Diffusion (Fourier-inspired)
        
        # Power flow causing heat generation (simplified: sum of absolute power flows)
        power_flow = power_in_kw + power_out_kw
        
        # Internal heat gain (proportional to total power flow and thermal coefficient)
        # Your previous logic used net_power^2. I will simplify using the total flow for robust heat generation.
        internal_heat_gain = power_flow * self.thermal_coeff * dt_hours
        
        # Cooling/Heating: 0.1 is a simple heat transfer coefficient (alpha)
        # Rate of cooling/heating is proportional to the difference between internal and external temp.
        cooling_or_heating = 0.1 * (env_temp - self.temperature) * dt_hours
        
        self.temperature += cooling_or_heating + internal_heat_gain
        
        # Enforce temperature safety limit
        self.temperature = min(self.max_temp, self.temperature)
        
        return soc, self.temperature