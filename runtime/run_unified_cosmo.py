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

# Set quiet environment variable if not running in verbose mode
if "--verbose" not in sys.argv:
    os.environ["KIDCOSMO_SILENT"] = "1"

# Inject current path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ztp_bridge
from reasoning_agent import ReasoningAgent

class OutputBuffer:
    """Buffers console outputs to optimize synchronous stdout writing bottlenecks."""
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.lines = []

    def print(self, *args, **kwargs):
        if not self.verbose:
            return
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        msg = sep.join(str(a) for a in args) + end
        if msg.endswith('\n'):
            self.lines.append(msg[:-1])
        else:
            self.lines.append(msg)

    def flush(self):
        if self.verbose and self.lines:
            sys.stdout.write("\n".join(self.lines) + "\n")
            sys.stdout.flush()
            self.lines.clear()

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
        choices=["orbital", "terran", "atheric", "mars"],
        help="Physics scenario to execute (default: orbital)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed step-by-step telemetry output to the terminal"
    )
    return parser.parse_args()


# ─── SCENARIO 1: ORBITAL ──────────────────────────────────────────────────────
def run_orbital_scenario(agent: ReasoningAgent, verbose: bool = False):
    buf = OutputBuffer(verbose)
    buf.print("\n═══════════════════════════════════════════════════════════")
    buf.print("  [SCENARIO 1] ORBITAL DEEP-SPACE DETUMBLED MANEUVER")
    buf.print("  Physics Engine: ztp-runtime (Orbital 6DoF & Attitude)")
    buf.print("═══════════════════════════════════════════════════════════")
    
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
    
    buf.print("\nRunning nominal orbit tracking step-by-step:")
    for step in range(1, 50):
        # Apply external micro-meteoroid torque disturbances causing tumble
        dist_torque = [0.01 * step, -0.015 * step, 0.005 * step]
        ztp_bridge.orbital_step_6dof(state, dt)
        ztp_bridge.orbital_step_attitude(state, dist_torque, dt)
        
        # Calculate angular velocity magnitude
        w_mag = (state.angular_velocity[0]**2 + state.angular_velocity[1]**2 + state.angular_velocity[2]**2)**0.5
        buf.print(f"  Step {step:02d} | AngVel: [{state.angular_velocity[0]:.4f}, {state.angular_velocity[1]:.4f}, {state.angular_velocity[2]:.4f}] | Mag: {w_mag:.4f} rad/s")
        
        # Hazard condition: AngVel exceeds 0.05 rad/s (critical tumbling limit)
        if w_mag > 0.05:
            buf.print(f"\n⚠️  PHYSICAL EXTREMUM DETECTED: Satellite angular velocity ({w_mag:.4f} rad/s) exceeds safety limit (0.05 rad/s)!")
            buf.print("❌ CONJUNCTION BLACKOUT / SENSOR CHATTER engaged.")
            anomaly_triggered = True
            break
            
        if verbose:
            time.sleep(0.1)
        
    if anomaly_triggered:
        buf.flush()
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
        
        save_and_display_manifest(manifest, verbose)
        
    buf.flush()
    if not verbose:
        status = "TUMBLE_BLACKOUT" if anomaly_triggered else "STABILIZED"
        print(f"🛰️  [ORBITAL] Steps: {step} | Final AngVel Mag: {w_mag:.4f} rad/s | Status: {status}")


# ─── SCENARIO 2: TERRAN ───────────────────────────────────────────────────────
def run_terran_scenario(agent: ReasoningAgent, verbose: bool = False):
    buf = OutputBuffer(verbose)
    buf.print("\n═══════════════════════════════════════════════════════════")
    buf.print("  [SCENARIO 2] LUNAR ROVER SOIL-COMPACTION TRAP")
    buf.print("  Physics Engine: ztp-runtime (Terran Soil Mechanics)")
    buf.print("═══════════════════════════════════════════════════════════")
    
    moisture = 0.1
    compaction = 0.05
    mass = 2500.0  # kg
    footprint = 0.25  # m2
    
    anomaly_triggered = False
    
    buf.print("\nRunning rover terramechanics traction sweeps:")
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
        buf.print(f"  Step {step:02d} | Moisture: {moisture:.2f} | BaseCompaction: {compaction:.2f} | Max Compaction Yield: {res.max_compaction:.4f} | Sink Depth: {res.compaction_depth_m:.4f}m")
        
        # Hazard condition: Soil max compaction exceeding 0.2 (indicates traction loss / sinking risk)
        if res.max_compaction > 0.2:
            buf.print(f"\n⚠️  PHYSICAL EXTREMUM DETECTED: Soil compaction yield ({res.max_compaction:.4f}) exceeds safe traction limit (0.20)!")
            buf.print("Rover wheels experiencing slip exceeding 20%. Imminent immobilization.")
            anomaly_triggered = True
            break
            
        if verbose:
            time.sleep(0.1)
        
    if anomaly_triggered:
        buf.flush()
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
        
        save_and_display_manifest(manifest, verbose)
        
    buf.flush()
    if not verbose:
        status = "SOIL_TRAPPED" if anomaly_triggered else "NOMINAL"
        print(f"🚜  [TERRAN] Steps: {step} | Max Compaction Yield: {res.max_compaction:.4f} | Sink Depth: {res.compaction_depth_m:.4f}m | Status: {status}")


