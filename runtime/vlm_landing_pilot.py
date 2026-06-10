#!/usr/bin/env python3
"""
KID COSMO — Vision-Language-Action (VLA) HIL Simulator
Renders physical state as a visual dashboard PNG, passes it to a local VLM (Qwen2-VL),
and feeds the parsed thrust decision back into the Rust ztp-runtime FFI physics step.
"""

import os
import sys
import time
import json
import re

# Suppress FFI loading prints
os.environ["KIDCOSMO_SILENT"] = "1"

# Inject current path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ztp_bridge

def generate_telemetry_dashboard(alt, vx, vz, fuel, cd, dust_storm, filepath):
    """Generates a premium dark-themed visual telemetry dashboard of the spacecraft status."""
    try:
        import matplotlib.pyplot as plt
        # Dark style for high aesthetics
        plt.style.use('dark_background')
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.suptitle("🚀 KID COSMO — VISUAL HIL TELEMETRY DASHBOARD", fontsize=16, fontweight='bold', color='#FF3366')
        
        # 1. Altitude History Tracker
        ax1 = axes[0, 0]
        # Simulate descent points
        alt_profile = [30000, 25000, 20000, 15000, alt]
        time_profile = [0, 15, 30, 45, 60]
        ax1.plot(time_profile, alt_profile, color='#00FFCC', marker='o', linewidth=2, markersize=6)
        ax1.set_title("Altitude Descent Profile", fontsize=12, color='#E0E0E0')
        ax1.set_xlabel("Time (s)", fontsize=9)
        ax1.set_ylabel("Altitude (m)", fontsize=9)
        ax1.grid(True, alpha=0.2, linestyle='--')
        
        # 2. Velocity Gauge (Vz vs. Vx)
        ax2 = axes[0, 1]
        ax2.bar(["H-Vel (Vx)", "V-Vel (Vz)"], [abs(vx), abs(vz)], color=['#00CCFF', '#FF0055'], width=0.4)
        ax2.set_title("Velocity Vectors", fontsize=12, color='#E0E0E0')
        ax2.set_ylabel("Speed (m/s)", fontsize=9)
        ax2.set_ylim(0, 500)
        ax2.grid(True, alpha=0.1, linestyle='--')
        
        # 3. Fuel reserve bar
        ax3 = axes[1, 0]
        fuel_pct = (fuel / 500.0) * 100
        ax3.bar(["Fuel Reserves"], [fuel], color='#00FF66' if fuel_pct > 25 else '#FFAA00', width=0.3)
        ax3.set_title(f"Fuel Mass ({fuel_pct:.1f}%)", fontsize=12, color='#E0E0E0')
        ax3.set_ylabel("Mass (kg)", fontsize=9)
        ax3.set_ylim(0, 500)
        ax3.grid(True, alpha=0.1, linestyle='--')
        
        # 4. Status alerts
        ax4 = axes[1, 1]
        ax4.axis('off')
        alert_color = '#FF3300' if dust_storm else '#00FF66'
        alert_text = (
            "⚠️ DUST STORM ACTIVE\n"
            "⚠️ COMM BLACKOUT ENGAGED\n"
            f"⚠️ DRAG COEFFICIENT Cd: {cd:.2f}\n"
            "⚠️ ENTRANCE TO DARK WINDOW"
        ) if dust_storm else "🟢 NOMINAL CONNECTION\n🟢 SENSORS UNBLINDED"
        
        ax4.text(0.5, 0.5, alert_text, color=alert_color, fontsize=12, fontweight='bold',
                 ha='center', va='center', bbox=dict(facecolor='#121212', edgecolor=alert_color, boxstyle='round,pad=1.2'))
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=100)
        plt.close()
        print(f"🖼️  Generated visual telemetry dashboard: {filepath}")
    except Exception as e:
        print(f"❌ Failed to generate matplotlib dashboard: {e}")

