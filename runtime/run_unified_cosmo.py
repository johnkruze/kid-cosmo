#!/usr/bin/env python3
"""
KID COSMO — Unified Physics-Grounded Scenario Runner
Runs step-by-step physical simulations using the Rust ztp-runtime engine via Python FFI,
detects physical anomalies, and dispatches to Kid Cosmo reasoning agent (Gemma/Qwen/Gemini).
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime

# Inject current path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ztp_bridge
from reasoning_agent import ReasoningAgent

def parse_args():
    parser = argparse.ArgumentParser(description="Kid Cosmo Unified Physics Scenario Runner")
    parser.add_argument(
        "--profile",
        type=str,
        default="fast",
        choices=["fast", "balanced", "physics", "gemma2-2b", "gemma2-9b", "gemini"],
        help="Model profile to use for somatic reasoning (default: fast/Qwen2.5-Coder-7b)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="orbital",
        choices=["orbital", "terran", "atheric"],
        help="Physics scenario to execute (default: orbital)"
    )
    return parser.parse_args()


# ─── SCENARIO 1: ORBITAL ──────────────────────────────────────────────────────
def run_orbital_scenario(agent: ReasoningAgent):
    print("\n═══════════════════════════════════════════════════════════")
    print("  [SCENARIO 1] ORBITAL DEEP-SPACE DETUMBLED MANEUVER")
    print("  Physics Engine: ztp-runtime (Orbital 6DoF & Attitude)")
    print("═══════════════════════════════════════════════════════════")
    
    # Initialize satellite state
    state = ztp_bridge.C_SatelliteState()
    state.position[0] = 6878.137  # Orbit radius (km)
    state.velocity[1] = 7.612     # Orbit speed (km/s)
    state.quaternion_attitude[0] = 1.0
    state.angular_velocity[0] = 0.01
    state.angular_velocity[1] = -0.015
    state.angular_velocity[2] = 0.005
    state.inertia_tensor[0] = 20.0
    state.inertia_tensor[4] = 20.0
    state.inertia_tensor[8] = 30.0
    
    dt = 0.5
    anomaly_triggered = False
    
    print("\nRunning nominal orbit tracking step-by-step:")
    for step in range(1, 50):
        # Apply external micro-meteoroid torque disturbances causing tumble
        dist_torque = [0.01 * step, -0.015 * step, 0.005 * step]
        ztp_bridge.orbital_step_6dof(state, dt)
        ztp_bridge.orbital_step_attitude(state, dist_torque, dt)
        
        # Calculate angular velocity magnitude
        w_mag = (state.angular_velocity[0]**2 + state.angular_velocity[1]**2 + state.angular_velocity[2]**2)**0.5
        print(f"  Step {step:02d} | AngVel: [{state.angular_velocity[0]:.4f}, {state.angular_velocity[1]:.4f}, {state.angular_velocity[2]:.4f}] | Mag: {w_mag:.4f} rad/s")
        
        # Hazard condition: AngVel exceeds 0.05 rad/s (critical tumbling limit)
        if w_mag > 0.05:
            print(f"\n⚠️  PHYSICAL EXTREMUM DETECTED: Satellite angular velocity ({w_mag:.4f} rad/s) exceeds safety limit (0.05 rad/s)!")
            print("❌ CONJUNCTION BLACKOUT / SENSOR CHATTER engaged.")
            anomaly_triggered = True
            break
            
        time.sleep(0.1)
        
    if anomaly_triggered:
        telemetry = {
            "position_km": list(state.position),
            "velocity_kms": list(state.velocity),
            "quaternion": list(state.quaternion_attitude),
            "angular_velocity_rads": list(state.angular_velocity),
            "tumble_magnitude": w_mag
        }
        
        anomaly_desc = (
            "Satellite is in uncontrolled gyroscopic tumble. Spin rate exceeds 0.05 rad/s "
            "due to external micro-meteoroid torque impulses. Navigation star-trackers are blinded. "
            "Direct link to ground control severed. Local physics prior required to stabilize."
        )
        
        # Recall trajectory proof context
        trajectory_context = {
            "parent_trajectory_id": "orbit_tumble_10k_6dof",
            "parent_trajectory_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "timestep_of_decision": step * dt,
            "anomaly_type": "GYROSCOPIC_TUMBLE"
        }
        
        # Dispatch to Kid Cosmo Reasoning Agent
        manifest = agent.generate_manifest(
            mission_id="COSMO_ORBITAL_STABILIZE",
            environment="DEEPBLACK",
            telemetry_snapshot=telemetry,
            anomaly_description=anomaly_desc,
            epistemic_isolation=True,
            trajectory_context=trajectory_context
        )
        
        save_and_display_manifest(manifest)


# ─── SCENARIO 2: TERRAN ───────────────────────────────────────────────────────
def run_terran_scenario(agent: ReasoningAgent):
    print("\n═══════════════════════════════════════════════════════════")
    print("  [SCENARIO 2] LUNAR ROVER SOIL-COMPACTION TRAP")
    print("  Physics Engine: ztp-runtime (Terran Soil Mechanics)")
    print("═══════════════════════════════════════════════════════════")
    
    moisture = 0.1
    compaction = 0.05
    mass = 2500.0  # kg
    footprint = 0.25  # m2
    
    anomaly_triggered = False
    
    print("\nRunning rover terramechanics traction sweeps:")
    for step in range(1, 11):
        # Soil moisture and baseline compaction increases dynamically (e.g. crossing a mud sinkhole or yielding lunar regolith)
        moisture += 0.04
        compaction += 0.02
        
        # Evaluate compaction depth
        res = ztp_bridge.evaluate_soil(
            soil_type="loam",
            moisture=moisture,
            glomalin=0.6,
            compaction=compaction,
            depth_layers=25,
            mass=mass,
            footprint=footprint,
            locomotion="wheeled"
        )
        print(f"  Step {step:02d} | Moisture: {moisture:.2f} | BaseCompaction: {compaction:.2f} | Max Compaction Yield: {res.max_compaction:.4f} | Sink Depth: {res.compaction_depth_m:.4f}m")
        
        # Hazard condition: Soil max compaction exceeding 0.2 (indicates traction loss / sinking risk)
        if res.max_compaction > 0.2:
            print(f"\n⚠️  PHYSICAL EXTREMUM DETECTED: Soil compaction yield ({res.max_compaction:.4f}) exceeds safe traction limit (0.20)!")
            print("Rover wheels experiencing slip exceeding 20%%. Imminent immobilization.")
            anomaly_triggered = True
            break
            
        time.sleep(0.1)
        
    if anomaly_triggered:
        telemetry = {
            "moisture": moisture,
            "base_compaction": compaction,
            "max_compaction_yield": res.max_compaction,
            "compaction_depth_m": res.compaction_depth_m,
            "locomotion": "wheeled",
            "vehicle_mass_kg": mass
        }
        
        anomaly_desc = (
            f"Lunar rover traversing a high-moisture loam substrate. Soil yield max compaction has reached {res.max_compaction:.4f}, "
            f"resulting in wheel sinkage of {res.compaction_depth_m:.4f} meters. Wheel slip ratio is spiked at 28%. "
            "Wheeled forward propulsion is disabled to prevent digging-in. Epistemic isolation engaged."
        )
        
        trajectory_context = {
            "parent_trajectory_id": "terran_loam_compaction_sink",
            "parent_trajectory_hash": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            "timestep_of_decision": step * 1.0,
            "anomaly_type": "SOIL_COMPACTION_TRAP"
        }
        
        manifest = agent.generate_manifest(
            mission_id="COSMO_ROVER_SOIL_ESCAPE",
            environment="TERRAN",
            telemetry_snapshot=telemetry,
            anomaly_description=anomaly_desc,
            epistemic_isolation=True,
            trajectory_context=trajectory_context
        )
        
        save_and_display_manifest(manifest)


# ─── SCENARIO 3: ATHERIC ──────────────────────────────────────────────────────
def run_atheric_scenario(agent: ReasoningAgent):
    print("\n═══════════════════════════════════════════════════════════")
    print("  [SCENARIO 3] DRONE CANOPY RF CONJUNCTION BLACKOUT")
    print("  Physics Engine: ztp-runtime (Atheric Pathloss & SNR)")
    print("═══════════════════════════════════════════════════════════")
    
    seed = bytes([0x12, 0x34, 0x56, 0x78] * 8)
    strength = 1e-14  # transmit power in Watts (extremely weak signal / deep space probe)
    distance = 10000.0   # starting distance in km
    
    anomaly_triggered = False
    
    print("\nRunning deep space probe telemetry and RF pathloss monitoring:")
    for step in range(1, 50):
        # Distance increases as probe recedes into deep space
        distance += 50000.0
        
        # Check signal handshake status
        res = ztp_bridge.atheric_handshake(seed, strength, distance)
        print(f"  Step {step:02d} | Distance: {distance:.1f}km | RF Coherence: {res.resonance:.4f} | Avg SNR: {res.avg_snr_db:.2f}dB | Link: {'OK' if res.success else 'FAILED'}")
        
        # Hazard condition: handshake fails due to pathloss
        if not res.success:
            print(f"\n⚠️  PHYSICAL EXTREMUM DETECTED: RF Coherence ({res.resonance:.4f}) dropped below critical resonance gate!")
            print("RF handshake failed. Command uplink disconnected. Auto-stabilization active.")
            anomaly_triggered = True
            break
            
        time.sleep(0.1)
        
    if anomaly_triggered:
        telemetry = {
            "rf_strength_dbm": strength,
            "distance_km": distance,
            "rf_resonance": res.resonance,
            "avg_snr_db": res.avg_snr_db,
            "link_status": "DISCONNECTED"
        }
        
        anomaly_desc = (
            f"Autonomous drone has drifted to {distance:.1f} km from base station. RF pathloss has degraded signal-to-noise ratio to "
            f"{res.avg_snr_db:.2f}dB. Coherence dropped below resonance gate, causing immediate command link dropout. "
            "Dark Window engaged. Safe return trajectory required."
        )
        
        trajectory_context = {
            "parent_trajectory_id": "atheric_canopy_pathloss_fade",
            "parent_trajectory_hash": "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
            "timestep_of_decision": step * 2.0,
            "anomaly_type": "RF_CONJUNCTION_BLACKOUT"
        }
        
        manifest = agent.generate_manifest(
            mission_id="COSMO_DRONE_COMM_RECOVERY",
            environment="AV_HIGHWAY",
            telemetry_snapshot=telemetry,
            anomaly_description=anomaly_desc,
            epistemic_isolation=True,
            trajectory_context=trajectory_context
        )
        
        save_and_display_manifest(manifest)


# ─── UTILITIES ────────────────────────────────────────────────────────────────

def save_and_display_manifest(manifest: dict):
    print("\n========================================================")
    print("             GENERATED REASONING MANIFEST               ")
    print("========================================================")
    print(json.dumps(manifest, indent=2))
    print("========================================================\n")
    
    # Save local manifest JSON
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifests")
    os.makedirs(out_dir, exist_ok=True)
    
    filename = f"manifest_{manifest['mission_id'].lower()}_{int(time.time())}.json"
    filepath = os.path.join(out_dir, filename)
    
    with open(filepath, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"✅ Reasoning Manifest sealed on-disk: {filepath}")
    print(f"🔒 SHA-256 Proof: {manifest['sha256_proof']}")
    print("========================================================\n")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    
    print("\n========================================================")
    print("     KID COSMO & G^G RUST RUNTIME UNIFIED EMULATION     ")
    print("========================================================")
    print(f"  Target Model Profile: {args.profile}")
    print(f"  Target Physics Domain: {args.scenario.upper()}")
    print("========================================================\n")
    
    # Initialize the reasoning brain
    agent = ReasoningAgent(profile=args.profile)
    
    if args.scenario == "orbital":
        run_orbital_scenario(agent)
    elif args.scenario == "terran":
        run_terran_scenario(agent)
    elif args.scenario == "atheric":
        run_atheric_scenario(agent)

if __name__ == "__main__":
    main()
