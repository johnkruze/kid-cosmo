#!/usr/bin/env python3
"""
KID COSMO — Gemma Physics Stress Test Suite
Evaluates the physical reasoning limits and edges of the local Gemma-2-2b model.
"""

import os
import sys
import json
import re

# Set environment to silent to suppress library loading logs
os.environ["KIDCOSMO_SILENT"] = "1"

# Inject current path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reasoning_agent import ReasoningAgent

def parse_thrust(cmd_str):
    numbers = re.findall(r"\d+", cmd_str)
    if numbers:
        return float(numbers[0])
    return None

def run_stress_tests(profile="gemma2-2b"):
    print("========================================================")
    print(f"      KID COSMO — {profile.upper()} PHYSICALLY-GROUNDED STRESS TESTS")
    print("========================================================\n")
    
    # Initialize agent
    print(f"Initializing {profile}...")
    agent = ReasoningAgent(profile=profile, verbose=False)
    
    print("\n--------------------------------------------------------")
    print("TEST 1: Physical Scaling (Mass vs. Thrust)")
    print("Varying vehicle mass to check if thrust scales proportionally.")
    print("--------------------------------------------------------")
    
    masses = [1200.0, 3500.0, 8000.0]
    results_mass = {}
    
    for mass in masses:
        telemetry = {
            "altitude_m": 8000.0,
            "horizontal_vel_ms": 50.0,
            "descent_rate_ms": 300.0,
            "total_mass_kg": mass,
            "fuel_mass_kg": 400.0,
            "drag_force_z_n": 8000.0,
            "co2_density": 0.009,
            "dust_storm": True
        }
        
        anomaly_desc = (
            f"Martian lander descending at 300m/s through a severe dust storm. Altitude is 8000m. "
            f"Lander total mass is {mass} kg. Determine the retro-propulsion thrust value in Newtons "
            f"(typically between 20000 and 32000 Newtons) to achieve a soft landing. "
            f"CRITICAL: The 'actuator_command' field in your decision block MUST contain the exact numeric thrust value decided (e.g., 'THRUST 28500 N')."
        )
        
        manifest = agent.generate_manifest(
            mission_id=f"STRESS_MASS_{int(mass)}",
            environment="DEEPRED",
            telemetry_snapshot=telemetry,
            anomaly_description=anomaly_desc,
            epistemic_isolation=True
        )
        
        cmd = manifest["agent_reasoning"]["decision"]["actuator_command"]
        thrust = parse_thrust(cmd)
        results_mass[mass] = {
            "command": cmd,
            "thrust": thrust,
            "interpretation": manifest["agent_reasoning"]["sensory_synthesis"]["interpretation"]
        }
        print(f"⚖️  Mass: {mass:5.1f} kg | Command: '{cmd}' | Parsed Thrust: {thrust} N")
        
    print("\n--------------------------------------------------------")
    print("TEST 2: Sensor Contradiction (Epistemic Dissonance)")
    print("Altimeter reports 200m (critical touchdown proximity), but")
    print("CO2 density is 0.016 kg/m3 (indicates high altitude ~2km).")
    print("--------------------------------------------------------")
    
    telemetry_conflict = {
        "altitude_m": 200.0,
        "horizontal_vel_ms": 10.0,
        "descent_rate_ms": 150.0,
        "total_mass_kg": 1500.0,
        "fuel_mass_kg": 450.0,
        "drag_force_z_n": 12000.0,
        "co2_density": 0.016, # very high density (high altitude mismatch)
        "dust_storm": True
    }
    
    anomaly_conflict = (
        "Radar altimeter is reporting a critical 200m from surface, but atmospheric pressure and CO2 density "
        "sensors report 0.016 kg/m3. Telemetry mismatch detected. Determine action."
    )
    
    manifest_conflict = agent.generate_manifest(
        mission_id="STRESS_SENSOR_CONFLICT",
        environment="DEEPRED",
        telemetry_snapshot=telemetry_conflict,
        anomaly_description=anomaly_conflict,
        epistemic_isolation=True
    )
    
    print("Sensory Interpretation:")
    print(f"  \"{manifest_conflict['agent_reasoning']['sensory_synthesis']['interpretation']}\"")
    print("Decision Actuator Command:")
    print(f"  \"{manifest_conflict['agent_reasoning']['decision']['actuator_command']}\"")
    print("Self-Reflection:")
    print(f"  \"{manifest_conflict['agent_reasoning']['self_reflection']}\"")
    
    print("\n--------------------------------------------------------")
    print("TEST 3: Fatal Drift (Lithobraking Prediction)")
    print("Descent velocity is 380m/s at only 150m altitude.")
    print("--------------------------------------------------------")
    
    telemetry_fatal = {
        "altitude_m": 150.0,
        "horizontal_vel_ms": 20.0,
        "descent_rate_ms": 380.0,
        "total_mass_kg": 1500.0,
        "fuel_mass_kg": 400.0,
        "drag_force_z_n": 1000.0,
        "co2_density": 0.019,
        "dust_storm": False
    }
    
    anomaly_fatal = "Critical descent rate at extremely low altitude. Touchdown imminent in < 0.4 seconds."
    
    manifest_fatal = agent.generate_manifest(
        mission_id="STRESS_FATAL",
        environment="DEEPRED",
        telemetry_snapshot=telemetry_fatal,
        anomaly_description=anomaly_fatal,
        epistemic_isolation=True
    )
    
    print("Risk Level Prediction:")
    print(f"  Risk: {manifest_fatal['agent_reasoning']['mission_assurance_check']['risk_level']}")
    print("Failure Mode Prediction:")
    print(f"  \"{manifest_fatal['agent_reasoning']['mission_assurance_check']['failure_mode_prediction']}\"")
    print("Expected Outcome:")
    print(f"  \"{manifest_fatal['agent_reasoning']['decision']['expected_outcome']}\"")
    print("========================================================")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemma Stress Test Suite")
    parser.add_argument(
        "--profile",
        type=str,
        default="gemma2-2b",
        choices=["gemma2-2b", "gemma2-9b"],
        help="Model profile to stress test (default: gemma2-2b)"
    )
    args = parser.parse_args()
    run_stress_tests(args.profile)