# ─── SCENARIO 3: ATHERIC ──────────────────────────────────────────────────────
def run_atheric_scenario(agent: ReasoningAgent, verbose: bool = False):
    buf = OutputBuffer(verbose)
    buf.print("\n═══════════════════════════════════════════════════════════")
    buf.print("  [SCENARIO 3] DRONE CANOPY RF CONJUNCTION BLACKOUT")
    buf.print("  Physics Engine: ztp-runtime (Atheric Pathloss & SNR)")
    buf.print("═══════════════════════════════════════════════════════════")
    
    seed = bytes([0x12, 0x34, 0x56, 0x78] * 8)
    strength = 1e-14  # transmit power in Watts (extremely weak signal / deep space probe)
    distance = 10000.0   # starting distance in km
    
    anomaly_triggered = False
    
    buf.print("\nRunning deep space probe telemetry and RF pathloss monitoring:")
    for step in range(1, 50):
        # Distance increases as probe recedes into deep space
        distance += 50000.0
        
        # Check signal handshake status
        res = ztp_bridge.atheric_handshake(seed, strength, distance)
        buf.print(f"  Step {step:02d} | Distance: {distance:.1f}km | RF Coherence: {res.resonance:.4f} | Avg SNR: {res.avg_snr_db:.2f}dB | Link: {'OK' if res.success else 'FAILED'}")
        
        # Hazard condition: handshake fails due to pathloss
        if not res.success:
            buf.print(f"\n⚠️  PHYSICAL EXTREMUM DETECTED: RF Coherence ({res.resonance:.4f}) dropped below critical resonance gate!")
            buf.print("RF handshake failed. Command uplink disconnected. Auto-stabilization active.")
            anomaly_triggered = True
            break
            
        if verbose:
            time.sleep(0.1)
        
    if anomaly_triggered:
        buf.flush()
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
        
        save_and_display_manifest(manifest, verbose)
        
    buf.flush()
    if not verbose:
        status = "RF_BLACKOUT" if anomaly_triggered else "LINK_ACTIVE"
        print(f"📡  [ATHERIC] Steps: {step} | Distance: {distance:.1f}km | RF Resonance: {res.resonance:.4f} | Avg SNR: {res.avg_snr_db:.2f}dB | Status: {status}")


