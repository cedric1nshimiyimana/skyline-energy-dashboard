# physics/SOHModel.py

class SOHModel:
    """
    Simulates the State of Health (SOH) degradation of a battery over time
    based on charge cycling and thermal stress.
    """
    def __init__(self, initial_soh=100.0):
        # SOH is tracked as a percentage (100% when new)
        self.soh = initial_soh 
        
        # Degradation rates (simplified constants)
        # 1. Base Cycle Degradation: Loss per 1% SOC change (e.g., 0.000001% SOH loss per 1% SOC cycled)
        self.cycle_loss_factor = 0.000001 
        # 2. Thermal Acceleration: Multiplier for loss when temperature is high
        self.thermal_accelerator = 1.5 
        # 3. Thermal Threshold: Temperature above which thermal degradation accelerates
        self.thermal_threshold_c = 40.0

    def calculate_degradation(self, soc_change_percent, battery_temp_c, dt_hours):
        """
        Calculates the SOH loss for the current time step.
        
        Args:
            soc_change_percent (float): Absolute change in SOC percentage (e.g., 1.5 for 1.5% change).
            battery_temp_c (float): Current battery cell temperature in Celsius.
            dt_hours (float): Time step duration in hours.
            
        Returns:
            float: The total SOH loss percentage for the step.
        """
        
        # 1. Cycle Stress Degradation
        # The larger the SOC change, the more degradation occurs.
        cycle_degradation = abs(soc_change_percent) * self.cycle_loss_factor * dt_hours
        
        # 2. Thermal Stress Acceleration
        thermal_multiplier = 1.0
        if battery_temp_c > self.thermal_threshold_c:
            # Thermal stress accelerates the degradation rate
            thermal_multiplier = self.thermal_accelerator
            
        # Apply the thermal stress to the cycle degradation
        total_loss = cycle_degradation * thermal_multiplier
        
        return total_loss

    def update_soh(self, soc_change_percent, battery_temp_c, dt_hours):
        """
        Updates the internal SOH state and returns the new value.
        
        Returns:
            float: The new SOH percentage.
        """
        soh_loss = self.calculate_degradation(soc_change_percent, battery_temp_c, dt_hours)
        
        self.soh -= soh_loss
        
        # SOH should never drop below 0 (though practically it would be replaced far sooner)
        self.soh = max(0.0, self.soh)
        
        return self.soh