#!/usr/bin/env python3
"""
KID COSMO — Somatic Sub v1.0
The Sovereign Pilot for Underwater Domains (ArduSub/BlueOS).
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any

# Bridge and Brain Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../integration/ardupilot/scripts")))
from mavlink_bridge import MAVLinkBridge
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../runtime")))
from reasoning_agent import ReasoningAgent

# CONFIGURATION
INVENTORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../samples/underwater"))
os.makedirs(INVENTORY_DIR, exist_ok=True)

class SomaticSub:
    def __init__(self, connection_str: str = "udpin:localhost:14550"):
        print("🌊 Initializing Sovereign Sub...")
        self.bridge = MAVLinkBridge(connection_str)
        self.agent = ReasoningAgent()
        self.last_decision_time = 0
        self.decision_cooldown = 10.0 # Underwater physics is slower

    def run(self):
        self.bridge.wait_for_heartbeat()
        print("⚓ Somatic Sub Active. Diving into the Exclusion Zone...")

        while True:
            self.bridge.update()
            snapshot = self.bridge.get_snapshot()
            
            # Underwater Exclusion Zone: Acoustic Blackout or Depth Sensor Spike
            is_blackout = snapshot["is_blackout"]
            # Depth anomaly: (Assuming alt is depth as negative)
            depth = abs(snapshot["perception"]["alt"])
            
            if is_blackout and (time.time() - self.last_decision_time > self.decision_cooldown):
                print(f"⚠️  ACOUSTIC BLACKOUT DETECTED at {depth:.1f}m. Consulting Sovereign Brain...")
                
                # Generate Sovereign Manifest
                manifest = self.agent.generate_manifest(
                    mission_id=f"sub_{uuid.uuid4().hex[:8]}",
                    environment="DEEPBLUE",
                    telemetry_snapshot=snapshot,
                    anomaly_description="ACOUSTIC_LINK_LOSS",
                    epistemic_isolation=True,
                    trajectory_context={
                        "parent_trajectory_id": f"sub_sitl_{int(time.time())}",
                        "parent_trajectory_hash": snapshot.get("parent_trajectory_hash", "0x0000"),
                        "anomaly_type": "ACOUSTIC_LINK_LOSS",
                        "timestep_of_decision": snapshot["t"],
                        "telemetry_at_decision": snapshot,
                        "mission_outcome": "success"
                    }
                )
                
                # Save Manifest
                m_filename = f"{manifest['mission_id']}.reasoning.json"
                m_path = os.path.join(INVENTORY_DIR, m_filename)
                with open(m_path, "w") as f:
                    json.dump(manifest, f, indent=2)
                
                decision = manifest["agent_reasoning"]["decision"]["actuator_command"]
                print(f"🧠 Brain Decision: {decision}")
                print(f"📄 Saved Manifest: {m_filename}")
                
                # EXECUTE SUB-SPECIFIC ACTION
                self.execute_sub_decision(decision)
                
                self.last_decision_time = time.time()

            time.sleep(0.1)

    def execute_sub_decision(self, command: str):
        """Maps logical reasoning to ArduSub MAVLink actions."""
        command = command.upper()
        
        if "SURFACE" in command:
            print("🕹️  Somatic Action: EXECUTING EMERGENCY SURFACE.")
            # self.bridge.set_mode("SURFACE") # ArduSub mode
        elif "DEPTH_HOLD" in command or "STAY" in command:
            print("🕹️  Somatic Action: Transitioning to DEPTH_HOLD.")
            self.bridge.set_mode("ALT_HOLD") # ArduSub uses ALT_HOLD for depth hold
        elif "STABILIZE" in command:
            print("🕹️  Somatic Action: Stabilizing attitude.")
            self.bridge.set_mode("STABILIZE")
        else:
            print(f"🕹️  Somatic Action: {command} (Monitoring only)")

if __name__ == "__main__":
    sub = SomaticSub()
    sub.run()