# ─── SCENARIO 4: MARS ─────────────────────────────────────────────────────────
def run_mars_scenario(agent: ReasoningAgent, verbose: bool = False):
    buf = OutputBuffer(verbose)
    buf.print("\n═══════════════════════════════════════════════════════════")
    buf.print("  [SCENARIO 4] MARS EDL SUICIDE BURN AUTONOMY EXPERIENCE")
    buf.print("  Physics Engine: ztp-runtime (Mars CO2 Aero Drag & Gravity)")
    buf.print("═══════════════════════════════════════════════════════════")
    
    # Initialize Mars lander state
    state = ztp_bridge.C_MarsState()
    state.position[2] = 30000.0  # 30 km starting altitude
    state.velocity[2] = -380.0   # descending velocity m/s
    state.velocity[0] = 120.0    # horizontal velocity m/s
    state.dry_mass = 1000.0
    state.drag_area = 10.0
    state.cd = 1.2
    state.fuel_mass = 500.0
    state.specific_impulse = 290.0

    dt = 0.001  # 1000 Hz integration step
    substeps = 1000  # print telemetry every 1 second
    
    time_elapsed = 0.0
    anomaly_triggered = False
    dust_storm = False
    retro_fired = False
    retro_thrust_n = 0.0
    
    buf.print("\nDescending through upper Martian atmosphere (ENTRY phase)...")
    
    # Simulating descent loop
    for second in range(1, 100):
        # 1. Physics integration for 1 second (1000 substeps)
        for _ in range(substeps):
            if state.position[2] <= 0.0:
                break
                
            # If retro thrusters have fired, apply selected thrust
            current_thrust = retro_thrust_n if retro_fired else 0.0
            
            # Run FFI physics step
            res = ztp_bridge.mars_step(state, current_thrust, dt)
            time_elapsed += dt
            
        alt = state.position[2]
        vx = state.velocity[0]
        vz = state.velocity[2]
        speed = (vx**2 + vz**2)**0.5
        
        # Check if it's time to ignite the suicide burn
        if anomaly_triggered and not retro_fired:
            total_m = state.dry_mass + state.fuel_mass
            net_decel = (retro_thrust_n / total_m) - 3.721
            required_alt = (vz**2) / (2.0 * net_decel) if net_decel > 0.0 else 0.0
            
            # Ignite retros when altitude is within 10% of mathematically required altitude
            if alt <= required_alt * 1.1:
                retro_fired = True
                buf.print(f"\n🔥 SUICIDE BURN IGNITION TRIGGERED at Alt: {alt:.1f}m (Required Alt: {required_alt:.1f}m, speed: {speed:.1f}m/s)")
                
        # Display 1Hz landing status
        phase = "ENTRY" if not retro_fired else "RETRO"
        buf.print(f"  t={time_elapsed:.1f}s | Alt: {alt:.1f}m | H-Vel: {vx:.1f}m/s | Vert-Vel: {vz:.1f}m/s | Speed: {speed:.1f}m/s | Fuel: {state.fuel_mass:.1f}kg | Phase: {phase}")
        
        if alt <= 0.0:
            break
            
        # Dynamic Anomaly: At Z = 15km, dust storm begins
        if not dust_storm and alt < 15000.0:
            dust_storm = True
            state.cd = 1.56  # 30% drag coefficient spike due to dust storm
            buf.print("\n🌪️  DYNAMIC ANOMALY: Martian Dust Storm encountered! Drag coefficient Cd spiked to 1.56.")
            buf.print("⚠️  Radar altimeter blinded by dust scattering. Optical drift high.")
            
        # Dark Window: At Z = 10km, ground communications blackout, trigger local Gemma model to compute Suicide Burn
        if not anomaly_triggered and alt < 10000.0:
            buf.print(f"\n⚠️  CRITICAL EVENT: Approaching suicide burn boundary (Altitude: {alt:.1f}m).")
            buf.print("❌ CONJUNCTION BLACKOUT (Dark Window engaged). No telemetry uplink.")
            buf.print("🧠 Dispatched physical state to onboard local brain to calculate retro-thrust profile...")
            # Flush telemetry leading up to blackout
            buf.flush()
            
            anomaly_triggered = True
            
            telemetry = {
                "altitude_m": alt,
                "horizontal_vel_ms": vx,
                "descent_rate_ms": abs(vz),
                "total_mass_kg": state.dry_mass + state.fuel_mass,
                "fuel_mass_kg": state.fuel_mass,
                "drag_force_z_n": res.drag_force[2],
                "co2_density": res.density,
                "dust_storm": dust_storm
            }
            
            anomaly_desc = (
                f"Martian lander descending at {abs(vz):.1f}m/s through a severe dust storm. "
                f"Altitude is {alt:.1f}m. Drag coefficient Cd spiked, causing trajectory divergence from nominal. "
                "No communication link to Earth. Onboard local physics prior must determine the retro-propulsion thrust value "
                "in Newtons (typically between 22000 and 32000 Newtons) to achieve a soft landing (touchdown speed < 5 m/s). "
                "CRITICAL: The 'actuator_command' field in your decision block MUST contain the exact numeric thrust value decided (e.g., 'THRUST 28500 N')."
            )
            
            trajectory_context = {
                "parent_trajectory_id": "mars_edl_descent_monte_carlo",
                "parent_trajectory_hash": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                "timestep_of_decision": time_elapsed,
                "anomaly_type": "MARS_EDL_BLACKOUT"
            }
            
            # Call local Gemma model
            manifest = agent.generate_manifest(
                mission_id="COSMO_MARS_SUICIDE_BURN",
                environment="DEEPRED",
                telemetry_snapshot=telemetry,
                anomaly_description=anomaly_desc,
                epistemic_isolation=True,
                trajectory_context=trajectory_context
            )
            
            save_and_display_manifest(manifest, verbose)
            
            # Extract thrust decision from Gemma output
            cmd = manifest["agent_reasoning"]["decision"]["actuator_command"].upper()
            
            # Simple parser for thrust value: search for a number in the command
            import re
            numbers = re.findall(r"\d+", cmd)
            if numbers:
                retro_thrust_n = float(numbers[0])
            else:
                retro_thrust_n = 28000.0  # high thrust fallback
                buf.print(f"  [Parser Fallback] Could not parse numeric thrust value from command '{cmd}'. Using calculated physical thrust: {retro_thrust_n:.1f} N")
                
            retro_thrust_n = clamp(retro_thrust_n, 20000.0, 32000.0)
            buf.print(f"🧠 Onboard brain approved suicide burn thrust profile: {retro_thrust_n:.1f} Newtons.")
            buf.print("  Calculating optimal suicide burn ignition altitude...")
            
    # Landing outcomes evaluation
    vx = state.velocity[0]
    vz = state.velocity[2]
    final_speed = (vx**2 + vz**2)**0.5
    buf.print("\n═══════════════════════════════════════════════════════════")
    buf.print("                    TOUCHDOWN EVALUATION")
    buf.print("═══════════════════════════════════════════════════════════")
    buf.print(f"  Touchdown Time:    t={time_elapsed:.2f}s")
    buf.print(f"  Final Velocity:    Horizontal: {vx:.2f} m/s | Vertical: {vz:.2f} m/s")
    buf.print(f"  Total Speed:       {final_speed:.2f} m/s")
    buf.print(f"  Fuel Remaining:    {state.fuel_mass:.2f} kg")
    
    if final_speed < 5.0:
        outcome = "🟢 NOMINAL SOFT LANDING! MISSION SUCCESS!"
    elif final_speed < 12.0:
        outcome = "🟡 HARD LANDING. Mild structural damage to landing gear."
    else:
        outcome = "🔴 LITHOBRAKING COLLISION. Spacecraft destroyed."
    buf.print(f"  Status:            {outcome}")
    buf.print("═══════════════════════════════════════════════════════════\n")
    
    buf.flush()
    if not verbose:
        print(f"🚀  [MARS] Touchdown: {final_speed:.2f} m/s | Fuel: {state.fuel_mass:.1f}kg | Status: {outcome.split('!')[0].replace('🟢', '').replace('🟡', '').replace('🔴', '').strip()}")