def run_vlm_loop():
    print("========================================================")
    print("     KID COSMO — LOCAL VLM VISUAL FLIGHT CONTROLLER     ")
    print("========================================================")
    
    # 1. Dependency checks
    try:
        import mlx_vlm
    except ImportError:
        print("\n❌ error: 'mlx-vlm' is not installed.")
        print("To run the visual closed-loop pilot, please install it first:")
        print("  pip install mlx-vlm\n")
        sys.exit(1)
        
    from mlx_vlm import load, generate
    from mlx_vlm.utils import load_image
    
    # 2. Physics Lander State initialization
    state = ztp_bridge.C_MarsState()
    state.position[2] = 30000.0  # 30 km starting altitude
    state.velocity[2] = -380.0   # descending velocity m/s
    state.velocity[0] = 120.0    # horizontal velocity m/s
    state.dry_mass = 1000.0
    state.drag_area = 10.0
    state.cd = 1.2
    state.fuel_mass = 500.0
    state.specific_impulse = 290.0

    dt = 0.001
    substeps = 1000
    time_elapsed = 0.0
    dust_storm = False
    
    print("\n[PHASE 1] Physics Engine simulating Entry Descent down to 10km blackout...")
    
    # Simulate descent down to 10km
    while state.position[2] > 10000.0:
        # Physics integration
        for _ in range(substeps):
            res = ztp_bridge.mars_step(state, 0.0, dt)
            time_elapsed += dt
            
        alt = state.position[2]
        vx = state.velocity[0]
        vz = state.velocity[2]
        speed = (vx**2 + vz**2)**0.5
        
        print(f"  t={time_elapsed:.1f}s | Alt: {alt:.1f}m | Speed: {speed:.1f}m/s | Fuel: {state.fuel_mass:.1f}kg")
        
        # Encounter storm
        if not dust_storm and alt < 15000.0:
            dust_storm = True
            state.cd = 1.56
            print("\n🌪️  Encountered Martian Dust Storm! Drag Cd spiked to 1.56.")
            
    # Blackout boundary reached!
    alt = state.position[2]
    vx = state.velocity[0]
    vz = state.velocity[2]
    speed = (vx**2 + vz**2)**0.5
    
    print(f"\n⚠️  Reached Blackout Boundary (Altitude: {alt:.1f}m).")
    print("❌ Conjunction blackout engaged. Uplink severed.")
    print("📸 Rendering telemetry dashboard...")
    
    # Render dashboard
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telemetry_dashboard.png")
    generate_telemetry_dashboard(alt, vx, vz, state.fuel_mass, state.cd, dust_storm, dashboard_path)
    
    # Load local VLM
    model_path = "mlx-community/Qwen2-VL-2B-Instruct-4bit"
    print(f"\n🧠 Loading local VLM brain: {model_path}...")
    try:
        model, processor = load(model_path)
        print("VLM Loaded. Processing visual dashboard...")
    except Exception as e:
        print(f"❌ Failed to load VLM model: {e}")
        sys.exit(1)
        
    # Construct VLM prompt
    prompt = (
        "You are an autonomous Martian spacecraft landing brain. Analyze the telemetry dashboard image. "
        "Find the current descent velocity and lander mass, and calculate the required retro-thrust "
        "in Newtons (typically between 20000 and 32000 Newtons) to slow the spacecraft down for a safe landing. "
        "Your final response MUST declare the command exactly as: 'THRUST <number> N'."
    )
    
    # Format chat prompt for Qwen2-VL
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": dashboard_path},
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    # Apply chat template
    formatted_prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    
    print("🧠 Dispatching image to VLM...")
    start_t = time.time()
    
    # Run vision generation
    response = generate(model, processor, formatted_prompt, max_tokens=128, verbose=False)
    output = response.text if hasattr(response, "text") else response
    
    latency = time.time() - start_t
    print(f"🧠 VLM Reasoning Completed in {latency:.2f} seconds.")
    print("\n================ VLM PILOT DELIBERATION ================")
    print(output.strip())
    print("========================================================\n")
    
    # Parse thrust command
    numbers = re.findall(r"\d+", output)
    retro_thrust_n = 28000.0  # fallback
    for num in re.findall(r"THRUST\s+(\d+)", output.upper()):
        retro_thrust_n = float(num)
        break
    else:
        # Backup parser: find any number next to N or general number
        match = re.search(r"(\d+)\s*N", output.upper())
        if match:
            retro_thrust_n = float(match.group(1))
        else:
            if numbers:
                retro_thrust_n = float(numbers[0])
                
    retro_thrust_n = max(20000.0, min(retro_thrust_n, 32000.0))
    print(f"🤖 Actuator Interface parsed thrust command: {retro_thrust_n:.1f} Newtons.")
    
    # [PHASE 2] Resume physics step with VLM burn decision
    print("\n[PHASE 2] Firing thrusters using VLM decision...")
    retro_fired = False
    
    # Simulating landing loop
    for second in range(1, 100):
        # 1. Physics integration for 1 second
        for _ in range(substeps):
            if state.position[2] <= 0.0:
                break
            current_thrust = retro_thrust_n if retro_fired else 0.0
            res = ztp_bridge.mars_step(state, current_thrust, dt)
            time_elapsed += dt
            
        alt = state.position[2]
        vx = state.velocity[0]
        vz = state.velocity[2]
        speed = (vx**2 + vz**2)**0.5
        
        # Check for retro ignition
        if not retro_fired:
            total_m = state.dry_mass + state.fuel_mass
            net_decel = (retro_thrust_n / total_m) - 3.721
            required_alt = (vz**2) / (2.0 * net_decel) if net_decel > 0.0 else 0.0
            if alt <= required_alt * 1.1:
                retro_fired = True
                print(f"🔥 Retro-ignition triggered at Alt: {alt:.1f}m (Target: {required_alt:.1f}m, speed: {speed:.1f}m/s)")
                
        if alt <= 0.0:
            break
            
    final_speed = (state.velocity[0]**2 + state.velocity[2]**2)**0.5
    print("\n═══════════════════════════════════════════════════════════")
    print("                    TOUCHDOWN EVALUATION")
    print("═══════════════════════════════════════════════════════════")
    print(f"  Touchdown Time:    t={time_elapsed:.2f}s")
    print(f"  Final Velocity:    Horizontal: {state.velocity[0]:.2f} m/s | Vertical: {state.velocity[2]:.2f} m/s")
    print(f"  Total Speed:       {final_speed:.2f} m/s")
    print(f"  Fuel Remaining:    {state.fuel_mass:.2f} kg")
    
    if final_speed < 5.0:
        print("  Status:            🟢 NOMINAL SOFT LANDING! MISSION SUCCESS!")
    elif final_speed < 12.0:
        print("  Status:            🟡 HARD LANDING. Mild structural damage.")
    else:
        print("  Status:            🔴 LITHOBRAKING COLLISION. Spacecraft destroyed.")
    print("═══════════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    run_vlm_loop()
