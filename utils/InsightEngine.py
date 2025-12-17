# utils/InsightEngine.py

def generate_insights(sim_state, initial_state):
    """
    Translates simulation results and contextual data into professional,
    physics-grounded qualitative insights.
    
    Args:
        sim_state (dict): The dictionary returned by SimulationCore.run_step().
        initial_state (dict): The dictionary containing initial and time-series data
                              (like ambient_temp, irradiance, load_kw).
    
    Returns:
        str: A single actionable system insight sentence.
    """
    
    insights = []
    
    # 1. Gather Key Metrics and Trends (Simplified for first launch)
    
    # Use the simulation's net power to determine charge/discharge direction
    net_power = sim_state.get("sim_net_kw", 0.0)
    
    # Use the simulated SOC and Temp for directional insights
    sim_soc = sim_state.get("sim_soc", 0.0)
    sim_temp = sim_state.get("sim_temp", 0.0)
    
    # Use the ambient data for context
    ambient_temp = initial_state.get("ambient_temp", 25.0)
    irradiance = initial_state.get("irradiance", 0.0)
    
    
    # 2. Apply Logic Rules (The 'Grammar' of the system)
    
    # Rule 1: Thermal Stress (Temp is high relative to environment and power flow is high)
    if sim_temp > ambient_temp + 5 and net_power > 5: # Temp 5°C above ambient under high power
        insights.append(
            "Battery operating at elevated temperature under high power transfer, suggesting potential thermal stress."
        )

    # Rule 2: Charging Efficiency (High solar but little SOC change)
    # Note: Requires history, but we use a proxy for now.
    if irradiance > 700 and net_power < 0.5 and net_power > -0.5 and sim_soc < 95: # High sun but battery is near flat charge/discharge
        insights.append(
            "High solar irradiance detected, but net power flow is minimal, check battery charge acceptance or site load balance."
        )

    # Rule 3: Deep Discharge Warning (SOC is low and still discharging)
    if sim_soc < 20 and net_power < 0:
        insights.append(
            "Critical: Battery SOC is below 20% and still discharging. Grid support or load shedding may be required."
        )
    
    # Rule 4: High Discharge Warning (SOC is healthy but discharging fast)
    elif sim_soc >= 20 and net_power < -5: # Discharging at high power
        insights.append(
            "High load demand requires rapid discharge, closely monitor discharge rate and battery temperature."
        )
        
    # Rule 5: Stable State (If nothing critical is happening)
    if not insights:
        # Check if the system is running well
        if irradiance > 10 and sim_soc > 30 and sim_temp < ambient_temp + 3:
             insights.append(
                "System is operating efficiently, with stable charge levels and low thermal variance."
            )
        else:
             insights.append(
                "System status is nominal. No immediate physics-driven warnings detected."
            )
            
    # 3. Return the single, most relevant insight (the first one generated)
    # For now, the rules are ordered from most critical to least.
    return insights[0]