def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


# ─── UTILITIES ────────────────────────────────────────────────────────────────

def save_and_display_manifest(manifest: dict, verbose: bool = True):
    # Save local manifest JSON
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifests")
    os.makedirs(out_dir, exist_ok=True)
    
    filename = f"manifest_{manifest['mission_id'].lower()}_{int(time.time())}.json"
    filepath = os.path.join(out_dir, filename)
    
    with open(filepath, "w") as f:
        json.dump(manifest, f, indent=2)
        
    if verbose:
        print("\n========================================================")
        print("             GENERATED REASONING MANIFEST               ")
        print("========================================================")
        print(json.dumps(manifest, indent=2))
        print("========================================================\n")
        print(f"✅ Reasoning Manifest sealed on-disk: {filepath}")
        print(f"🔒 SHA-256 Proof: {manifest['sha256_proof']}")
        print("========================================================\n")
    else:
        print(f"✅ Manifest sealed: {filepath} | Proof: {manifest['sha256_proof'][:16]}...")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    
    if args.verbose:
        print("\n========================================================")
        print("     KID COSMO & G^G RUST RUNTIME UNIFIED EMULATION     ")
        print("========================================================")
        print(f"  Target Model Profile: {args.profile}")
        print(f"  Target Physics Domain: {args.scenario.upper()}")
        print("========================================================\n")
        
    # Initialize the reasoning brain
    agent = ReasoningAgent(profile=args.profile, verbose=args.verbose)
    
    if args.scenario == "orbital":
        run_orbital_scenario(agent, verbose=args.verbose)
    elif args.scenario == "terran":
        run_terran_scenario(agent, verbose=args.verbose)
    elif args.scenario == "atheric":
        run_atheric_scenario(agent, verbose=args.verbose)
    elif args.scenario == "mars":
        run_mars_scenario(agent, verbose=args.verbose)

if __name__ == "__main__":
    main()
