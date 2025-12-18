# physics/solar.py

class SolarPanel:
    """Models the power output of a solar array based on irradiance and temperature."""
    def __init__(self, area, efficiency, temp_coeff):
        self.area = area              # Total effective panel area (m^2)
        self.efficiency = efficiency  # Rated efficiency (e.g., 0.20 for 20%)
        self.temp_coeff = temp_coeff  # % loss per °C above 25°C (e.g., 0.003 for 0.3%)

    def power_output(self, irradiance, temperature):
        """
        Calculates expected solar power (kW) using the simplified engineering model.
        Irradiance is expected in W/m^2 (will convert to kW output).
        Core Equation: Psolar = G * A * eta * f(T)
        """
        # Temperature derating: 1 - % loss per degree C above 25°C
        # We only derate if temperature > 25 (Standard Test Conditions)
        temp_loss = 1 - self.temp_coeff * (max(0, temperature - 25))
        
        # Power = Irradiance * Area * Efficiency * Temp_Loss (Result in Watts)
        power_watts = irradiance * self.area * self.efficiency * temp_loss
        
        # Convert to Kilowatts for use in the main system
        return power_watts / 1000.0