# physics/load.py
import random
from datetime import datetime

class LoadModel:
    """Models human-driven energy demand with time-of-day variation."""
    def __init__(self, base_load_kw, peak_multiplier=1.5, evening_start=18, evening_end=22):
        self.base_load = base_load_kw # Average daytime load (kW)
        self.peak_multiplier = peak_multiplier
        self.evening_start = evening_start
        self.evening_end = evening_end
        
    def demand(self, current_time=datetime.now()):
        """
        Calculates expected load demand (kW) based on the current hour.
        """
        hour = current_time.hour
        variation = random.uniform(-0.2, 0.3) # Simulates minor appliance switching
        
        # Evening Peak (18:00 - 22:00)
        if self.evening_start <= hour <= self.evening_end:
            # 50% increase during peak hours
            return self.base_load * self.peak_multiplier * (1 + variation)
        
        # Overnight Low (0:00 - 6:00)
        elif 0 <= hour <= 6:
            # Drop to maintenance level
             return self.base_load * 0.4 * (1 + random.uniform(-0.1, 0.1))
        
        # Daytime Standard
        return self.base_load * (1 + variation)